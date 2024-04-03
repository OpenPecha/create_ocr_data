import csv
from pathlib import Path
from shutil import copy2


def organize_images_by_criteria(csv_file_path, images_base_path, output_base):
    """
    Organize images into specific folders based on CSV data, including counts, volume-wise.

    :param csv_file_path: Path to the CSV file.
    :param images_base_path: Base path where the original images are stored.
    :param output_base: Base output directory for organizing images volume-wise.
    """
    with open(csv_file_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Determine folder structure based on CSV row
            volume_folder = output_base / f"{row['Work ID']}-{row['Volume ID']}"
            tib_num = row["Tibetan Num"].lower() == "true"
            non_bo_word = row["Non Bo Word"].lower() == "true"
            non_bo_num = row["Non Bo Num"].lower() == "true"

            # Determine the target subfolder based on the criteria
            if not tib_num and not non_bo_word:
                target_folder = volume_folder / "bo/text"
            elif tib_num and not non_bo_word:
                target_folder = volume_folder / "bo/number"
            elif non_bo_word and non_bo_num:
                target_folder = volume_folder / "non_bo/number"
            else:
                target_folder = volume_folder / "non_bo/text"

            # Ensure the target directory exists
            target_folder.mkdir(parents=True, exist_ok=True)

            # Construct the source image path
            # Construct the source image path
            source_path = (
                images_base_path
                / f"{row['Work ID']}-{row['Volume ID']}"
                / "images"
                / row["Page ID"]
                / row["Line Image Name"]
            )
            # Copy the image to the target folder
            try:
                copy2(source_path, target_folder / row["Line Image Name"])
            except FileNotFoundError:
                print(f"File not found: {source_path}")


def filter_and_copy_csv(file_paths, desired_columns):
    """
    Copies CSV files with only a subset of columns to a subdirectory 'csv'.

    :param file_paths: Iterable of Paths to the CSV files.
    :param desired_columns: List of column names to retain in the new CSV files.
    """
    for file_path in file_paths:
        # Define the output directory ('csv' folder within the same directory as the source file)
        output_dir = file_path.parent / "csv"
        output_dir.mkdir(exist_ok=True)  # Create the directory if it doesn't exist

        # Define the output file path
        output_file_path = output_dir / file_path.name

        with open(file_path, newline="", encoding="utf-8") as infile, open(
            output_file_path, mode="w", newline="", encoding="utf-8"
        ) as outfile:
            reader = csv.DictReader(infile)
            writer = csv.DictWriter(outfile, fieldnames=desired_columns)

            # Write the header and desired columns to the new file
            writer.writeheader()
            for row in reader:
                writer.writerow({col: row[col] for col in desired_columns})


if __name__ == "__main__":
    # Example path setup
    csv_file_path = Path(
        "/home/gangagyatso/Desktop/work/create_ocr_data/data/outputs/W00EGS1017555/W00EGS1017555_86-100%.csv"
    )
    images_base_path = Path(
        "/home/gangagyatso/Desktop/work/create_ocr_data/data/outputs/W00EGS1017555/"
    )
    output_base = Path("./data/outputs/W00EGS1017555/filtered_images")
    output_base.mkdir(parents=True, exist_ok=True)

    organize_images_by_criteria(csv_file_path, images_base_path, output_base)

    # Correctly find all CSV files using "*.csv" pattern
    csv_file_paths = list(
        csv_file_path.parent.glob("*.csv")
    )  # Use .glob instead of .rglob for direct children

    # Define the desired columns to retain in the new CSV files
    desired_columns = [
        "Work ID",
        "Volume ID",
        "Page ID",
        "Line Image Name",
        "OCR Confidence",
        "Text",
    ]
    filter_and_copy_csv(csv_file_paths, desired_columns)
