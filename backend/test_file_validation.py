from file_routes import validate_file_content


def test_valid_pdf_signature():
    assert validate_file_content("report.pdf", b"%PDF-1.7 test content")


def test_invalid_pdf_signature():
    assert not validate_file_content("report.pdf", b"This is not a PDF")


def test_empty_file_is_rejected():
    assert not validate_file_content("report.txt", b"")


def test_text_file_accepts_utf8():
    assert validate_file_content("report.txt", "Hello Aditya!".encode("utf-8"))


def test_text_file_rejects_invalid_utf8():
    assert not validate_file_content("report.txt", b"\xff\xfe\xfa")


def test_extension_content_mismatch_is_rejected():
    assert not validate_file_content("report.pdf", b"Plain text content")


def test_unknown_extension_is_rejected():
    assert not validate_file_content("script.exe", b"MZ executable content")


def test_valid_png_signature():
    png_signature = b"\x89PNG\r\n\x1a\n"
    assert validate_file_content("image.png", png_signature + b"test")
