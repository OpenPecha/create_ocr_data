from pathlib import Path

"""checkpoint system"""
CORRUPTED_FILES = Path("corrupted_file.txt")
if not CORRUPTED_FILES.exists():
    CORRUPTED_FILES.touch()


def save_corrupted_files(file_path: Path, error: str) -> None:
    with open(CORRUPTED_FILES, "a") as f:
        f.write(f"{file_path}-{error}\n")


"""check point system"""

CONVERT_CHECKPOINT = Path("checkpoint.txt")


def load_checkpoints():
    if CONVERT_CHECKPOINT.exists():
        return CONVERT_CHECKPOINT.read_text().splitlines()

    CONVERT_CHECKPOINT.touch()
    return []


def save_checkpoint(file_checkpoint: Path):
    with open(CONVERT_CHECKPOINT, "a") as f:
        f.write(f"{str(file_checkpoint)}\n")
