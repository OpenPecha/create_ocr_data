import zipfile
from pathlib import Path


def extract_zip_file(zip_path):
    """
    Extract a zip file to a specified location based on its content indication ('html' or 'images').
    The target folder is determined by the zip file's name.
    """

    extract_path = zip_path.parent / zip_path.stem

    # Ensure the target directory exists
    extract_path.mkdir(parents=True, exist_ok=True)

    # Extract the zip file
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_path)
        print(f"Extracted: {zip_path} to {extract_path}")


if __name__ == "__main__":
    zip_file_dir = Path("/home/gangagyatso/Desktop/work/create_ocr_data/data/works")
    for zip_file in zip_file_dir.rglob("*.zip"):
        extract_zip_file(zip_file)
