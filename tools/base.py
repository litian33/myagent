import inspect
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar, get_type_hints

from openai.types.responses import FunctionToolParam

ToolHandler = Callable[..., Any]

F = TypeVar(
    "F",
    bound=ToolHandler,
)


@dataclass(frozen=True, slots=True)
class Tool:
    schema: FunctionToolParam
    handler: ToolHandler

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
        raise TypeError(
            "Unsupported tool parameter type: "
            f"{annotation!r}"
        )

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
                "Tool functions cannot use *args or **kwargs: "
                f"{handler.__name__}"
            )

        if parameter.default is not inspect.Parameter.empty:
            raise TypeError(
                "Default tool parameters are not supported yet: "
                f"{handler.__name__}.{name}"
            )

        annotation = type_hints.get(name)

        if annotation is None:
            raise TypeError(
                "Tool parameter must have a type annotation: "
                f"{handler.__name__}.{name}"
            )

        properties[name] = (
            python_type_to_json_schema(annotation)
        )

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
) -> Callable[[F], Tool]:
    def decorator(
        handler: F,
    ) -> Tool:
        schema: FunctionToolParam = {
            "type": "function",
            "name": handler.__name__,
            "description": description,
            "parameters": build_parameters_schema(
                handler
            ),
            "strict": True,
        }

        return Tool(
            schema=schema,
            handler=handler,
        )

    return decorator
