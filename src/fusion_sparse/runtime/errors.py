"""Runtime error hierarchy."""


class FusionSparseError(Exception):
    """Base class for FusionSparse runtime errors."""


class InvalidContextError(FusionSparseError):
    """Raised when the current Fusion context is incompatible with an operation."""


class UnitCoercionError(FusionSparseError):
    """Raised when a value cannot be coerced safely into a Fusion unit input."""


class UnsupportedOperationError(FusionSparseError):
    """Raised when a requested compact operation is not supported."""


class GenerationMismatchError(FusionSparseError):
    """Raised when generated metadata is incompatible with the runtime."""

