from typing import Union
from db import obtain_100_rows
from fastapi import FastAPI
import math

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


@app.get("/value")
def get_values():
    rows = obtain_100_rows()
    from db import cur
    columns = [desc[0] for desc in cur.description]
    import decimal

    result = []
    for row in rows:
        row_dict = {}
        for col, val in zip(columns, row):
            if isinstance(val, decimal.Decimal):
                fval = float(val)
                # Check for NaN or Infinity
                if math.isnan(fval) or math.isinf(fval):
                    row_dict[col] = None  # or set to 0, or skip, as you prefer
                else:
                    row_dict[col] = fval
            else:
                row_dict[col] = val
        result.append(row_dict)
    return {"rows": result}