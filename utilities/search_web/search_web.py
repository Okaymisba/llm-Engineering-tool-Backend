import os

import httpx
from dotenv import load_dotenv

load_dotenv()

BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")
BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"


async def search_web(query: str, count: int = 10) -> list[dict]:
    """
    Perform a web search using the Brave Search API.

    This function sends an asynchronous GET request to the Brave Search API
    with the specified search query and the number of results to retrieve.
    It processes the response data to extract and return relevant search
    results in a structured format. Each result includes the title, URL, and
    a snippet of the associated content.

    :param query: The search query string to be used for the web search.
    :type query: str
    :param count: The maximum number of search results to retrieve. Defaults
        to 10.
    :type count: int
    :return: A list of dictionaries containing the search results. Each
        dictionary has the keys "title", "url", and "snippet".
    :rtype: list[dict]
    """
    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": BRAVE_API_KEY
    }
    params = {
        "q": query,
        "count": count
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(BRAVE_SEARCH_URL, headers=headers, params=params)

        response.raise_for_status()

        data = response.json()
        return [
            {
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "snippet": result.get("description", "")
            }
            for result in data.get("web", {}).get("results", [])
        ]
