import requests


def query_local_model(prompt: str):
    """
    Send a prompt to a local AI model API hosted at http://127.0.0.1:1234/v1/chat/completions
    and retrieve the model's response.

    :param prompt: The input prompt to send to the local AI model.
    :type prompt: str
    :return: The response content from the AI model if successful, `None` if the API
        response is not successful, or an exception message if an error occurs during
        the request.
    :rtype: str or None
    """

    url = "http://127.0.0.1:1234/v1/chat/completions"
    headers = {"Content-Type": "application/json"}

    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 250
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json().get("choices", [{}])[0].get("message", {}).get("content", "No content returned.")
        return None
    except Exception as e:
        return f"Exception: {e}"
