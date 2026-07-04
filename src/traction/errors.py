"""Domain errors with stable exit semantics."""

class TractionError(RuntimeError):
    """Expected user-actionable protocol failure."""


class ValidationError(TractionError):
    """An artifact does not satisfy its machine-readable contract."""


class StateError(TractionError):
    """The requested transition is illegal for the current state."""


class IntegrityError(TractionError):
    """A locked artifact, receipt, or ledger no longer matches its hash."""
