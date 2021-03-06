# 02/11/22
# app.py
from typing import Optional, Generator
import json
import requests
from requests import Session, Response

class AirtableBaseAPI:
    def __init__(self, baseID: str, api_key: str, schema: dict | tuple=(),  enforce_schema=False):
        self.host = "https://api.airtable.com/v0"
        self.baseID = baseID

        self.schema = schema
        self.enforce_schema = enforce_schema

        self.api = f"{self.host}/{baseID}"
        self.auth = {"Authorization": f"Bearer {api_key}"}
        self.session = Session()

    def _request(self, method, table, *args, raise_for_status=False, **kwargs) -> Response:
        if self.enforce_schema and not table in self.schema:
            raise ValueError(f"Table {table} does not exist")
        headers = self.auth | kwargs.pop("headers", {})
        response = method(f"{self.api}/{table}", *args, headers=headers, **kwargs)
        if raise_for_status:
            response.raise_for_status()
        return response

    def _update_request(self, method, table, data, *args, maximum=10, **kwargs) -> Response:
        if not 0 < len(data) <= maximum:
            raise ValueError("Only between one and ten values can be included.")
        headers = {"Content-Type": "application/json"} | kwargs.pop("headers", {})
        return self._request(method, table, *args, headers=headers, data=json.dumps(data), **kwargs)

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.session.close()

class Airtable(AirtableBaseAPI):
    def get(self, *args, **kwargs) -> Response:
        return self._request(self.session.get, *args, **kwargs)

    def post(self, table, data, *args, maximum=10, **kwargs) -> Response:
        if not 0 < len(data) <= maximum:
            raise ValueError("Only between one and ten values can be included.")
        records = {"records": [{"fields": i} for i in data]}
        return self._update_request(self.session.post, table, records, *args, **kwargs)

    def patch(self, *args, **kwargs) -> Response:
        return self._update_request(self.session.patch, *args, **kwargs)

    def put(self, *args, **kwargs) -> Response:
        return self._update_request(self.session.put, *args, **kwargs)

    def delete(self, table, IDs, *args, maximum=10, **kwargs) -> Response:
        params: list[tuple[str, str]]
        params = [(f"records[]", IDs)] if isinstance(IDs, str) else [(f"records[]", ID) for ID in IDs]
        return self._request(self.session.delete, table, *args, params=params, **kwargs)

    def dump_tables(self, tables=(), *args, **kwargs) -> Generator:
        for table in tables or self.schema:
            yield table, self.get(table, *args, **kwargs)

    # Aliases for the corresponding request methods
    select, insert, update, update_and_clear = get, post, patch, put
