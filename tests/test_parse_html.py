from pathlib import Path

from create_ocr_data.pipeline import parse_html


def test_parse_html():
    html_path = Path("tests/test_data/work/work_volume_id/ocr/html/00000005.html")
    parsed_data = parse_html(html_path)

    # Assuming parsed_data is a list of dictionaries for each line of OCR text
    # Let's verify the structure and content of the first few lines based on your HTML content
    expected_first_line = {
        "bbox": [752, 896, 2510, 1186],
        "text": "༄༅། །རང་ཉིད་ངོ་སྤྲོད་",
        "ocr_conf": 100,
    }

    expected_second_line = {
        "bbox": [1366, 2403, 1820, 2591],
        "text": "རྩོམ་པ་པོ། ",
        "ocr_conf": 100,
    }

    # Verify the length of the parsed_data to ensure all lines are extracted
    assert len(parsed_data) == 4, "Expected 4 lines of OCR data"

    # Verify the content of the first and second lines
    assert (
        parsed_data[0] == expected_first_line
    ), "First line OCR data does not match expected output"
    assert (
        parsed_data[1] == expected_second_line
    ), "Second line OCR data does not match expected output"

    # You can add more assertions here for the rest of the lines or for specific properties you care about

    print("All tests passed!")
