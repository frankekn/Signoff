"""Domain errors with stable exit semantics."""

class SignoffError(RuntimeError):
    """Expected user-actionable protocol failure."""


class ValidationError(SignoffError):
    """An artifact does not satisfy its machine-readable contract."""


class StateError(SignoffError):
    """The requested transition is illegal for the current state."""


class IntegrityError(SignoffError):
    """A locked artifact, receipt, or ledger no longer matches its hash."""
