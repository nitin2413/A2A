class UnknownAgentError(Exception):
    """Raised when a task references an agent that does not exist."""
    pass


class PlanGraphError(Exception):
    """Raised when a plan contains an invalid dependency graph."""
    pass
