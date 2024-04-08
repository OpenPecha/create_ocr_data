import csv
from pathlib import Path
from shutil import copy2
from typing import Any, Dict, List


def organize_images_and_create_category_csvs(
    csv_file_path, images_base_path, output_base
):
    """
    Organize images into specific folders based on CSV data, including counts, volume-wise,
    and create separate CSV files for each category.
    """

    category_rows: Dict[str, List[Dict[str, Any]]] = {
        "bo_text": [],
        "bo_number": [],
        "non_bo_text": [],
        "non_bo_number": [],
    }

    desired_columns = [
        "Work ID",
        "Volume ID",
        "Page ID",
        "Line Image Name",
        "OCR Confidence",
        "Text",
    ]

    with open(csv_file_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Determine folder structure based on CSV row
            tib_num = row["Tibetan Num"].lower() == "true"
            non_bo_word = row["Non Bo Word"].lower() == "true"
            non_bo_num = row["Non Bo Num"].lower() == "true"
            text_length = int(row["Text_length"])

            if text_length < 10:
                continue

            # Determine the target subfolder and category key based on the criteria
            if not tib_num and not non_bo_word:
                target_folder = output_base / "bo/text"
                category_key = "bo_text"
            elif tib_num and not non_bo_word:
                target_folder = output_base / "bo/number"
                category_key = "bo_number"
            elif non_bo_word and non_bo_num:
                target_folder = output_base / "non_bo/number"
                category_key = "non_bo_number"
            else:
                target_folder = output_base / "non_bo/text"
                category_key = "non_bo_text"

            # Add row to the corresponding category list
            category_rows[category_key].append(row)

            # Ensure the target directory exists
            target_folder.mkdir(parents=True, exist_ok=True)

            # Construct the source image path
            source_path = (
                images_base_path / "images" / row["Page ID"] / row["Line Image Name"]
            )

            # Copy the image to the target folder
            try:
                copy2(source_path, target_folder / row["Line Image Name"])
            except FileNotFoundError:
                print(f"File not found: {source_path}")

    # Create category CSVs with filtered rows
    for category, rows in category_rows.items():
        category_csv_path = output_base.parent / "csv" / f"{category}.csv"
        category_csv_path.parent.mkdir(
            parents=True, exist_ok=True
        )  # Ensure directory exists
        if rows:  # Only create CSV if there are rows to write
            with open(
                category_csv_path, mode="w", newline="", encoding="utf-8"
            ) as file:
                # Initialize writer with only the desired columns
                writer = csv.DictWriter(file, fieldnames=desired_columns)
                writer.writeheader()
                # Filter each row to include only the desired columns before writing
                filtered_rows = [
                    {col: row[col] for col in desired_columns if col in row}
                    for row in rows
                ]
                writer.writerows(filtered_rows)


if __name__ == "__main__":
    # Example path setup
    csv_file_path = Path(
        "/home/gangagyatso/Desktop/work/create_ocr_data/data/outputs/W00EGS1017555/W00EGS1017555_90-100%.csv"
    )
    images_base_path = Path(
        "/home/gangagyatso/Desktop/work/create_ocr_data/data/outputs/W00EGS1017555/"
    )
    output_base = Path("./data/outputs/W00EGS1017555/filtered_images")
    output_base.mkdir(parents=True, exist_ok=True)

    organize_images_and_create_category_csvs(
        csv_file_path, images_base_path, output_base
    )
