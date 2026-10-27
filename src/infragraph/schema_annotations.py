"""Schema based annotations: schema compilation, document validation,
JSON Pointer resolution and JSONPath evaluation."""

import json
import math
import re
from functools import lru_cache
from typing import Any, Callable, Dict, Optional

import re2
from iregexp_check import check
from jsonpath_rfc9535 import JSONPathEnvironment
from jsonschema import validators
from jsonschema.exceptions import ValidationError
from openapi_schema_validator import OAS30Validator, OAS31Validator
from referencing import Registry
from ruamel.yaml import YAML

from infragraph.schema_errors import SchemaAnnotationError

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

MAX_DEFINITION_BYTES = 8 * 1024 * 1024
MAX_DOCUMENT_BYTES = 1024 * 1024
MAX_DOCUMENT_NODES = 200_000
MAX_PATH_CHARS = 1024
MAX_DESCENDANT_SEGMENTS = 2


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


class _StrictJsonError(ValueError):
    """JSON that is well formed but not accepted, YAML must not reparse it."""


def _reject_constant(name: str) -> Any:
    raise _StrictJsonError(f"non finite number {name}")


def _load_json(text: str) -> Any:
    """Strict JSON, raises ValueError on duplicate keys or constants."""

    def no_duplicates(pairs):
        keys = [k for k, _ in pairs]
        if len(keys) != len(set(keys)):
            raise _StrictJsonError("duplicate key")
        return dict(pairs)

    return json.loads(text, object_pairs_hook=no_duplicates, parse_constant=_reject_constant)


def decode_text(text: str, what: str, max_bytes: int) -> Any:
    """Decode JSON or YAML text containing only JSON data types."""
    if len(text.encode("utf-8")) > max_bytes:
        raise SchemaAnnotationError(f"{what} exceeds {max_bytes} bytes")
    try:
        # the C JSON parser is much faster, YAML is the fallback
        data = _load_json(text)
    except _StrictJsonError as e:
        raise SchemaAnnotationError(f"{what} is not accepted: {e}")
    except ValueError:
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
    try:
        return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    except ValueError as e:
        # for example an integer beyond the interpreter digit limit
        raise SchemaAnnotationError(f"value cannot be serialized: {e}")


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
        try:
            errors = sorted(validator.iter_errors(document), key=lambda e: list(map(str, e.path)))
        except Exception as e:
            raise SchemaAnnotationError(f"schema {namespace} cannot be evaluated: {e}")
        if errors:
            first = errors[0]
            where = "/" + "/".join(str(p) for p in first.path)
            raise SchemaAnnotationError(f"document does not validate against {namespace} at {where}: {first.message}")

    return validate


@lru_cache(maxsize=1024)
def _compile_schema_re2(pattern: str) -> Any:
    """Compile a schema pattern with RE2, which has no backtracking."""
    try:
        return re2.compile(pattern)
    except Exception as e:
        raise SchemaAnnotationError(f"schema pattern {pattern!r} is not supported by RE2: {e}")


# keywords whose values are data, not schemas
_DATA_KEYWORDS = frozenset({"enum", "const", "default", "example", "examples"})
# keywords whose values map arbitrary names to schemas
_NAME_MAP_KEYWORDS = frozenset(
    {"properties", "patternProperties", "$defs", "definitions", "dependentSchemas", "dependencies", "schemas"}
)


def _iter_schema_dicts(node: Any):
    """Yield every dict that is a schema, skipping data keyword values and
    treating the keys of a name map as names rather than keywords."""
    stack = [(node, False)]
    while stack:
        item, is_name_map = stack.pop()
        if isinstance(item, dict):
            if is_name_map:
                stack.extend((v, False) for v in item.values())
                continue
            yield item
            stack.extend((v, k in _NAME_MAP_KEYWORDS) for k, v in item.items() if k not in _DATA_KEYWORDS)
        elif isinstance(item, list):
            stack.extend((v, False) for v in item)


def _check_schema_patterns(node: Any) -> None:
    """Compile every pattern and patternProperties key with RE2."""
    for item in _iter_schema_dicts(node):
        if isinstance(item.get("pattern"), str):
            _compile_schema_re2(item["pattern"])
        properties = item.get("patternProperties")
        if isinstance(properties, dict):
            for key in properties:
                _compile_schema_re2(key)


def _check_local_refs(node: Any, namespace: str) -> None:
    """Reject any $ref that does not point inside the document."""
    for item in _iter_schema_dicts(node):
        ref = item.get("$ref")
        if isinstance(ref, str) and not ref.startswith("#"):
            raise SchemaAnnotationError(f"schema {namespace} has a non local $ref {ref!r}")


def _check_unevaluated_properties(node: Any, namespace: str) -> None:
    """Reject unevaluatedProperties combined with patternProperties, the
    jsonschema evaluation of that pair uses backtracking regular expressions."""
    schemas = list(_iter_schema_dicts(node))
    if any("unevaluatedProperties" in s for s in schemas) and any(
        isinstance(s.get("patternProperties"), dict) for s in schemas
    ):
        raise SchemaAnnotationError(f"schema {namespace} combines unevaluatedProperties and patternProperties")


