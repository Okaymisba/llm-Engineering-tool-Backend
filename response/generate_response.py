import logging

from models import get_db
from models.api_list import APIList
from models.user import User
from prompt_generation.prompt_generation import generate_prompt
from prompt_generation.query_local_model import query_local_model
from response.anthropic.query_anthropic_model import query_anthropic_model
from response.deepseek.query_deepseek_model import query_deepseek_model
from response.google.query_google_model import query_google_model
from response.openai.query_openai_model import query_openai_model
from utilities.count_tokens import count_gemini_tokens
from utilities.count_tokens import count_tokens

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def generate_response(
        provider: str,
        model: str,
        question: str,
        prompt_context: list = None,
        instructions: str = None,
        image_data: list = None,
        document_data: list = None,
        api_key: str = None,
        user_id: int = None,
        stream: bool = True
):
    """
    Generates a response from the specified provider's model based on the given parameters.
    The function dynamically selects the appropriate model and handles token counting and
    database updates for usage statistics. Supports streaming responses for Google models
    and integrates token management for users or API keys.

    :param provider: The provider name for the model to be queried.
                     Accepted values include "deepseek", "openai", "anthropic", "google",
                     or custom local model configurations.
                     Example: 'openai'.
    :type provider: str
    :param model: The specific model identifier of the provider to be queried.
                  Example: 'gpt-4'.
    :type model: str
    :param question: The main query or input text to be answered or processed
                     by the model.
    :type question: str
    :param prompt_context: A list of additional contextual information to refine
                           the query, if needed. Default is None.
    :type prompt_context: list, optional
    :param instructions: Specific instructions or guidelines passed to tailor
                         the model's response. Default is None.
    :type instructions: str, optional
    :param image_data: A list of image data to accompany the query for models
                       supporting multi-modal inputs. Default is None.
    :type image_data: list, optional
    :param document_data: A list of document data to accompany the query for models
                          supporting document processing. Default is None.
    :type document_data: list, optional
    :param api_key: The API key authorized for querying the provider and tracking
                    token usage. Optional but required if user-related token management
                    is bypassed. Default is None.
    :type api_key: str, optional
    :param user_id: The unique identifier for a user being tracked for token usage.
                    Default is None.
    :type user_id: int, optional
    :param stream: Specifies if the response should be streamed progressively for
                   models that support streaming (e.g., Google).
                   Default value is True.
    :type stream: bool, optional
    :return: Generates and yields response text (in chunks during streaming) or a
             complete final response from the queried model. The streaming response
             functionality applies only for "google" provider.
    :rtype: tuple(str, dict) - Response text and metadata (tokens, status)
    """
    try:
        response = ""
        input_tokens = 0
        output_tokens = 0
        status_code = 200  # Default success status

        # Calculate input tokens first
        if provider == "google":
            input_tokens = count_gemini_tokens(question, model)
            if prompt_context:
                for context in prompt_context:
                    input_tokens += count_gemini_tokens(context, model)
        elif provider == "openai":
            # OpenAI calculates tokens internally
            pass
        else:
            input_tokens = count_tokens(question, model)
            if prompt_context:
                for context in prompt_context:
                    input_tokens += count_tokens(context, model)

        if provider == "deepseek":
            response = query_deepseek_model(model, question, prompt_context, instructions, image_data, document_data)
            output_tokens = count_tokens(response, model)
            yield response, {"input_tokens": input_tokens, "output_tokens": output_tokens, "status_code": status_code}
        elif provider == "openai":
            response, total_tokens_used = query_openai_model(model, question, prompt_context, instructions, image_data,
                                                             document_data)
            input_tokens = total_tokens_used // 2
            output_tokens = total_tokens_used - input_tokens
            yield response, {"input_tokens": input_tokens, "output_tokens": output_tokens, "status_code": status_code}
        elif provider == "anthropic":
            response = query_anthropic_model(model, question, prompt_context, instructions, image_data, document_data)
            output_tokens = count_tokens(response, model)
            yield response, {"input_tokens": input_tokens, "output_tokens": output_tokens, "status_code": status_code}
        elif provider == "google":
            if stream:
                response = ""
                async for chunk in query_google_model(model, question, prompt_context, instructions, image_data,
                                                      document_data, stream=True):
                    response += chunk
                    # Calculate output tokens for the accumulated response
                    output_tokens = count_gemini_tokens(response, model)
                    yield chunk, {"input_tokens": input_tokens, "output_tokens": output_tokens, "status_code": status_code}
            else:
                response = await query_google_model(model, question, prompt_context, instructions, image_data,
                                                    document_data)
                output_tokens = count_gemini_tokens(response, model)
                yield response, {"input_tokens": input_tokens, "output_tokens": output_tokens, "status_code": status_code}
        else:
            response = query_local_model(
                generate_prompt(question, prompt_context, instructions, image_data, document_data))
            output_tokens = count_tokens(response, model)
            yield response, {"input_tokens": input_tokens, "output_tokens": output_tokens, "status_code": status_code}

        total_tokens_used = input_tokens + output_tokens

        db = next(get_db())
        try:
            if api_key:
                api_entry = APIList.get_by_api_key(db, api_key)
                if api_entry:
                    api_entry.tokens_used += total_tokens_used
                    api_entry.tokens_remaining = api_entry.total_tokens - api_entry.tokens_used
                    db.commit()
                    logger.info(f"Updated token usage for API key {api_key}: {total_tokens_used} tokens used")
            elif user_id:
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    user.tokens_used += total_tokens_used
                    user.tokens_remaining = user.total_tokens - user.tokens_used
                    db.commit()
                    logger.info(f"Updated token usage for user {user_id}: {total_tokens_used} tokens used")
        except Exception as e:
            logger.error(f"Error updating token usage in database: {str(e)}")
            status_code = 500
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error in generate_response: {str(e)}")
        status_code = 500
        yield f"Error: {str(e)}", {"input_tokens": 0, "output_tokens": 0, "status_code": status_code}
        raise
