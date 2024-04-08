from pathlib import Path

from create_ocr_data.pipeline import (
    analyze_ocr_texts,
    crop_and_save_line_images,
    parse_html,
)


def test_analyze_ocr_texts():
    html_file_path = Path(
        "./tests/test_data/work/work_volume_id/ocr/html/00000005.html"
    )
    ocr_data = parse_html(html_file_path)
    if ocr_data:
        # Step 2: Call the function to crop and save line images
        image_file_path = Path(
            "./tests/test_data/work/work_volume_id/ocr/images/00000005"
        )
        output_dir = Path(
            "./tests/test_data/output/work/work_volume_id/ocr/images/00000005"
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        result_ocr_data = crop_and_save_line_images(
            image_file_path, ocr_data, output_dir, volume_id="volume_id"
        )
        analyzed_data = analyze_ocr_texts(result_ocr_data)

        # Assert that the analyzed data includes the expected keys with correct boolean values
        assert not analyzed_data[0][
            "non_bo_word"
        ], "First line should contain non-bo word"
        assert not analyzed_data[0]["tib_num"], "First line should not contain tib num"
        assert not analyzed_data[0][
            "non_bo_num"
        ], "First line should contain non-bo num"

        assert not analyzed_data[1][
            "non_bo_word"
        ], "Second line should contain non-bo word"
        assert not analyzed_data[1]["tib_num"], "Second line should contain tib num"
        assert not analyzed_data[1][
            "non_bo_num"
        ], "Second line should not contain non-bo num"

        print("All assertions passed for test_analyze_ocr_texts.")
    else:
        print("Failed to parse OCR data.")


if __name__ == "__main__":
    test_analyze_ocr_texts()
