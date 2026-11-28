from mcp.server.fastmcp import FastMCP

mcp = FastMCP("text-tools")

@mcp.tool()
def reverse_text(text: str) -> str:
    """Reverse the characters in the supplied text."""
    return text[::-1]

if __name__ == "__main__":
    mcp.run()
