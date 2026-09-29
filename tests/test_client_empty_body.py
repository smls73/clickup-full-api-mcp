"""A write that succeeds with an empty body is a success, not a JSON error (audit item A8).

ClickUp's update_doc_page answers 200 with no body. The client used to treat only 204 as
empty and called response.json() on the empty 200, so a write that worked was reported
as "Expecting value". No network: every response comes from httpx.MockTransport.
"""

import asyncio
import json
import unittest

import httpx

from clickup_mcp import server
from clickup_mcp.client import ClickUpClient


def client_answering(status, body=b"", content_type=None):
    seen = []

    def handler(request):
        seen.append(request)
        headers = {"Content-Type": content_type} if content_type else {}
        return httpx.Response(status, content=body, headers=headers)

    c = ClickUpClient(api_token="test-token-not-real")
    c._client = httpx.AsyncClient(base_url=c.BASE_URL, transport=httpx.MockTransport(handler))
    return c, seen


def run(coro):
    return asyncio.run(coro)


class EmptySuccessBody(unittest.TestCase):
    def test_empty_2xx_is_the_same_success_as_204(self):
        for status in (200, 201, 202, 204):
            with self.subTest(status):
                c, _ = client_answering(status)
                self.assertEqual(run(c.put("/x", json={"a": 1})), {"success": True})

    def test_whitespace_only_body_is_empty(self):
        for body in (b" ", b"\n", b"\r\n\t "):
            with self.subTest(body):
                c, _ = client_answering(200, body)
                self.assertEqual(run(c.post("/x")), {"success": True})

    def test_json_body_still_parsed(self):
        c, _ = client_answering(200, b'{"id": "p1"}', "application/json")
        self.assertEqual(run(c.get("/x")), {"id": "p1"})

    def test_non_json_body_still_raises(self):
        c, _ = client_answering(200, b"<html>not json</html>")
        with self.assertRaises(ValueError):
            run(c.get("/x"))

    def test_empty_error_status_still_raises(self):
        for status in (400, 404, 500):
            with self.subTest(status):
                c, _ = client_answering(status)
                with self.assertRaises(httpx.HTTPStatusError):
                    run(c.get("/x"))

    def test_empty_redirect_is_not_called_a_success(self):
        c, _ = client_answering(302)
        with self.assertRaises(ValueError):
            run(c.get("/x"))

    def test_update_doc_page_empty_200_reports_success_through_the_tool(self):
        c, seen = client_answering(200)
        server._client = c
        try:
            out = run(server.call_tool("update_doc_page", {"team_id": "9", "doc_id": "d", "page_id": "p", "name": "New"}))
        finally:
            server._client = None
        self.assertEqual(json.loads(out[0].text), {"success": True})
        self.assertEqual(len(seen), 1)
        self.assertEqual(seen[0].method, "PUT")


if __name__ == "__main__":
    unittest.main()
