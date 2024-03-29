import csv
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


def analyze_ocr_texts(ocr_data):
    for line in ocr_data:
        tokens = wt.tokenize(line["text"])
        non_word_count = 0
        non_bo_word_count = 0
        tib_num_count = 0
        for token in tokens:
            if token.pos == "NON_WORD" and not token.skrt:
                non_word_count += 1
            if token.chunk_type in ["LATIN", "CJK", "OTHER"] and (
                token.chunk_type != "OTHER" or not token.skrt
            ):
                non_bo_word_count += 1
            if token.chunk_type == "NUM":
                tib_num_count += 1
        if len(tokens) > 0:
            if (
                non_word_count / len(tokens) > 0.01
                or non_bo_word_count / len(tokens) > 0.01
            ):
                line["validity"] = "Invalid"
            else:
                line["validity"] = "Valid"

        line["word_count"] = len(tokens)
        line["non_bo_word_count"] = non_bo_word_count
        line["non_word_count"] = non_word_count
        line["tib_num_count"] = tib_num_count

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
    # Extract parts needed to construct the image path
    parts = list(html_file_path.parts)
    work_id_volume_id = parts[-3]  # Assuming this is 'W00EGS1016612-I01JW78' format
    volume_id = work_id_volume_id.split("-")[1]
    html_id = parts[-1][:-5]
    page_id = (
        f"{volume_id}{html_id[-4:]}"  # Remove .html and prepend with work_id_volume_id
    )
    image_path = Path(work_id_volume_id, "images", page_id)
    return image_path


def find_image_files(image_path_pattern):
    """Find image files matching a pattern."""
    return list(Path(image_path_pattern.parent).glob(f"{image_path_pattern.name}.*"))


def crop_and_save_line_images(image_file_path, ocr_data, output_dir):
    """Crop and save line images from a page image based on OCR data."""
    try:
        image_files = find_image_files(image_file_path)
        if not image_files:
            raise FileNotFoundError(f"No image file found for {image_file_path}")
        image = Image.open(image_files[0])
        page_id = image_files[0].stem
        for i, line in enumerate(ocr_data, start=1):
            line_image_id = f"{page_id}_{i:04d}"
            output_path = output_dir / f"{line_image_id}{image_files[0].suffix}"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            cropped_image = image.crop(line["bbox"])
            cropped_image.save(output_path)
            line["line_image_name"] = output_path.name
        return ocr_data
    except UnidentifiedImageError as e:
        save_corrupted_files(image_file_path, f"UnidentifiedImageError {str(e)}")
    except Exception as e:
        save_corrupted_files(image_file_path, str(e))
    return None


def update_csv_files_by_category(
    base_csv_file_path, ocr_data, repo_id, work_id, volume_id, page_id
):
    base_path_template = (
        str(base_csv_file_path.parent / (base_csv_file_path.stem + "_{}"))
        + base_csv_file_path.suffix
    )

    categories = ["50-75%", "76-90%", "91-100%", "Uncategorized", "No Confidence Data"]
    writers = {}
    files = {}  # Dictionary to keep track of file handles

    # Define the header
    header = [
        "Repo ID",
        "Work ID",
        "Volume ID",
        "Page ID",
        "Line Image Name",
        "OCR Confidence",
        "Word Count",
        "Non Word Count",
        "Non Bo Word Count",
        "Tib Num Count",
        "validty",
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
            if 50 <= ocr_conf <= 75:
                confidence_category = "50-75%"
            elif 76 <= ocr_conf <= 90:
                confidence_category = "76-90%"
            elif 91 <= ocr_conf <= 100:
                confidence_category = "91-100%"
            else:
                confidence_category = "Uncategorized"
        else:
            confidence_category = "No Confidence Data"

        # Append the data row to the appropriate CSV
        writers[confidence_category].writerow(
            [
                repo_id,
                work_id,
                volume_id,
                page_id,
                line.get("line_image_name", "No Image"),
                ocr_conf if ocr_conf else "No Data",
                line.get("word_count", "N/A"),
                line.get("non_word_count", "N/A"),
                line.get("non_bo_word_count", "N/A"),
                line.get("tib_num_count", "N/A"),
                line.get("validity", "N/A"),
                line.get("text", "N/A"),
            ]
        )

    # Close all the file handles
    for file in files.values():
        file.close()


def process_repo_folder(repo_folder, work_image_folder, output_base):
    """Process HTML files in repo folder, cropping images and updating CSVs."""
    checkpoints = load_checkpoints()
    for html_file in Path(repo_folder).rglob("*.html"):
        if str(html_file) in checkpoints:
            continue  # Skip already processed files
        try:
            ocr_data = parse_html(html_file)
            if ocr_data is None:  # Skip if parsing failed
                continue
            image_path = find_corresponding_image_path(html_file)
            work_id = image_path.parts[0].split("-")[0]
            volume_id = image_path.parts[0].split("-")[1]
            output_dir = output_base / work_id / image_path
            image_file_path = work_image_folder / f"{image_path}"
            ocr_data = crop_and_save_line_images(image_file_path, ocr_data, output_dir)
            ocr_data = analyze_ocr_texts(ocr_data)
            if ocr_data:  # Ensure OCR data was processed successfully
                csv_file_path = output_base / work_id / f"{work_id}.csv"
                repo_id = repo_folder.name
                update_csv_files_by_category(
                    csv_file_path,
                    ocr_data,
                    repo_id,
                    work_id,
                    volume_id,
                    image_file_path.name,
                )
                save_checkpoint(html_file)  # Mark as processed
        except Exception as e:
            save_corrupted_files(html_file, str(e))


# Example usage:
if __name__ == "__main__":
    repo_folder = Path(
        "/home/gangagyatso/Desktop/work/create_ocr_data/data/assets/IF15C06ED"
    )
    work_image_folder = Path(
        "/home/gangagyatso/Desktop/work/create_ocr_data/data/works/W00EGS1016612"
    )
    output_base = Path("./data/output")
    output_base.mkdir(parents=True, exist_ok=True)
    process_repo_folder(repo_folder, work_image_folder, output_base)
