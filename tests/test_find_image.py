from pathlib import Path

from create_ocr_data.pipeline import find_corresponding_image_path


def test_find_corresponding_image_path():
    html_path = Path("tests/test_data/work/work_volume_id/ocr/html/00000005.html")
    image_path = find_corresponding_image_path(html_path)

    # Assuming the image path is derived from the HTML path based on your file structure
    expected_image_path = Path(
        "tests/test_data/work/work_volume_id/ocr/images/00000005"
    )

    assert (
        image_path == expected_image_path
    ), "Image path does not match expected output"

    print("All tests passed!")
