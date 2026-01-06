"""
Model router for intelligent AI model selection.

Analyzes tasks, selects optimal models, and manages fallback chains
for reliable AI operations.
"""

from typing import Any, Optional

from omnidev.core.config import ConfigManager
from omnidev.core.exceptions import ProviderError
from omnidev.core.logger import get_logger
from omnidev.models.base import BaseProvider, ProviderResponse
from omnidev.models.registry import ProviderRegistry
from omnidev.prompts.llm_helper import get_system_prompt_for_task


class TaskComplexity:
    """Represents task complexity analysis."""

    def __init__(
        self,
        score: float,
        task_type: str,
        context_size: str,
        reasoning_depth: str,
    ) -> None:
        """Initialize task complexity.

        Args:
            score: Complexity score (0-100).
            task_type: Type of task (code_gen, debug, explain, refactor, test).
            context_size: Required context size (small, medium, large).
            reasoning_depth: Required reasoning depth (surface, step-by-step, deep).
        """
        self.score = score
        self.task_type = task_type
        self.context_size = context_size
        self.reasoning_depth = reasoning_depth


class TaskAnalyzer:
    """Analyzes tasks to determine complexity and requirements."""

    # Task type keywords
    TASK_KEYWORDS = {
        "code_gen": ["create", "generate", "write", "build", "make", "add"],
        "debug": ["fix", "debug", "error", "bug", "issue", "problem"],
        "explain": ["explain", "describe", "how", "what", "why"],
        "refactor": ["refactor", "improve", "optimize", "clean", "restructure"],
        "test": ["test", "testing", "coverage", "spec"],
        "documentation": ["document", "doc", "comment", "readme"],
    }

    def analyze(self, query: str, context_size: int = 0) -> TaskComplexity:
        """Analyze a task query.

        Args:
            query: Task query or description.
            context_size: Size of available context in tokens.

        Returns:
            TaskComplexity analysis.
        """
        query_lower = query.lower()

        # Determine task type
        task_type = self._classify_task_type(query_lower)

        # Calculate complexity score
        complexity_score = self._calculate_complexity(query_lower, task_type)

        # Determine context size requirement
        context_size_req = self._determine_context_size(context_size)

        # Determine reasoning depth
        reasoning_depth = self._determine_reasoning_depth(complexity_score, task_type)

        return TaskComplexity(
            score=complexity_score,
            task_type=task_type,
            context_size=context_size_req,
            reasoning_depth=reasoning_depth,
        )

    def _classify_task_type(self, query: str) -> str:
        """Classify the type of task.

        Args:
            query: Lowercase query string.

        Returns:
            Task type string.
        """
        scores: dict[str, int] = {}
        for task_type, keywords in self.TASK_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in query)
            if score > 0:
                scores[task_type] = score

        if scores:
            return max(scores, key=scores.get)  # type: ignore
        return "code_gen"  # Default

    def _calculate_complexity(self, query: str, task_type: str) -> float:
        """Calculate complexity score (0-100).

        Args:
            query: Lowercase query string.
            task_type: Type of task.

        Returns:
            Complexity score.
        """
        base_scores = {
            "code_gen": 40.0,
            "debug": 60.0,
            "explain": 30.0,
            "refactor": 70.0,
            "test": 50.0,
            "documentation": 25.0,
        }

        base_score = base_scores.get(task_type, 40.0)

        # Adjust based on query length and keywords
        query_length_factor = min(len(query.split()) / 50.0, 1.0) * 20.0

        # Complexity indicators
        complexity_keywords = ["complex", "multiple", "all", "entire", "refactor", "migrate"]
        complexity_bonus = sum(10.0 for keyword in complexity_keywords if keyword in query)

        score = base_score + query_length_factor + complexity_bonus
        return min(score, 100.0)

    def _determine_context_size(self, available_tokens: int) -> str:
        """Determine required context size.

        Args:
            available_tokens: Available tokens in context.

        Returns:
            Context size category.
        """
        if available_tokens < 4000:
            return "small"
        elif available_tokens < 32000:
            return "medium"
        else:
            return "large"

    def _determine_reasoning_depth(self, complexity: float, task_type: str) -> str:
        """Determine required reasoning depth.

        Args:
            complexity: Complexity score.
            task_type: Type of task.

        Returns:
            Reasoning depth category.
        """
        if complexity > 80 or task_type in ("refactor", "debug"):
            return "deep"
        elif complexity > 50:
            return "step-by-step"
        else:
            return "surface"


