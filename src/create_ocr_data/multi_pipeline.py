from multiprocessing import Pool
from pathlib import Path

from tqdm import tqdm

from create_ocr_data.checkpoints import (
    load_checkpoints,
    save_checkpoint,
    save_corrupted_files,
)
from create_ocr_data.extract_valid_image import (
    filter_and_copy_csv,
    organize_images_by_criteria,
)
from create_ocr_data.pipeline import process_work_folder


def worker_task(args):
    work, output_dir, checkpoints = args
    work = Path(work)
    work_id = work.name
    output_work_dir = Path(output_dir / work_id)
    desired_columns = [
        "Work ID",
        "Volume ID",
        "Page ID",
        "Line Image Name",
        "OCR Confidence",
        "Text",
    ]
    if f"{str(work)}" in checkpoints:
        return
    try:
        process_work_folder(work, output_dir)
        organize_images_by_criteria(
            output_work_dir / f"{work_id}_86-100%.csv",
            output_work_dir,
            output_work_dir / "filtered_images",
        )
        csv_file_paths = list(output_work_dir.rglob("*.csv"))
        filter_and_copy_csv(csv_file_paths, desired_columns)
        save_checkpoint(work)
    except Exception as e:
        save_corrupted_files(work, str(e))
        print(f"Error processing {work}: {e}")


# Note: Updated the 'elif' for PDF to TXT and JPEG conversion to fit the expected arguments structure of `process_pdf`.
# Ensure the `process_pdf` function is adapted to handle the directory paths correctly, especially if it expects
# specific subdirectories for images and text.


def process_all_works(works: Path, output_dir: Path, num_processes: int = 10):
    checkpoints = load_checkpoints()
    tasks = [(work, output_dir, checkpoints) for work in works.iterdir()]

    num_processes = num_processes
    with Pool(processes=num_processes) as pool:
        list(
            tqdm(
                pool.imap(worker_task, tasks),
                total=len(tasks),
                desc="Converting files to txt",
            )
        )


if __name__ == "__main__":
    works = Path("./data/works")

    output_dir = Path("./data/outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    num_processes = 4
    process_all_works(works, output_dir, num_processes)
