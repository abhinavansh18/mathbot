"""
Wikipedia Tool — for conceptual math questions that need background knowledge.
"""
from langchain_community.utilities import WikipediaAPIWrapper

from core.logging import get_logger

log = get_logger(__name__)

_wrapper = WikipediaAPIWrapper(top_k_results=2, doc_content_chars_max=1500)


async def run_wikipedia(query: str) -> str:
    """
    Searches Wikipedia for math concept background.
    The result is used by the reasoner for context, not as a final answer.
    """
    try:
        result = _wrapper.run(query)
        log.info("tool.wikipedia.success", query=query[:60])
        return result
    except Exception as exc:
        log.warning("tool.wikipedia.failed", error=str(exc))
        return f"Wikipedia search failed: {exc}"
