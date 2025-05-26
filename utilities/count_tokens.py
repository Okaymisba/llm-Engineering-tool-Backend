import tiktoken
from transformers import AutoTokenizer
from anthropic import Anthropic
from typing import Optional, Union
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_openai_encoding(model: str) -> tiktoken.Encoding:
    """
    Get the appropriate encoding for OpenAI models.

    Args:
        model (str): The model name (e.g., "gpt-4", "gpt-3.5-turbo")

    Returns:
        tiktoken.Encoding: The encoding object for the specified model
    """
    try:
        return tiktoken.encoding_for_model(model_name=model)
    except KeyError:
        logger.warning(f"Model {model} not found, using cl100k_base encoding")
        return tiktoken.encoding_for_model("cl100k_base")

def count_openai_models_tokens(text: str, model: str = "gpt-4") -> int:
    """
    Counts the number of tokens in a given text for OpenAI models.

    Args:
        text (str): The input text (prompt or response)
        model (str): The model name (e.g., "gpt-4", "gpt-3.5-turbo")

    Returns:
        int: Number of tokens in the input text
    """
    try:
        encoding = get_openai_encoding(model)
        return len(encoding.encode(text))
    except Exception as e:
        logger.error(f"Error counting OpenAI tokens: {str(e)}")
        return 0

def count_claude_models_tokens(text: str, model: str) -> int:
    """
    Counts the number of tokens in a given text for Claude models.

    Args:
        text (str): The input text (prompt or response)
        model (str): The model name (e.g., "claude-3-5-sonnet-latest")

    Returns:
        int: Number of tokens in the input text
    """
    try:
        client = Anthropic()
        return client.count_tokens(text)
    except Exception as e:
        logger.error(f"Error counting Claude tokens: {str(e)}")
        return 0

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

def count_general_models_tokens(text: str, model: str = "deepseek") -> int:
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

def count_tokens(text: str, provider: str, model: str) -> int:
    """
    Unified function to count tokens based on provider and model.

    Args:
        text (str): The input text to count tokens for
        provider (str): The provider name ("openai", "anthropic", or other)
        model (str): The specific model name

    Returns:
        int: Number of tokens in the input text
    """
    try:
        if provider == "openai":
            return count_openai_models_tokens(text, model)
        elif provider == "anthropic":
            return count_claude_models_tokens(text, model)
        else:
            return count_general_models_tokens(text, model)
    except Exception as e:
        logger.error(f"Error in count_tokens: {str(e)}")
        return 0