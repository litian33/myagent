import inspect
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from typing import Any, ParamSpec, TypeVar, get_type_hints

import openai
from openai.types.responses import FunctionToolParam

from agent.errors import ModelInvocationError
from policy.model import (
    ToolCapability,
)

ToolHandler = Callable[..., Any]

F = TypeVar(
    "F",
    bound=ToolHandler,
)

P = ParamSpec("P")
R = TypeVar("R")


def handle_openai_errors(func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return func(*args, **kwargs)
        except (
            openai.APIConnectionError,
            openai.APITimeoutError,
            openai.RateLimitError,
            openai.InternalServerError,
        ) as exc:
            raise ModelInvocationError(
                str(exc),
                retryable=True,
            ) from exc
        except openai.APIError as exc:
            raise ModelInvocationError(
                str(exc),
                retryable=False,
            ) from exc

    return wrapper


@dataclass(
    frozen=True,
    slots=True,
)
class Tool:
    schema: FunctionToolParam
    handler: ToolHandler
    capability: ToolCapability

    @property
    def name(self) -> str:
        return self.schema["name"]

    def __call__(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        return self.handler(
            *args,
            **kwargs,
        )


def python_type_to_json_schema(
    annotation: Any,
) -> dict[str, Any]:
    type_mapping: dict[Any, str] = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
    }

    json_type = type_mapping.get(annotation)

    if json_type is None:
        raise TypeError(f"Unsupported tool parameter type: {annotation!r}")

    return {
        "type": json_type,
    }


def build_parameters_schema(
    handler: ToolHandler,
) -> dict[str, Any]:
    signature = inspect.signature(handler)
    type_hints = get_type_hints(handler)

    properties: dict[str, Any] = {}
    required: list[str] = []

    for name, parameter in signature.parameters.items():
        if parameter.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            raise TypeError(
                f"Tool functions cannot use *args or **kwargs: {handler.__name__}"
            )

        if parameter.default is not inspect.Parameter.empty:
            raise TypeError(
                "Default tool parameters are not supported yet: "
                f"{handler.__name__}.{name}"
            )

        annotation = type_hints.get(name)

        if annotation is None:
            raise TypeError(
                f"Tool parameter must have a type annotation: {handler.__name__}.{name}"
            )

        properties[name] = python_type_to_json_schema(annotation)

        required.append(name)

    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


def tool(
    *,
    description: str,
    capability: ToolCapability,
) -> Callable[[F], Tool]:
    def decorator(
        handler: F,
    ) -> Tool:
        schema: FunctionToolParam = {
            "type": "function",
            "name": handler.__name__,
            "description": description,
            "parameters": (build_parameters_schema(handler)),
            "strict": True,
        }

        return Tool(
            schema=schema,
            handler=handler,
            capability=capability,
        )

    return decorator
