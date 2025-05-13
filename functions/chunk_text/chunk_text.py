def chunk_document_text(text, chunk_size=200):
    """
    Divides the input text into smaller chunks of specified size.

    :param text: The input text to be chunked.
    :param chunk_size: The maximum size of each chunk in characters. Default is 100.
    :return: A list of text chunks.
    """
    if not text:
        return []

    words = text.split()
    chunks = []
    current_chunk = []

    current_length = 0

    for word in words:
        # Check if adding the word exceeds the chunk size
        if current_length + len(word) + 1 > chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_length = 0

        current_chunk.append(word)
        current_length += len(word) + 1  # Add 1 for the space

    # Append the last chunk if it exists
    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks
