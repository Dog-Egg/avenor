import zangar as z

from avenor.openapi30 import (
    MediaTypeObject,
    ParameterObject,
    RequestBodyObject,
    ResponseObject,
    as_path_item_spec,
    declare,
    specify,
)

book_struct = z.struct(
    {
        "id": z.int(),
        "name": z.str(),
        "author": z.str(),
    }
)


class BookList:
    @declare({"summary": "Get book list"})
    @specify(
        ParameterObject(
            name="paging",
            location="query",
            schema=z.struct(
                {
                    "page": z.int().gte(1),
                    "page_size": z.int().gte(1),
                }
            ),
            description="Paging parameters",
        )
    )
    @specify(
        ResponseObject(
            200,
            content={
                "application/json": MediaTypeObject(
                    schema=z.struct(
                        {
                            "items": z.list(book_struct),
                            "count": z.int(),
                        }
                    )
                )
            },
        )
    )
    def get(self): ...

    @specify(
        ResponseObject(
            201,
            content={
                "application/json": MediaTypeObject(
                    schema=book_struct,
                )
            },
        )
    )
    @specify(
        RequestBodyObject(
            required=True,
            content={
                "application/json": MediaTypeObject(
                    schema=book_struct.omit_fields(["id"])
                )
            },
            description="Book information",
        )
    )
    def post(self): ...


class BookDetail:
    @specify(
        ParameterObject(
            name="id",
            location="path",
            schema=z.to.int(),
            required=True,
        )
    )
    @specify(ResponseObject(404, description="Book is not found"))
    def dispatch(self): ...

    @specify(
        ResponseObject(
            200,
            content={
                "application/json": MediaTypeObject(
                    schema=book_struct,
                )
            },
        )
    )
    def get(self): ...


openapi = {
    "openapi": "3.0.3",
    "info": {
        "title": "Bookstore API",
        "version": "0.1",
    },
    "paths": {
        "/books": as_path_item_spec(BookList),
        "/books/{id}": as_path_item_spec(BookDetail),
    },
}
