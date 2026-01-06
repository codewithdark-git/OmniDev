"""
Helper functions for loading LLM system prompts.
"""

from typing import Optional

from omnidev.prompts.loader import PromptLoader

_prompt_loader: Optional[PromptLoader] = None


def get_prompt_loader() -> PromptLoader:
    """Get or create prompt loader instance.
    
    Returns:
        PromptLoader instance.
    """
    global _prompt_loader
    if _prompt_loader is None:
        _prompt_loader = PromptLoader()
    return _prompt_loader


def get_code_generation_prompt() -> str:
    """Get system prompt for code generation.
    
    Returns:
        Code generation system prompt.
    """
    loader = get_prompt_loader()
    return loader.load("llm", "code_generation")


def get_code_review_prompt() -> str:
    """Get system prompt for code review.
    
    Returns:
        Code review system prompt.
    """
    loader = get_prompt_loader()
    return loader.load("llm", "code_review")


def get_error_handling_prompt() -> str:
    """Get system prompt for error handling.
    
    Returns:
        Error handling system prompt.
    """
    loader = get_prompt_loader()
    return loader.load("llm", "error_handling")


def get_refactoring_prompt() -> str:
    """Get system prompt for refactoring.
    
    Returns:
        Refactoring system prompt.
    """
    loader = get_prompt_loader()
    return loader.load("llm", "refactoring")


def get_testing_prompt() -> str:
    """Get system prompt for testing.
    
    Returns:
        Testing system prompt.
    """
    loader = get_prompt_loader()
    return loader.load("llm", "testing")


def get_documentation_prompt() -> str:
    """Get system prompt for documentation.
    
    Returns:
        Documentation system prompt.
    """
    loader = get_prompt_loader()
    return loader.load("llm", "documentation")


def get_system_prompt_for_task(task_type: str) -> str:
    """Get appropriate system prompt for task type.
    
    Args:
        task_type: Type of task (code_gen, review, error_handling, etc.).
        
    Returns:
        System prompt for the task type.
    """
    prompt_map = {
        "code_gen": get_code_generation_prompt,
        "code_generation": get_code_generation_prompt,
        "review": get_code_review_prompt,
        "code_review": get_code_review_prompt,
        "error_handling": get_error_handling_prompt,
        "refactoring": get_refactoring_prompt,
        "refactor": get_refactoring_prompt,
        "testing": get_testing_prompt,
        "test": get_testing_prompt,
        "documentation": get_documentation_prompt,
        "docs": get_documentation_prompt,
    }
    
    getter = prompt_map.get(task_type.lower(), get_code_generation_prompt)
    return getter()

