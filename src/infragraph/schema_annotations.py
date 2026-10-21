"""Schema based annotations: schema compilation, document validation,
JSON Pointer resolution and JSONPath evaluation."""

import json
import math
from functools import lru_cache
from typing import Any, Callable, Dict, Optional

import re2
from iregexp_check import check
from jsonpath_rfc9535 import JSONPathEnvironment
from ruamel.yaml import YAML

try:
    # jsonpath-rfc9535 2.x, which requires Python 3.12
    from jsonpath_rfc9535 import functions as _jsonpath_functions

    _FUNCTION_REGISTRY = "functions"
except ImportError:
    # jsonpath-rfc9535 1.x, the last release for Python before 3.12
    from jsonpath_rfc9535 import function_extensions as _jsonpath_functions

    _FUNCTION_REGISTRY = "function_extensions"

_MatchBase = _jsonpath_functions.Match
_SearchBase = _jsonpath_functions.Search

MAX_DEFINITION_BYTES = 32 * 1024 * 1024
MAX_DOCUMENT_BYTES = 1024 * 1024
MAX_DOCUMENT_NODES = 200_000


class SchemaAnnotationError(ValueError):
    """Raised when a schema, document, reference or schema filter is invalid."""


def _map_dot(pattern: str) -> str:
    """Map an I-Regexp pattern to RE2, where . excludes \\n and \\r."""
    escaped = False
    in_class = False
    parts = []
    for ch in pattern:
        if escaped:
            escaped = False
        elif ch == "\\":
            escaped = True
        elif ch == "[":
            in_class = True
        elif ch == "]":
            in_class = False
        elif ch == "." and not in_class:
            parts.append("[^\\n\\r]")
            continue
        parts.append(ch)
    return "".join(parts)


@lru_cache(maxsize=1024)
def _compile_re2(pattern: str) -> Optional[Any]:
    """Compile an I-Regexp pattern with RE2, None if it is invalid."""
    try:
        if not check(pattern):
            return None
        return re2.compile(_map_dot(pattern))
    except Exception:
        return None


class _Re2Mixin:
    """Evaluates the pattern of match() and search() with RE2."""

    def __call__(self, string: object, pattern: object) -> bool:
        if not isinstance(pattern, str) or not isinstance(string, str):
            return False
        compiled = _compile_re2(pattern)
        if compiled is None:
            return False
        return self.go(compiled, string)


class _Re2Match(_Re2Mixin, _MatchBase):
    def go(self, pattern, string: str) -> bool:
        return pattern.fullmatch(string) is not None


class _Re2Search(_Re2Mixin, _SearchBase):
    def go(self, pattern, string: str) -> bool:
        return pattern.search(string) is not None


def _jsonpath_environment() -> JSONPathEnvironment:
    env = JSONPathEnvironment()
    registry = getattr(env, _FUNCTION_REGISTRY)
    registry["match"] = _Re2Match()
    registry["search"] = _Re2Search()
    return env


_JSONPATH = _jsonpath_environment()


def decode_text(text: str, what: str, max_bytes: int) -> Any:
    """Decode JSON or YAML text containing only JSON data types."""
    if len(text.encode("utf-8")) > max_bytes:
        raise SchemaAnnotationError(f"{what} exceeds {max_bytes} bytes")
    try:
        data = YAML(typ="safe", pure=True).load(text)
    except Exception as e:
        raise SchemaAnnotationError(f"{what} does not decode as JSON or YAML: {e}")
    _check_json_types(data, what)
    return data


def _check_json_types(data: Any, what: str) -> None:
    """Reject non JSON types and bound the size, aliases included."""
    count = 0
    stack = [data]
    while stack:
        item = stack.pop()
        count += 1
        if count > MAX_DOCUMENT_NODES:
            raise SchemaAnnotationError(f"{what} exceeds {MAX_DOCUMENT_NODES} values")
        if isinstance(item, dict):
            for key, value in item.items():
                if not isinstance(key, str):
                    raise SchemaAnnotationError(f"{what} has a non string key {key!r}")
                stack.append(value)
        elif isinstance(item, list):
            stack.extend(item)
        elif isinstance(item, float):
            if not math.isfinite(item):
                raise SchemaAnnotationError(f"{what} has a non finite number")
        elif not (item is None or isinstance(item, (str, bool, int))):
            raise SchemaAnnotationError(f"{what} has a value that is not JSON: {type(item).__name__}")


