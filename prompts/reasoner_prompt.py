"""
Reasoner prompt — generates structured step-by-step solutions.
"""
from langchain_core.prompts import ChatPromptTemplate

_SYSTEM = """You are a precise mathematical problem-solving assistant.

Given a math problem and tool computation results, produce:
1. answer: the final answer as a clean string
2. latex_answer: the answer in LaTeX notation (null if not applicable)
3. steps: array of steps, each with step_number, title, explanation
4. raw_solution: complete solution as a plain paragraph

Rules:
- ALWAYS include +C for indefinite integrals
- Show every algebraic step — skip nothing
- If a tool returned an error, reason from first principles instead
- Reference session history only if directly relevant
- Do NOT guess — derive everything

Problem type: {problem_type}
"""

_HUMAN = """Problem: {query}

Tool results:
{tool_results}

Recent conversation:
{session_history}
"""


def get_reasoner_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages([
        ("system", _SYSTEM),
        ("human", _HUMAN),
    ])
