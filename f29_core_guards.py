from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


def ensure_non_empty(value: str, field_name: str) -> str:
    clean = (value or "").strip()
    if not clean:
        raise ValueError(f"{field_name} cannot be empty")
    return clean


def validate_model(data: dict[str, Any], model_cls: type[T]) -> T:
    try:
        return model_cls.model_validate(data)
    except ValidationError as exc:
        raise ValueError(exc.json()) from exc