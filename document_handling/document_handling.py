import fitz
import pytesseract
from PIL import Image
import docx


def parse_pdf(file_path):
    """
    Extracts text from a pdf file.

    This function opens a pdf file and extracts the text content from each page.
    The extracted text is concatenated into a single string and returned.

    Args:
        file_path (str): The path to the pdf file to be parsed.

    Returns:
        str: The extracted text from the pdf file.
    """

    text = ""
    with fitz.open(file_path) as doc:
        for page in doc:
            text += page.get_text()
    return text


def parse_docx(file_path):
    """
    Extracts text from a docx file.

    This function opens a docx file and extracts the text content from each paragraph.
    The extracted text is concatenated into a single string and returned.

    Args:
        file_path (str): The path to the docx file to be parsed.

    Returns:
        str: The concatenated text content of the docx file.
    """

    doc = docx.Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])


def parse_image(file_path):
    """
    Extracts text from an image file.

    This function opens an image file and uses the Tesseract OCR engine to extract
    text from the image. The extracted text is returned as a string.

    Args:
        file_path (str): The path to the image file to be parsed.

    Returns:
        str: The extracted text from the image file.
    """

    image = Image.open(file_path)
    return pytesseract.image_to_string(image)


def parse_document(file_path):
    """
    Extracts text from a given document.

    This function takes a file path as argument and extracts the text content from the given document.
    It supports pdf, docx and image files. The extracted text is returned as a string.

    Args:
        file_path (str): The path to the document to be parsed.

    Returns:
        str: The extracted text from the document.

    Raises:
        ValueError: If the file type is not supported.
    """
    if file_path.endswith('.pdf'):
        return parse_pdf(file_path)
    elif file_path.endswith('.docx'):
        return parse_docx(file_path)
    elif file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
        return parse_image(file_path)
    else:
        raise ValueError("Unsupported file type.")
