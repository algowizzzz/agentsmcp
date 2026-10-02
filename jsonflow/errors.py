"""Exception types shared across the engine."""


class JsonFlowError(Exception):
    """Base class for all engine errors."""


class SpecError(JsonFlowError):
    """The workflow document is invalid."""


class ExpressionError(JsonFlowError):
    """A template expression could not be resolved."""


class ToolError(JsonFlowError):
    """An MCP tool call failed or returned an error payload."""


class LLMError(JsonFlowError):
    """An LLM call failed or returned output that does not match its schema."""


class BudgetExceeded(JsonFlowError):
    """A run tried to exceed its tool-call or LLM-call budget."""
