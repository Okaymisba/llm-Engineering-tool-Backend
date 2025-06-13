import os

def parse_txt_file(file_input):
    """
    Parses the content of a text file and returns its content as a cleaned string.

    Args:
        file_input: Either a file path (str) or a file stream (bytes/io.BytesIO)
        
    Returns:
        str: The content of the text file
    """
    try:
        # Handle both file paths and file streams
        if isinstance(file_input, str):
            # If it's a file path, read the file
            with open(file_input, 'r', encoding='utf-8') as file:
                return file.read().strip()
        else:
            # If it's a stream, decode it directly
            return file_input.decode('utf-8').strip()
            
    except Exception as e:
        raise Exception(f"Error processing text file: {str(e)}")