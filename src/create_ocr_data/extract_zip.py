import os
import zipfile


def extract_zip(zip_path, extract_to):
    """
    Extracts a ZIP file to a specified location.
    """
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_to)


def find_and_extract_zip(root_path, output_path):
    """
    Recursively finds ZIP files in the given directory and subdirectories,
    and extracts them.
    """
    for root, dirs, files in os.walk(root_path):
        for filename in files:
            if filename.endswith(".zip"):
                # Correctly construct zip_path from the current root
                zip_path = os.path.join(root, filename)
                print(f"Extracting: {zip_path}")
                # Prepare a corresponding output directory within output_path
                relative_root = os.path.relpath(root, start=root_path)
                extract_to = os.path.join(
                    output_path, relative_root, os.path.splitext(filename)[0]
                )
                if not os.path.exists(extract_to):
                    os.makedirs(extract_to)
                extract_zip(zip_path, extract_to)
                # Recursively search the newly extracted directory for more ZIP files
                find_and_extract_zip(
                    extract_to, extract_to
                )  # Adjusted to use extract_to for both parameters


if __name__ == "__main__":
    root_path = "../../data/work_zip"
    output_path = "../../data/extracted_data"
    find_and_extract_zip(root_path, output_path)