def _re2_pattern(validator, pattern, instance, schema):
    if validator.is_type(instance, "string") and _compile_schema_re2(pattern).search(instance) is None:
        yield ValidationError(f"{instance!r} does not match {pattern!r}")


def _re2_pattern_properties(validator, patterns, instance, schema):
    if not validator.is_type(instance, "object"):
        return
    for pattern, subschema in patterns.items():
        compiled = _compile_schema_re2(pattern)
        for key, value in instance.items():
            if compiled.search(key) is not None:
                yield from validator.descend(value, subschema, path=key, schema_path=pattern)


def _re2_additional_properties(validator, additional, instance, schema):
    """additionalProperties with patternProperties evaluated by RE2, the
    jsonschema implementation joins the patterns for the re module."""
    if not validator.is_type(instance, "object"):
        return
    properties = schema.get("properties", {})
    patterns = [_compile_schema_re2(p) for p in schema.get("patternProperties", {})]
    extras = [k for k in instance if k not in properties and not any(p.search(k) for p in patterns)]
    if validator.is_type(additional, "object"):
        for extra in extras:
            yield from validator.descend(instance[extra], additional, path=extra)
    elif not additional and extras:
        # same wording as jsonschema
        extras = sorted(extras, key=str)
        joined = ", ".join(repr(e) for e in extras)
        if "patternProperties" in schema:
            verb = "does" if len(extras) == 1 else "do"
            regexes = ", ".join(repr(p) for p in sorted(schema["patternProperties"]))
            yield ValidationError(f"{joined} {verb} not match any of the regexes: {regexes}")
        else:
            verb = "was" if len(extras) == 1 else "were"
            yield ValidationError(f"Additional properties are not allowed ({joined} {verb} unexpected)")


def _hardened(cls: Any) -> Any:
    """Extend a validator class to evaluate patterns with RE2."""
    return validators.extend(
        cls,
        {
            "pattern": _re2_pattern,
            "patternProperties": _re2_pattern_properties,
            "additionalProperties": _re2_additional_properties,
        },
    )


def _compile_jsonschema(definition: str, namespace: str) -> Any:
    body = decode_text(definition, f"schema {namespace} definition", MAX_DEFINITION_BYTES)
    cls = validators.validator_for(body)
    try:
        cls.check_schema(body)
    except Exception as e:
        raise SchemaAnnotationError(f"schema {namespace} is not a valid JSON Schema: {e}")
    _check_schema_patterns(body)
    _check_local_refs(body, namespace)
    _check_unevaluated_properties(body, namespace)
    # an empty registry resolves no remote reference
    return _hardened(cls)(body, registry=Registry())


def _compile_openapi(definition: str, root: str, namespace: str) -> Any:
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
    _check_schema_patterns(components)
    _check_local_refs(components, namespace)
    _check_unevaluated_properties(components, namespace)
    body = {"$ref": f"#/components/schemas/{root}", "components": components}
    try:
        # an empty registry resolves no remote reference
        return _hardened(cls)(body, registry=Registry())
    except Exception as e:
        raise SchemaAnnotationError(f"schema {namespace} is not a valid OpenAPI document: {e}")


_QUOTED = re.compile(r"'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\"")


@lru_cache(maxsize=1024)
def _compile_path(path: str) -> Any:
    """Compile and bound a JSONPath, raises SchemaAnnotationError."""
    if not path or not path.startswith("$"):
        raise SchemaAnnotationError(f"path {path!r} must be a JSONPath that starts with $")
    if len(path) > MAX_PATH_CHARS:
        raise SchemaAnnotationError(f"path exceeds {MAX_PATH_CHARS} characters")
    # descendant segments are polynomial in the document size
    if _QUOTED.sub("", path).count("..") > MAX_DESCENDANT_SEGMENTS:
        raise SchemaAnnotationError(f"path has more than {MAX_DESCENDANT_SEGMENTS} descendant segments")
    try:
        return _JSONPATH.compile(path)
    except Exception as e:
        raise SchemaAnnotationError(f"path {path!r} is not valid JSONPath: {e}")


def jsonpath_selects(path: str, element: Any) -> bool:
    """True if the RFC 9535 JSONPath selects at least one node of element."""
    query = _compile_path(path)
    try:
        finditer = getattr(query, "finditer", None)
        if finditer is not None:
            # stop at the first match
            return next(iter(finditer(element)), None) is not None
        return len(query.find(element)) > 0
    except Exception as e:
        raise SchemaAnnotationError(f"path {path!r} cannot be evaluated: {e}")


def validate_jsonpath(path: str) -> None:
    """Raise SchemaAnnotationError if path is not a valid JSONPath."""
    _compile_path(path)
