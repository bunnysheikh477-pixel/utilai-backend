from typing import Any, Optional


class AppException(Exception):
    def __init__(self, message: str, error_code: str = "APP_ERROR", status_code: int = 400, details: Any = None):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details
        super().__init__(message)
