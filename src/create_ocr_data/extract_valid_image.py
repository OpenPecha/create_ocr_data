import csv
from pathlib import Path
from shutil import copy2


def organize_images_by_validity(csv_file_path, images_base_path, output_base):
    """
    Organize images into 'valid' and 'invalid' folders based on CSV data.

    :param csv_file_path: Path to the CSV file.
    :param images_base_path: Base path where the original images are stored.
    :param output_base: Base output directory for organizing valid and invalid images.
    """
    valid_folder = output_base / "valid_images"
    invalid_folder = output_base / "invalid_images"
    valid_folder.mkdir(parents=True, exist_ok=True)
    invalid_folder.mkdir(parents=True, exist_ok=True)

    with open(csv_file_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            image_name = row["Line Image Name"]
            validity = row["validty"]
            # Determine the target folder based on validity
            target_folder = (
                valid_folder if validity.lower() == "valid" else invalid_folder
            )

            # Construct the source image path
            source_path = (
                images_base_path
                / f"{row['Work ID']}-{row['Volume ID']}"
                / "images"
                / row["Page ID"]
                / image_name
            )

            # Copy the image to the target folder
            try:
                copy2(source_path, target_folder / image_name)
                print(f"Copied: {source_path} to {target_folder / image_name}")
            except FileNotFoundError:
                print(f"File not found: {source_path}")


# Define your paths here
csv_file_path = (
    "./data/output/W00EGS1016612/W00EGS1016612_91-100%.csv"  # Update this path
)
images_base_path = Path("./data/output/W00EGS1016612")
output_base = Path("./data/output/W00EGS1016612/")
organize_images_by_validity(Path(csv_file_path), images_base_path, output_base)
