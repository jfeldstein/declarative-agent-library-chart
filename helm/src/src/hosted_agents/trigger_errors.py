"""HTTP-oriented errors raised inside the trigger pipeline."""


class TriggerHttpError(Exception):
    """Maps to a non-200 HTTP response from the FastAPI layer."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)
