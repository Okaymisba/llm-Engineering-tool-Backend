def parse_txt_file(file_stream):
    """
    Parses the input binary stream of a .txt file and returns its content as a cleaned string.

    This function decodes the provided binary stream (assumed to be UTF-8 encoded) and removes
    any leading or trailing whitespace characters from the decoded string.

    :param file_stream: Binary stream of the .txt file.
    :type file_stream: bytes
    :return: Content of the .txt file as a stripped UTF-8 string.
    :rtype: str
    """

    return file_stream.decode('utf-8').strip()
