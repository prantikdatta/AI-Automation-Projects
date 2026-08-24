class JobAutomationException(Exception):
    """Base exception for the application."""


class ConfigurationError(JobAutomationException):
    """Raised when configuration is invalid."""


class ProviderError(JobAutomationException):
    """Raised when a provider fails."""


class GoogleSheetsError(JobAutomationException):
    """Raised when Google Sheets operations fail."""


class GeminiError(JobAutomationException):
    """Raised when Gemini operations fail."""