from typing import Literal, Union
from fastapi import FastAPI
from db import single_lookup

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


# TODO: make the logic dynamic for all three tables when looking up information, Key is to use literals from typing, also will need it for select and from values
@app.get("/{lookup}/{item_id}")
def read_item(lookup: Literal['users', 'products'], item_id: int, q: Union[str, None] = None):
    return single_lookup(lookup, item_id, q)