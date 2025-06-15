import os

import httpx
from dotenv import load_dotenv

load_dotenv()

BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")
BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"


async def search_web(query: str, count: int = 5) -> list[dict]:
    """
    Executes a web search query using the Brave Search API and retrieves the results as a
    list of dictionaries containing title, URL, and snippet for each result.

    :param query: The search query string used to look for relevant resources.
    :type query: str
    :param count: The number of search results to retrieve, defaults to 5.
    :type count: int
    :return: A list of dictionaries representing the search results, where each dictionary contains a
             title, URL, and snippet of the result.
    :rtype: list[dict]
    :raises httpx.HTTPStatusError: If the HTTP response contains a status code indicating an error.
    :raises httpx.RequestError: If an error occurred while making the request (e.g., network issue).
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
                "snippet": result.get("description", ""),
            }
            for result in data.get("web", {}).get("results", [])
        ]
