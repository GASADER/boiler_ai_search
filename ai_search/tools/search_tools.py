# -*- coding: utf-8 -*-
from crewai.tools import tool
from ddgs import DDGS

@tool("DuckDuckGo Search")
def web_search_tool(query: str) -> str:
    """Search information from the internet using English keywords."""
    try:
        results = list(DDGS().text(query=query, max_results=5))
        if not results:
            return "No results found."
        return "\n---\n".join([f"Title: {r['title']}\nSnippet: {r['body']}" for r in results])
    except Exception as e:
        return f"Error: {str(e)}"