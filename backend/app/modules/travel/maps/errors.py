"""Maps failures. `code` values match the AI/Wordnik adapters so the client handles vendor errors uniformly."""


class MapsError(Exception):
    code: str = "provider_unavailable"


class MapsNotConfigured(MapsError):
    code = "missing_credential"


class MapsInvalidCredential(MapsError):
    code = "invalid_credential"


class MapsRateLimited(MapsError):
    code = "rate_limit"


class MapsTimeout(MapsError):
    code = "timeout"


class MapsUnavailable(MapsError):
    code = "provider_unavailable"


class MapsBlocked(MapsError):
    """Cost protection refused the call before it reached the provider."""

    code = "cost_protection"

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason
