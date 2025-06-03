import logging

import tiktoken

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def count_tokens(text: str, buffer_percent: float = 0.0) -> int:
    """
    Counts the number of tokens in the provided text using a specific encoding
    scheme while accounting for an optional buffer percentage. The buffer
    percentage increases the token count by a proportional amount to the original
    token count.

    :param text: The input text for which tokens need to be counted.
    :type text: str
    :param buffer_percent: The optional percentage of buffer to add to the token
        count. Must be a float value. Defaults to 0.0.
    :type buffer_percent: float
    :return: The total number of tokens, including the buffer.
    :rtype: int
    """
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
        total_tokens = len(encoding.encode(text))

        buffer_tokens = int(total_tokens * buffer_percent)
        total_tokens += total_tokens + buffer_tokens

        return total_tokens

    except Exception as e:
        logger.error(f"Error counting tokens: {e}")
        return 0
