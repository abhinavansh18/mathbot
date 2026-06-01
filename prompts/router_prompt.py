"""
Router prompt — classifies the problem type and selects tools.
"""
from langchain_core.prompts import ChatPromptTemplate


_SYSTEM = """You are a math problem classifier.

Given a math problem, return:
1. problem_type: one of arithmetic | symbolic | conceptual | mixed | unknown
2. selected_tools: list from [calculator, sympy, wikipedia]
3. reasoning: one sentence explaining your choice

Rules:
- arithmetic: plain number problems → ["calculator"]
- symbolic: integrals, derivatives, equations, limits → ["sympy"]
- conceptual: theory questions → ["wikipedia"]
- mixed: requires multiple tools → combine as needed
- When unsure, prefer sympy over calculator
"""

_HUMAN = "Problem: {query}"


def get_router_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages([
        ("system", _SYSTEM),
        ("human", _HUMAN),
    ])
