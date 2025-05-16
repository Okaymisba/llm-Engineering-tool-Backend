import fitz


def parse_pdf(file_stream):
    """
    Parses the content of a PDF file stream into plain text.

    This function reads a PDF file provided as a binary stream and extracts
    its textual content page by page. After extracting the text from all pages,
    the function concatenates them and removes any leading or trailing whitespace
    before returning the result.

    .. note::
       This function requires the `PyMuPDF` library (`fitz` module) to process PDF files.

    :param file_stream: A binary stream representing the PDF file to be parsed.
    :type file_stream: io.BytesIO or similar binary stream object
    :return: A string containing the concatenated plain text extracted from all pages
        of the provided PDF.
    :rtype: str
    """

    text = ""

    with fitz.open(stream=file_stream, filetype="pdf") as doc:
        for page in doc:
            text += page.get_text() + "\n"

    return text.strip()
