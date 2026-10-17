from pydantic import BaseModel


class FieldError(BaseModel):
    field: str
    message: str


class ApiError(BaseModel):
    """Error body returned by the API.

    ``code`` is stable and meant for branching; ``message`` is for humans and
    may be reworded or localised at any time (#1164).
    """

    code: str
    message: str
    errors: list[FieldError] | None = None
    field: str | None = None
