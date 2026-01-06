"""
Prompt management system for OmniDev.

Provides system prompts for agents and LLMs to ensure consistent,
high-quality code generation and agent behavior.
"""

from omnidev.prompts.loader import PromptLoader
from omnidev.prompts.llm_helper import (
    get_code_generation_prompt,
    get_code_review_prompt,
    get_documentation_prompt,
    get_error_handling_prompt,
    get_refactoring_prompt,
    get_system_prompt_for_task,
    get_testing_prompt,
)

__all__ = [
    "PromptLoader",
    "get_code_generation_prompt",
    "get_code_review_prompt",
    "get_documentation_prompt",
    "get_error_handling_prompt",
    "get_refactoring_prompt",
    "get_system_prompt_for_task",
    "get_testing_prompt",
]

