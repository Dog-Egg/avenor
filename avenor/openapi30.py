from __future__ import annotations as _annotations

import http as _http
import itertools as _itertools
import typing as _t

import zangar as _z
from zangar import compilation as _compilation

_OAS_SPECIFIC_OBJECTS = "oas_specific_objects"
_OAS_DECLARATION = "oas_declaration"
_HTTP_METHODS = ["get", "post", "put", "delete", "patch", "head", "options", "trace"]


def as_path_item_spec(obj, /, *, dispatch_name: str = "dispatch") -> dict:
    rv = {}
    method_common_specifics = []

    dispatch = getattr(obj, dispatch_name, None)
    if dispatch is not None:
        dispatch_specifics = getattr(dispatch, _OAS_SPECIFIC_OBJECTS, [])
        for specific in reversed(dispatch_specifics):
            if isinstance(specific, ParameterObject):
                _set_dict(rv, ["parameters"], lambda x: (x or []) + [specific.spec()])
            else:
                method_common_specifics.append(specific)

    for method in _HTTP_METHODS:
        if not hasattr(obj, method):
            continue

        method_handle = getattr(obj, method)
        method_specifics = getattr(method_handle, _OAS_SPECIFIC_OBJECTS, [])
        for specific in _itertools.chain(
            method_common_specifics, reversed(method_specifics)
        ):
            if isinstance(specific, ParameterObject):
                _set_dict(
                    rv,
                    [method, "parameters"],
                    lambda x: (x or []) + [specific.spec()],
                )
            elif isinstance(specific, ResponseObject):
                _set_dict(
                    rv,
                    [method, "responses", str(specific.status_code)],
                    lambda _: specific.spec(),
                )
            elif isinstance(specific, RequestBodyObject):
                _set_dict(rv, [method, "requestBody"], lambda _: specific.spec())
            else:
                raise NotImplementedError(f"Unknown specific object: {specific}")

        operation_spec: dict | None = getattr(method_handle, _OAS_DECLARATION, None)
        if operation_spec is not None:
            _set_dict(
                rv,
                [method],
                lambda x: {**x, **operation_spec} if x is not None else x,  # type: ignore
            )

    return rv


class _SpecificObject:
    pass


def specify(specific: _SpecificObject, /):
    def decorator(func):
        objs = getattr(func, _OAS_SPECIFIC_OBJECTS, [])
        objs.append(specific)
        setattr(func, _OAS_SPECIFIC_OBJECTS, objs)

        return func

    return decorator


def declare(spec: dict, /):
    def decorator(obj):
        if hasattr(obj, _OAS_DECLARATION):
            raise RuntimeError("Cannot declare multiple times")  # pragma: no cover
        setattr(obj, _OAS_DECLARATION, spec)

        return obj

    return decorator


class ParameterObject(_SpecificObject):
    def __init__(
        self,
        *,
        name: str,
        location: _t.Literal["query", "path", "header", "cookie"],
        required=False,
        schema: _z.Schema | None = None,
        description: str | None = None,
    ):
        self.name = name
        self.location = location
        self.required = required
        self.__schema = schema
        self.description = description

    def spec(self):
        rv: dict = {
            "name": self.name,
            "in": self.location,
        }
        if self.__schema:
            rv["schema"] = _compilation.OpenAPI30Compiler().compile(self.__schema)
        if self.required:
            rv["required"] = True
        if self.description is not None:
            rv["description"] = self.description
        return rv


class ResponseObject(_SpecificObject):
    def __init__(
        self,
        status_code: int,
        /,
        *,
        content: dict[str, MediaTypeObject] | None = None,
        description: str | None = None,
    ):
        self.status_code = status_code
        self.content = content
        self.description = description

    def spec(self):
        rv: dict = {
            "description": self.description
            or _http.HTTPStatus(self.status_code).phrase,
        }
        if self.content:
            rv["content"] = {
                content_type: content.spec()
                for content_type, content in self.content.items()
            }
        return rv


class RequestBodyObject(_SpecificObject):
    def __init__(
        self,
        *,
        content: dict[str, MediaTypeObject],
        description: str | None = None,
        required=False,
    ):
        self.content = content
        self.description = description
        self.required = required

    def spec(self):
        rv: dict = {
            "content": {k: v.spec() for k, v in self.content.items()},
        }
        if self.description is not None:
            rv["description"] = self.description
        if self.required:
            rv["required"] = True
        return rv


def _set_dict(
    data: dict, path: list[_t.Hashable], setter: _t.Callable[[_t.Any], _t.Any]
):
    d = data
    for index, key in enumerate(path):
        if index == len(path) - 1:
            d[key] = setter(d.get(key))
        else:
            d = d.setdefault(key, {})
    return data


class MediaTypeObject:
    def __init__(self, *, schema: _z.Schema | None = None):
        self.__schema = schema

    def spec(self):
        rv = {}
        if self.__schema:
            rv["schema"] = _compilation.OpenAPI30Compiler().compile(self.__schema)
        return rv
