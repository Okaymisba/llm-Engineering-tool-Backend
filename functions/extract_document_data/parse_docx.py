import io

from docx import Document


def parse_docx(file_stream):
    """
    Parses the content of a .docx file and extracts its text content.

    This function takes a file-like byte stream of a .docx file as input,
    parses its contents and concatenates the text from all paragraphs into
    a single string. Every paragraph text is separated by a newline character.

    :param file_stream: A byte stream representing a .docx file.
    :type file_stream: io.BytesIO
    :return: A string containing the combined text content of the .docx file,
        with paragraphs separated by newline characters.
    :rtype: str
    """

    document = Document(io.BytesIO(file_stream))

    text = ""
    for paragraph in document.paragraphs:
        text += paragraph.text + "\n"

    return text.strip()
