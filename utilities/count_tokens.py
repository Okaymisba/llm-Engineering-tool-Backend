import tiktoken
from transformers import AutoTokenizer
import logging
from typing import Optional
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_tokenizer(model: str) -> Optional[AutoTokenizer]:
    """
    Get the appropriate tokenizer for general models.

    Args:
        model (str): The model name (e.g., "deepseek", "llama-3.0")

    Returns:
        Optional[AutoTokenizer]: The tokenizer object or None if not found
    """
    try:
        return AutoTokenizer.from_pretrained(model)
    except Exception as e:
        logger.error(f"Error loading tokenizer for model {model}: {str(e)}")
        return None

def count_tokens(text: str, model: str = "deepseek") -> int:
    """
    Counts the number of tokens in a given text for general models like deepseek, llama, and mistral.

    Args:
        text (str): The input text (prompt or response)
        model (str): The model name (e.g., "deepseek", "llama-3.0")

    Returns:
        int: Number of tokens in the input text
    """
    try:
        tokenizer = get_tokenizer(model)
        if tokenizer is None:
            logger.warning(f"Using fallback tokenizer for model {model}")
            # Fallback to a basic tokenizer if the model-specific one fails
            tokenizer = AutoTokenizer.from_pretrained("gpt2")
        return len(tokenizer.encode(text))
    except Exception as e:
        logger.error(f"Error counting general model tokens: {str(e)}")
        return 0

