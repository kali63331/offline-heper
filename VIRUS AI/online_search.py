
import re
import requests
from html import unescape
from ddgs import DDGS


def search_wikipedia(query, max_results=5):
    try:
        headers = {
            "User-Agent": "VIRUS-AI/1.0"
        }

        response = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "list": "search",
                "srsearch": query,
                "srlimit": max_results,
                "format": "json"
            },
            headers=headers,
            timeout=15
        )

        response.raise_for_status()
        results = response.json()["query"]["search"]

        search_results = []

        for result in results:
            title = result["title"]

            extract_response = requests.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "prop": "extracts",
                    "exintro": True,
                    "explaintext": True,
                    "exchars": 1500,
                    "titles": title,
                    "format": "json"
                },
                headers=headers,
                timeout=15
            )

            extract_response.raise_for_status()
            pages = extract_response.json()["query"]["pages"]

            page = next(iter(pages.values()))
            snippet = page.get("extract", "")

            search_results.append({
                "title": title,
                "url": "https://en.wikipedia.org/wiki/" + title.replace(" ", "_"),
                "snippet": snippet
            })

        return search_results

    except Exception as error:
        print("Wikipedia search error:", error)
        return []


def search_web(query, max_results=5):
    for backend in ["auto", "html", "lite"]:
        try:
            print("Searching using DDGS:", backend)

            results = DDGS().text(
                query,
                max_results=max_results,
                backend=backend
            )

            search_results = []
            seen_urls = set()

            for result in results:
                url = result.get("href", "").strip()

                if url and url not in seen_urls:
                    seen_urls.add(url)

                    search_results.append({
                        "title": result.get("title", ""),
                        "url": url,
                        "snippet": result.get("body", "")
                    })

            if search_results:
                return search_results[:max_results]

        except Exception as error:
            print("DDGS search failed:", error)

    print("DDGS unavailable. Trying Wikipedia...")
    return search_wikipedia(query, max_results)

def internet_available():
    try:
        response = requests.get(
            "https://www.google.com",
            timeout=5
        )
        return response.status_code == 200
    except requests.RequestException:
        return False
