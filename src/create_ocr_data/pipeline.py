import csv
import re
from pathlib import Path

from botok import WordTokenizer
from bs4 import BeautifulSoup
from PIL import Image, UnidentifiedImageError

from create_ocr_data.checkpoints import (
    load_checkpoints,
    save_checkpoint,
    save_corrupted_files,
)

wt = WordTokenizer()


def latin_num_exists(text):
    # Regular expression to find any sequence of digits
    latin_num_pattern = r"\d"  # Matches any single digit

    # Search for at least one occurrence of a Latin number
    match = re.search(latin_num_pattern, text)

    # Return True if a match is found, False otherwise
    return match is not None


def analyze_ocr_texts(ocr_data):
    for line in ocr_data:
        tokens = wt.tokenize(line["text"])
        non_bo_num = False
        non_bo_word = False
        tib_num = False
        for token in tokens:
            if token.chunk_type in ["LATIN", "CJK", "OTHER"]:
                non_bo_word = True
                if token.chunk_type == "LATIN" and latin_num_exists(token.text):
                    non_bo_num = True
            if token.chunk_type == "NUM":
                tib_num = True
        line["text length"] = len(line["text"])
        line["non_bo_word"] = non_bo_word
        line["tib_num"] = tib_num
        line["non_bo_num"] = non_bo_num
    return ocr_data


def parse_html(html_file_path):
    """Parse HTML file to extract OCR data including OCR confidence."""
    try:
        with open(html_file_path, encoding="utf-8") as file:
            soup = BeautifulSoup(file, "html.parser")
            ocr_data = []
            for line in soup.find_all("span", {"class": "ocr_line"}):
                bbox = line["title"].split(";")[0].split()[1:]  # Extract bounding box
                bbox = [int(x) for x in bbox]
                text = line.text
                # Extract OCR confidence if available
                ocr_conf = None
                if "x_wconf" in line["title"]:
                    ocr_conf = int(
                        line["title"].split("x_wconf")[1].split(";")[0].strip()
                    )
                ocr_data.append({"bbox": bbox, "text": text, "ocr_conf": ocr_conf})
        return ocr_data
    except Exception as e:
        print(f"Error processing {html_file_path}: {e}")
        return None


def find_corresponding_image_path(html_file_path):
    html_file_path = Path(html_file_path)
    parts = html_file_path.parts
    page_id = html_file_path.stem
    image_path = Path(*parts[:-3], "ocr", "images", f"{page_id}")

    return image_path


def find_image_files(image_path_pattern):
    """Find image files matching a pattern."""
    return list(Path(image_path_pattern.parent).glob(f"{image_path_pattern.name}.*"))


def crop_and_save_line_images(image_file_path, ocr_data, output_dir, volume_id):
    """Crop and save line images from a page image based on OCR data."""
    try:
        # Assuming find_image_files is a function you've defined to locate image files.
        image_files = find_image_files(image_file_path)
        if not image_files:
            raise FileNotFoundError(f"No image file found for {image_file_path}")
        image = Image.open(image_files[0])
        page_id = image_files[0].stem

        # Construct the directory for the current page images
        image_page_id = f"{volume_id}{page_id[-4:]}"
        page_output_dir = output_dir / image_page_id
        page_output_dir.mkdir(
            parents=True, exist_ok=True
        )  # Create it only once per page

        for i, line in enumerate(ocr_data, start=1):
            line_image_id = f"{image_page_id}_{i:04d}"
            output_path = page_output_dir / f"{line_image_id}{image_files[0].suffix}"
            cropped_image = image.crop(line["bbox"])
            cropped_image.save(output_path)
            line["image_page_id"] = image_page_id
            line["line_image_name"] = output_path.name

        return ocr_data
    except UnidentifiedImageError as e:
        save_corrupted_files(image_file_path, f"UnidentifiedImageError {str(e)}")
    except Exception as e:
        save_corrupted_files(image_file_path, str(e))
    return None


def update_csv_files_by_category(
    base_csv_file_path, ocr_data, work_id, volume_id, page_id
):
    base_path_template = (
        str(base_csv_file_path.parent / (base_csv_file_path.stem + "_{}"))
        + base_csv_file_path.suffix
    )

    categories = ["51-89%", "90-100%", "0-50%"]
    writers = {}
    files = {}  # Dictionary to keep track of file handles

    # Define the header
    header = [
        "Work ID",
        "Volume ID",
        "Page ID",
        "Line Image Name",
        "OCR Confidence",
        "Tibetan Num",
        "Non Bo Word",
        "Non Bo Num",
        "Text_length",
        "Text",
    ]

    for category in categories:
        csv_file_path = Path(base_path_template.format(category))
        is_new_file = not csv_file_path.exists()  # Check if file exists
        csv_file = csv_file_path.open("a", newline="", encoding="utf-8")

        writers[category] = csv.writer(csv_file)
        files[category] = csv_file  # Store the file handle for later closing

        # If it's a new file, write the header
        if is_new_file:
            writers[category].writerow(header)

    for line in ocr_data:
        ocr_conf = line.get("ocr_conf")
        # Determine the confidence category
        if ocr_conf:
            if 51 <= ocr_conf <= 89:
                confidence_category = "51-89%"
            elif 90 <= ocr_conf <= 100:
                confidence_category = "90-100%"
            else:
                confidence_category = "0-50%"

        # Append the data row to the appropriate CSV
        writers[confidence_category].writerow(
            [
                work_id,
                volume_id,
                line["image_page_id"],
                line.get("line_image_name", "No Image"),
                ocr_conf if ocr_conf else "No Confidence",
                line.get("tib_num"),
                line.get("non_bo_word"),
                line.get("non_bo_num"),
                line.get("text length"),
                line["text"],
            ]
        )

    # Close all the file handles
    for file in files.values():
        file.close()


def process_volume_folder(volume_folder, checkpoints, output_base):
    for html_file in volume_folder.rglob("*.html"):
        if str(html_file) in checkpoints:
            continue  # Skip already processed files
        try:
            ocr_data = parse_html(html_file)
            if ocr_data is None:  # Skip if parsing failed
                continue
            image_path = find_corresponding_image_path(html_file)
            parts = image_path.parts
            work_id, work_volume_id = parts[-5:-3]
            volume_id = work_volume_id.split("-")[1]
            output_dir = output_base / work_id / "images"

            ocr_data = crop_and_save_line_images(
                image_path, ocr_data, output_dir, volume_id
            )
            ocr_data = analyze_ocr_texts(ocr_data)
            if ocr_data:  # Ensure OCR data was processed successfully
                csv_file_path = output_base / work_id / f"{work_id}.csv"
                update_csv_files_by_category(
                    csv_file_path,
                    ocr_data,
                    work_id,
                    volume_id,
                    image_path.name,
                )
                save_checkpoint(html_file)  # Mark as processed
        except Exception as e:
            save_corrupted_files(html_file, str(e))


def process_work_folder(work_folder, output_base):
    """Process HTML files in work folder, cropping images and updating CSVs."""
    checkpoints = load_checkpoints()
    for volume_folder in work_folder.iterdir():
        if not volume_folder.is_dir():
            continue
        process_volume_folder(volume_folder, checkpoints, output_base)
        save_checkpoint(volume_folder)


# Example usage:
if __name__ == "__main__":
    work_folder = Path(
        "/home/gangagyatso/Desktop/work/create_ocr_data/data/works/W00EGS1017555"
    )
    output_base = Path("./data/outputs")
    output_base.mkdir(parents=True, exist_ok=True)
    process_work_folder(work_folder, output_base)
