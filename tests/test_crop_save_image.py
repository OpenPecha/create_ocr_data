from pathlib import Path

from create_ocr_data.pipeline import crop_and_save_line_images, parse_html


def test_crop_and_save_line_images():
    html_file_path = Path(
        "./tests/test_data/work/work_volume_id/ocr/html/00000005.html"
    )
    ocr_data = parse_html(html_file_path)
    if ocr_data:
        # Step 2: Call the function to crop and save line images
        image_file_path = Path(
            "./tests/test_data/work/work_volume_id/ocr/images/00000005"
        )
        output_dir = Path("./tests/test_data/output/work/work_volume_id/ocr/images/")
        output_dir.mkdir(parents=True, exist_ok=True)
        result_ocr_data = crop_and_save_line_images(
            image_file_path, ocr_data, output_dir, volume_id="volume_id"
        )

        assert result_ocr_data is not None, "The function should return OCR data"
        for i, line in enumerate(result_ocr_data, start=1):
            line_image_path = (
                output_dir / "volume_id0005" / f"volume_id0005_{i:04d}.tif"
            )
            assert (
                line_image_path.exists()
            ), f"Expected cropped image file {line_image_path} was not created"
            assert (
                "line_image_name" in line
            ), "Expected 'line_image_name' in the result OCR data"
            assert (
                line["line_image_name"] == line_image_path.name
            ), "The 'line_image_name' does not match the expected file name"
    else:
        print("Failed to parse OCR data.")


if __name__ == "__main__":
    test_crop_and_save_line_images()
