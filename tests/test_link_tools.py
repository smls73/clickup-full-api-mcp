"""Tool-level tests: what each write tool actually sends to ClickUp.

No network, no token: the client's single _request function is replaced by a
recorder, and the tool runs through the real server dispatch (execute_tool)
and the real write-safety gate (call_tool).
"""

import asyncio
import json
import unittest

from clickup_mcp import safety, server
from clickup_mcp.client import ClickUpClient

LINK = [{"text": "Mail scans", "attributes": {"link": "https://app.clickup.com/8424803/docs/abc"}}]
MD = "[Mail scans](https://app.clickup.com/8424803/docs/abc)"

COMMENT_TOOLS = {
    # tool: (id args, method, endpoint, extra body keys expected besides the text)
    "create_task_comment": ({"task_id": "t1"}, "POST", "/task/t1/comment", {"notify_all": False}),
    "create_list_comment": ({"list_id": "l1"}, "POST", "/list/l1/comment", {"notify_all": False}),
    "create_chat_view_comment": ({"view_id": "v1"}, "POST", "/view/v1/comment", {"notify_all": False}),
    "update_comment": ({"comment_id": "c1"}, "PUT", "/comment/c1", {}),
    "create_threaded_comment": ({"comment_id": "c1"}, "POST", "/comment/c1/reply", {"notify_all": False}),
}


class Recorder:
    def __init__(self):
        self.calls = []

    async def __call__(self, method, endpoint, params=None, json=None, data=None, **kw):
        self.calls.append({"method": method, "endpoint": endpoint, "params": params, "json": json})
        return {"ok": True}


def make_client():
    c = ClickUpClient(api_token="test-token-not-real")
    rec = Recorder()
    c._request = rec
    return c, rec


def run(coro):
    return asyncio.run(coro)


class CommentToolTests(unittest.TestCase):
    def dispatch(self, name, args):
        c, rec = make_client()
        run(server.execute_tool(c, name, dict(args)))
        self.assertEqual(len(rec.calls), 1)
        return rec.calls[0]

    def test_comment_text_body_is_unchanged(self):
        for name, (ids, method, endpoint, extra) in COMMENT_TOOLS.items():
            with self.subTest(name):
                call = self.dispatch(name, {**ids, "comment_text": "hi https://a.com"})
                self.assertEqual(call["method"], method)
                self.assertEqual(call["endpoint"], endpoint)
                self.assertEqual(call["json"], {"comment_text": "hi https://a.com", **extra})

    def test_markdown_text_sends_link_blocks_only(self):
        for name, (ids, method, endpoint, extra) in COMMENT_TOOLS.items():
            with self.subTest(name):
                call = self.dispatch(name, {**ids, "markdown_text": MD})
                self.assertEqual(call["json"], {"comment": LINK, **extra})
                self.assertNotIn("comment_text", call["json"])

    def test_multiline_markdown_body(self):
        call = self.dispatch("create_task_comment", {"task_id": "t1", "markdown_text": "Line 1\n" + MD})
        self.assertEqual(
            call["json"]["comment"],
            [{"text": "Line 1", "attributes": {}}, {"text": "\n", "attributes": {}}] + LINK,
        )

    def test_markdown_without_link_is_plain(self):
        call = self.dispatch("create_task_comment", {"task_id": "t1", "markdown_text": "no link"})
        self.assertEqual(call["json"], {"comment_text": "no link", "notify_all": False})

    def test_other_task_comment_args_still_sent(self):
        call = self.dispatch(
            "create_task_comment",
            {"task_id": "t1", "markdown_text": MD, "assignee": "5", "notify_all": True, "custom_task_ids": True, "team_id": "9"},
        )
        self.assertEqual(call["json"], {"comment": LINK, "notify_all": True, "assignee": "5"})
        self.assertEqual(call["params"], {"custom_task_ids": "true", "team_id": "9"})

    def test_update_comment_resolved_kept(self):
        call = self.dispatch("update_comment", {"comment_id": "c1", "markdown_text": MD, "resolved": True})
        self.assertEqual(call["json"], {"comment": LINK, "resolved": True})

    def test_bad_input_returns_error_and_sends_nothing(self):
        raw = [{"text": "x", "attributes": {"link": "javascript:alert(1)"}}]
        for bad in ({}, {"comment_text": "a", "markdown_text": MD}, {"comment": raw}, {"comment_text": "a", "comment": raw}):
            for name, (ids, *_rest) in COMMENT_TOOLS.items():
                with self.subTest(name=name, bad=bad):
                    c, rec = make_client()
                    server._client = c
                    try:
                        out = run(server.call_tool(name, {**ids, **bad}))
                    finally:
                        server._client = None
                    self.assertIn("error", json.loads(out[0].text))
                    self.assertEqual(rec.calls, [])