class ModelRouter:
    """Routes requests to optimal AI models based on task analysis."""

    # Model suitability matrix
    MODEL_SUITABILITY = {
        "gpt-4o-mini": {
            "code_gen": 0.8,
            "debug": 0.7,
            "explain": 0.9,
            "refactor": 0.6,
            "test": 0.8,
            "documentation": 0.7,
        },
        "gpt-4o": {
            "code_gen": 0.95,
            "debug": 0.9,
            "explain": 0.95,
            "refactor": 0.85,
            "test": 0.9,
            "documentation": 0.9,
        },
        "gpt-4": {
            "code_gen": 0.9,
            "debug": 0.85,
            "explain": 0.9,
            "refactor": 0.8,
            "test": 0.85,
            "documentation": 0.85,
        },
        "claude-3-sonnet": {
            "code_gen": 0.9,
            "debug": 0.85,
            "explain": 0.95,
            "refactor": 0.95,
            "test": 0.85,
            "documentation": 0.95,
        },
        "claude-3-opus": {
            "code_gen": 0.95,
            "debug": 0.95,
            "explain": 0.95,
            "refactor": 0.98,
            "test": 0.9,
            "documentation": 0.98,
        },
        "deepseek-chat": {
            "code_gen": 0.85,
            "debug": 0.8,
            "explain": 0.8,
            "refactor": 0.75,
            "test": 0.8,
            "documentation": 0.75,
        },
    }

    def __init__(self, registry: ProviderRegistry, config: Optional[ConfigManager] = None) -> None:
        """Initialize the model router.

        Args:
            registry: Provider registry instance.
            config: Optional configuration manager.
        """
        self.registry = registry
        self.config = config
        self.logger = get_logger("router")
        self.analyzer = TaskAnalyzer()

    async def route_request(
        self,
        query: str,
        context_size: int = 0,
        preferred_model: Optional[str] = None,
        preferred_provider: Optional[str] = None,
    ) -> ProviderResponse:
        """Route a request to the optimal model.

        Args:
            query: User query or task description.
            context_size: Size of context in tokens.
            preferred_model: Optional preferred model name.
            preferred_provider: Optional preferred provider name.

        Returns:
            ProviderResponse from the selected model.

        Raises:
            ProviderError: If all providers fail.
        """
        # Analyze task
        complexity = self.analyzer.analyze(query, context_size)
        self.logger.debug(f"Task analysis: {complexity.task_type}, complexity={complexity.score:.1f}")

        # Select model
        selected_provider, selected_model = self._select_model(
            complexity,
            preferred_model,
            preferred_provider,
        )

        if not selected_provider:
            raise ProviderError("No available providers")

        # Get system prompt for task type
        system_prompt = get_system_prompt_for_task(complexity.task_type)
        
        # Use ONLY the selected provider - no fallback to other providers
        # This ensures user's choice is respected
        model_to_use = selected_model
        if not selected_provider.is_model_available(selected_model):
            # Try to find an equivalent model on this provider
            model_to_use = self._get_best_model_for_task(complexity, selected_provider)
            if not selected_provider.is_model_available(model_to_use):
                # Use first available model from provider
                available_models = selected_provider.list_models()
                if available_models:
                    model_to_use = available_models[0]
                else:
                    raise ProviderError(f"Provider {selected_provider.name} has no available models")

        self.logger.info(f"Using provider: {selected_provider.name}, model: {model_to_use}")
        
        try:
            # Include system prompt in generation
            response = await selected_provider.generate(
                prompt=query,
                model=model_to_use,
                system_prompt=system_prompt,
            )
            return response
        except Exception as e:
            # No fallback - fail immediately with clear error
            self.logger.error(f"Provider {selected_provider.name} failed: {e}")
            raise ProviderError(f"Provider {selected_provider.name} failed: {e}") from e

    def _select_model(
        self,
        complexity: TaskComplexity,
        preferred_model: Optional[str],
        preferred_provider: Optional[str],
    ) -> tuple[Optional[BaseProvider], str]:
        """Select the best model for a task.

        Args:
            complexity: Task complexity analysis.
            preferred_model: Optional preferred model.
            preferred_provider: Optional preferred provider.

        Returns:
            Tuple of (provider, model_name).
        """
        # If user specified a preference, try to use it
        if preferred_provider:
            provider = self.registry.get_provider(preferred_provider)
            if provider and provider.check_health():
                model = preferred_model or self._get_best_model_for_task(complexity, provider)
                return provider, model

        # Use the highest priority provider and find the best model it supports
        for provider_name in self.registry.provider_priority:
            provider = self.registry.get_provider(provider_name)
            if provider and provider.check_health():
                # Get the best model for this provider
                if preferred_model and provider.is_model_available(preferred_model):
                    return provider, preferred_model
                
                # Get best model this provider supports
                best_model = self._get_best_model_for_task(complexity, provider)
                if provider.is_model_available(best_model):
                    return provider, best_model
                
                # If no best model found, use first available from provider
                available_models = provider.list_models()
                if available_models:
                    return provider, available_models[0]

        # Fallback: find any provider for the best model
        best_model = self._get_best_model_for_task(complexity)
        best_provider = self._find_provider_for_model(best_model)

        return best_provider, best_model

    def _get_best_model_for_task(
        self,
        complexity: TaskComplexity,
        provider: Optional[BaseProvider] = None,
    ) -> str:
        """Get the best model for a task type.

        Args:
            complexity: Task complexity analysis.
            provider: Optional specific provider to use.

        Returns:
            Model name.
        """
        task_type = complexity.task_type

        # Score available models
        model_scores: dict[str, float] = {}

        if provider:
            # Score models from this provider
            for model in provider.list_models():
                if model in self.MODEL_SUITABILITY:
                    suitability = self.MODEL_SUITABILITY[model].get(task_type, 0.5)
                    # Adjust for complexity
                    if complexity.score > 70:
                        suitability *= 1.1  # Prefer better models for complex tasks
                    model_scores[model] = suitability
        else:
            # Score all available models
            for model, suitabilities in self.MODEL_SUITABILITY.items():
                suitability = suitabilities.get(task_type, 0.5)
                if complexity.score > 70:
                    suitability *= 1.1
                model_scores[model] = suitability

        if not model_scores:
            # Default fallback
            return "gpt-4o"

        # Return best scoring model
        return max(model_scores, key=model_scores.get)  # type: ignore

    def _find_provider_for_model(self, model: str) -> Optional[BaseProvider]:
        """Find a provider that supports a model.

        Uses providers in priority order.

        Args:
            model: Model name.

        Returns:
            Provider instance if found, None otherwise.
        """
        # Use priority order, not arbitrary order
        for provider_name in self.registry.provider_priority:
            provider = self.registry.get_provider(provider_name)
            if provider and provider.is_model_available(model) and provider.check_health():
                return provider
        return None

