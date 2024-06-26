import shutil
import zipfile
from pathlib import Path

import pandas as pd


def zip_dir(src_dir: Path, dest_zip: Path):
    """
    Compresses a directory (src_dir) into a zip file located at dest_zip.
    Uses pathlib for path operations.
    """
    with zipfile.ZipFile(dest_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file_path in src_dir.glob("**/*"):
            if file_path.is_file():
                zipf.write(file_path, file_path.relative_to(src_dir.parent))


def reorganize_directory_structure(base_path: Path, new_base_path: Path):
    new_base_path.mkdir(parents=True, exist_ok=True)
    for work_id in base_path.iterdir():
        if not work_id.is_dir():
            continue

        paths = {
            "bo_text": new_base_path / "bo" / "text" / work_id.name,
            "bo_number": new_base_path / "bo" / "numbers" / work_id.name,
            "non_bo_text": new_base_path / "non-bo" / work_id.name,
            "non_bo_number": new_base_path / "non-bo" / work_id.name,
        }

        # Create new directories and their image subdirectories
        for path in paths.values():
            (path / "images").mkdir(parents=True, exist_ok=True)

        # Move image files
        filter_images_path = work_id / "filtered_images"
        for category_dir in filter_images_path.iterdir():
            for sub_category_dir in category_dir.iterdir():
                dest_path = paths[f"{category_dir.name}_{sub_category_dir.name}"]
                for image_file in sub_category_dir.iterdir():
                    shutil.copy(str(image_file), dest_path / "images")

        # Move CSV files
        csv_path = Path(work_id) / "csv"
        for csv_file in csv_path.iterdir():
            category = csv_file.stem
            dest_path = paths[category]
            dest_file_path = dest_path / f"{work_id.name}.csv"

            if dest_file_path.exists():
                # File exists, append new data to existing CSV
                existing_df = pd.read_csv(dest_file_path)
                new_df = pd.read_csv(csv_file)
                combined_df = pd.concat([existing_df, new_df[1:]])
                combined_df.to_csv(dest_file_path, index=False)
            else:
                # File does not exist, copy the new file
                shutil.copy(str(csv_file), dest_file_path)

        for key, path in paths.items():
            zip_file_path = path.parent / f"{path.name}.zip"
            zip_dir(path, zip_file_path)

            # Check if the directory exists before trying to remove it
            if path.exists():
                shutil.rmtree(path)
            else:
                print(f"Attempted to remove non-existing directory: {path}")


# Call the function
base_path = Path("../../data/output_data")
new_base_path = Path("../../data/outputs_new")
reorganize_directory_structure(base_path, new_base_path)
