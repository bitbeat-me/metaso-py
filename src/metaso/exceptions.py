"""Exception hierarchy for the Metaso client."""


class MetasoError(Exception):
    """Base exception for all metaso errors."""


class AuthError(MetasoError):
    """Authentication failed or expired."""


class BackendError(MetasoError):
    """Backend does not support this operation."""


class NetworkError(MetasoError):
    """Network connectivity issue."""


class RateLimitError(MetasoError):
    """Rate limit exceeded."""


class ServerError(MetasoError):
    """Server returned 5xx."""


class NotFoundError(MetasoError):
    """Resource not found."""


class ValidationError(MetasoError):
    """Invalid parameters."""
