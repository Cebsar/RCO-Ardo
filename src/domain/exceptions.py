class DomainError(Exception):
    """Base class for domain-specific errors."""


class EntityNotFound(DomainError):
    """Raised when an entity cannot be found in a repository."""


class DuplicateEntityError(DomainError):
    """Raised when attempting to create an entity that already exists."""


class InvalidDomainError(DomainError):
    """Raised when domain invariants are violated."""
