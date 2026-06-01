from tools.tool_registry import tool

@tool(description="Simple search placeholder. Arguments: query (str)")
def simple_search(query):

    return f"Search placeholder for {query}"
