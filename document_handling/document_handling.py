import docx
import fitz


def parse_pdf(file_path):
    """
    Parses the content of a PDF file and extracts all textual information
    from its pages.

    This function utilizes the PyMuPDF library to open the specified
    PDF file and iterate through its pages to collect their textual
    content. The resulting text is compiled into a single string.

    :param file_path: The file path to the PDF document to be parsed.
    :type file_path: str
    :return: A string containing all the textual content extracted from
        the PDF file.
    :rtype: str
    """

    text = ""
    with fitz.open(file_path) as doc:
        for page in doc:
            text += page.get_text()
    return text


def parse_docx(file_path):
    """
    Parses a .docx file and extracts text content from all paragraphs.

    This function takes the file path of a .docx document, opens the file,
    and extracts the text from each paragraph into a single concatenated string.
    Each paragraph's text is separated by a newline character in the returned
    string.

    :param file_path: Path to the .docx file to be parsed
    :type file_path: str
    :return: A string containing the concatenated text from all paragraphs of
        the .docx document, separated by newline characters
    :rtype: str
    """

    doc = docx.Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])


def parse_document(file_path):
    """
    Parses a document based on its file type. The function identifies the file
    type (e.g., PDF, DOCX, or image) from the file extension and performs an
    appropriate parsing operation. For unsupported file formats, it raises a
    ValueError.

    :param file_path: Path to the document file to be parsed.
    :type file_path: str
    :return: The parsed content of the document.
    :rtype: Any
    :raises ValueError: If the file type is unsupported.
    """

    if file_path.endswith('.pdf'):
        return parse_pdf(file_path)
    elif file_path.endswith('.docx'):
        return parse_docx(file_path)
    else:
        raise ValueError("Unsupported file type.")