def canonical_json(data: Any) -> str:
    """Canonical JSON text with sorted keys and no whitespace."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def resolve_pointer(document: Any, pointer: Optional[str]) -> Any:
    """Resolve an RFC 6901 JSON Pointer, an empty pointer is the document."""
    if not pointer:
        return document
    if not pointer.startswith("/"):
        raise SchemaAnnotationError(f"pointer {pointer!r} does not start with /")
    current = document
    for token in pointer[1:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict) and token in current:
            current = current[token]
        elif (
            isinstance(current, list)
            and token.isascii()
            and token.isdigit()
            and (token == "0" or not token.startswith("0"))
            and int(token) < len(current)
        ):
            current = current[int(token)]
        else:
            raise SchemaAnnotationError(f"pointer {pointer!r} does not resolve")
    return current


def compile_validator(schema: Any) -> Callable[[Any], None]:
    """Compile an Infrastructure.Schema into a function that raises
    SchemaAnnotationError if a decoded document does not validate."""
    namespace = schema.namespace
    if schema.choice == "jsonschema":
        validator = _compile_jsonschema(schema.jsonschema.definition, namespace)
    elif schema.choice == "openapi":
        validator = _compile_openapi(schema.openapi.definition, schema.openapi.root, namespace)
    else:
        raise SchemaAnnotationError(f"schema {namespace} has no choice")

    def validate(document: Any) -> None:
        errors = sorted(validator.iter_errors(document), key=lambda e: list(map(str, e.path)))
        if errors:
            first = errors[0]
            where = "/" + "/".join(str(p) for p in first.path)
            raise SchemaAnnotationError(f"document does not validate against {namespace} at {where}: {first.message}")

    return validate


def _compile_jsonschema(definition: str, namespace: str) -> Any:
    from jsonschema.validators import validator_for

    body = decode_text(definition, f"schema {namespace} definition", MAX_DEFINITION_BYTES)
    cls = validator_for(body)
    try:
        cls.check_schema(body)
    except Exception as e:
        raise SchemaAnnotationError(f"schema {namespace} is not a valid JSON Schema: {e}")
    return cls(body)


def _compile_openapi(definition: str, root: str, namespace: str) -> Any:
    from openapi_schema_validator import OAS30Validator, OAS31Validator

    doc = decode_text(definition, f"schema {namespace} definition", MAX_DEFINITION_BYTES)
    if not isinstance(doc, dict):
        raise SchemaAnnotationError(f"schema {namespace} is not an OpenAPI document")
    version = str(doc.get("openapi", ""))
    if version.startswith("3.0"):
        cls = OAS30Validator
    elif version.startswith("3.1"):
        cls = OAS31Validator
    else:
        raise SchemaAnnotationError(f"schema {namespace} has unsupported openapi version {version!r}")
    components = doc.get("components", {})
    if root not in (components.get("schemas") or {}):
        raise SchemaAnnotationError(f"schema {namespace} has no root {root} under components/schemas")
    body = {"$ref": f"#/components/schemas/{root}", "components": components}
    try:
        return cls(body)
    except Exception as e:
        raise SchemaAnnotationError(f"schema {namespace} is not a valid OpenAPI document: {e}")


def jsonpath_selects(path: str, element: Any) -> bool:
    """True if the RFC 9535 JSONPath selects at least one node of element."""
    return len(_JSONPATH.find(path, element)) > 0


def validate_jsonpath(path: str) -> None:
    """Raise SchemaAnnotationError if path is not a valid JSONPath."""
    if not path or not path.startswith("$"):
        raise SchemaAnnotationError(f"path {path!r} must be a JSONPath that starts with $")
    try:
        _JSONPATH.compile(path)
    except Exception as e:
        raise SchemaAnnotationError(f"path {path!r} is not valid JSONPath: {e}")