class MarkdownFieldTests(unittest.TestCase):
    """Fields where ClickUp itself reads markdown: the connector passes text through untouched."""

    def dispatch(self, name, args):
        c, rec = make_client()
        run(server.execute_tool(c, name, dict(args)))
        return rec.calls[0]

    def test_list_markdown_content_passes_through(self):
        for name, ids in (
            ("create_list", {"folder_id": "f1", "name": "N"}),
            ("create_folderless_list", {"space_id": "s1", "name": "N"}),
            ("update_list", {"list_id": "l1"}),
        ):
            with self.subTest(name):
                call = self.dispatch(name, {**ids, "markdown_content": MD})
                self.assertEqual(call["json"]["markdown_content"], MD)

    def test_task_markdown_content_passes_through(self):
        call = self.dispatch("create_task", {"list_id": "l1", "name": "N", "markdown_content": MD})
        self.assertEqual(call["json"]["markdown_content"], MD)
        call = self.dispatch("update_task", {"task_id": "t1", "markdown_content": MD})
        self.assertEqual(call["json"]["markdown_content"], MD)

    def test_chat_content_passes_through_untouched(self):
        call = self.dispatch("send_chat_message", {"team_id": "9", "channel_id": "ch", "content": MD})
        self.assertEqual(call["json"], {"type": "message", "content": MD})
        call = self.dispatch("send_chat_reply", {"team_id": "9", "message_id": "m", "content": MD})
        self.assertEqual(call["json"], {"type": "message", "content": MD})
        call = self.dispatch("update_chat_message", {"team_id": "9", "message_id": "m", "content": MD})
        self.assertEqual(call["json"], {"content": MD})

    def test_doc_page_content_passes_through(self):
        call = self.dispatch("create_doc_page", {"team_id": "9", "doc_id": "d", "name": "P", "content": MD})
        self.assertEqual(call["json"]["content"], MD)
        self.assertEqual(call["json"]["content_format"], "text/md")


class SchemaTests(unittest.TestCase):
    def tool(self, name):
        return next(t for t in server.TOOLS if t.name == name)

    def test_comment_tools_offer_two_inputs(self):
        for name in COMMENT_TOOLS:
            with self.subTest(name):
                schema = self.tool(name).inputSchema
                for key in ("comment_text", "markdown_text"):
                    self.assertEqual(schema["properties"][key]["type"], "string")
                self.assertNotIn("comment", schema["properties"])
                self.assertNotIn("comment_text", schema["required"])
                for key in ("oneOf", "anyOf", "allOf"):
                    self.assertNotIn(key, schema)  # the Claude API rejects these at the top level

    def test_list_tools_offer_markdown_content(self):
        for name in ("create_list", "create_folderless_list", "update_list"):
            with self.subTest(name):
                self.assertIn("markdown_content", self.tool(name).inputSchema["properties"])

    def test_tool_names_unique_and_schemas_serialize(self):
        names = [t.name for t in server.TOOLS]
        self.assertEqual(len(names), len(set(names)))
        json.dumps([t.inputSchema for t in server.TOOLS])


class ClientDirectTests(unittest.TestCase):
    """The client helper keeps the exactly-one rule for direct callers too."""

    def test_both_or_neither_rejected(self):
        c, rec = make_client()
        calls = (
            lambda **kw: c.create_task_comment("t1", **kw),
            lambda **kw: c.create_list_comment("l1", **kw),
            lambda **kw: c.create_chat_view_comment("v1", **kw),
            lambda **kw: c.update_comment("c1", **kw),
            lambda **kw: c.create_threaded_comment("c1", **kw),
        )
        for fn in calls:
            for kw in ({}, {"comment_text": "a", "comment": [{"text": "a"}]}):
                with self.assertRaises(ValueError):
                    run(fn(**kw))
        self.assertEqual(rec.calls, [])

    def test_old_positional_call_unchanged(self):
        c, rec = make_client()
        run(c.create_task_comment("t1", "hello", "5", True, True, "9"))
        self.assertEqual(rec.calls[0]["json"], {"comment_text": "hello", "notify_all": True, "assignee": "5"})
        self.assertEqual(rec.calls[0]["params"], {"custom_task_ids": "true", "team_id": "9"})


class SafetyGateTests(unittest.TestCase):
    def test_red_chat_tools_still_blocked_without_token(self):
        for name in ("send_chat_message", "send_chat_reply", "update_chat_message"):
            with self.subTest(name):
                with self.assertRaises(safety.SafetyError):
                    safety.check(name, {"team_id": "9", "content": MD})

    def test_comment_tools_stay_green(self):
        for name in COMMENT_TOOLS:
            with self.subTest(name):
                self.assertNotIn(name, safety.RED_TOOLS)
                self.assertNotIn(name, safety.ADMIN_TOOLS)


if __name__ == "__main__":
    unittest.main()
