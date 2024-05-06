from multiprocessing import Pool
from pathlib import Path

from tqdm import tqdm

from create_ocr_data.checkpoints import (
    load_checkpoints,
    save_checkpoint,
    save_corrupted_files,
)
from create_ocr_data.extract_valid_image import organize_images_and_create_category_csvs
from create_ocr_data.pipeline import process_work_folder


def worker_task(args):
    work, output_dir, checkpoints = args
    work = Path(work)
    work_id = work.name
    output_work_dir = Path(output_dir / work_id)
    csv_file_path = output_work_dir / f"{work_id}_90-100%.csv"
    images_base_path = output_work_dir
    output_base = output_work_dir / "filtered_images"
    if f"{str(work)}" in checkpoints:
        return
    try:
        process_work_folder(work, output_dir)
        organize_images_and_create_category_csvs(
            csv_file_path, images_base_path, output_base
        )
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
                desc="Creating OCR data...",
            )
        )


if __name__ == "__main__":
    works = Path("../../data/extracted_data")

    output_dir = Path("../../data/output_data")
    output_dir.mkdir(parents=True, exist_ok=True)
    num_processes = 10
    process_all_works(works, output_dir, num_processes)
