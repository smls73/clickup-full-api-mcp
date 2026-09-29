"""content_file on create_doc_page and update_doc_page: page text read from a local file.

No network, no token: the client's _request is replaced by a recorder, and each tool
runs through the real dispatch (execute_tool) or the real safety gate (call_tool).
The allowed folders are pointed at a scratch folder for each test, so nothing is
written under the real allowed folders.
"""

import asyncio
import json
import os
import shutil
import tempfile
import unittest

from clickup_mcp import server
from clickup_mcp.client import ClickUpClient

# Emojis (including a joined family and a flag), accents, Cyrillic, CRLF and a tab: all must arrive unchanged.
SAMPLE = "🗂️ Meeting Filing Log\r\n| 📅 Date | 👨‍👩‍👧 Who | 🇲🇽 |\n\tcafé Ирина ✅🔄⏳\n[link](https://a.com) end"
CREATE = {"team_id": "9", "doc_id": "d", "name": "P"}
UPDATE = {"team_id": "9", "doc_id": "d", "page_id": "p"}


class Recorder:
    def __init__(self):
        self.calls = []

    async def __call__(self, method, endpoint, params=None, json=None, data=None, **kw):
        self.calls.append({"method": method, "endpoint": endpoint, "json": json})
        return {"ok": True}


def make_client():
    c = ClickUpClient(api_token="test-token-not-real")
    rec = Recorder()
    c._request = rec
    return c, rec


def run(coro):
    return asyncio.run(coro)


class Base(unittest.TestCase):
    def setUp(self):
        self.scratch = os.path.realpath(tempfile.mkdtemp(prefix="cf-test-"))
        self.root = os.path.join(self.scratch, "allowed")
        self.outside = os.path.join(self.scratch, "outside")
        os.makedirs(os.path.join(self.root, "sub"))
        os.makedirs(self.outside)
        self._roots = server.CONTENT_FILE_ROOTS
        server.CONTENT_FILE_ROOTS = (self.root,)

    def tearDown(self):
        server.CONTENT_FILE_ROOTS = self._roots
        for dirpath, dirnames, _ in os.walk(self.scratch):
            for d in dirnames:  # unlink junctions first so rmtree never follows one
                full = os.path.join(dirpath, d)
                if os.path.isjunction(full) or os.path.islink(full):
                    os.unlink(full)
        shutil.rmtree(self.scratch, ignore_errors=True)

    def write(self, rel, data, base=None):
        path = os.path.join(base or self.root, rel)
        with open(path, "wb") as f:
            f.write(data if isinstance(data, bytes) else data.encode("utf-8"))
        return path

    def dispatch(self, name, args):
        c, rec = make_client()
        run(server.execute_tool(c, name, dict(args)))
        return rec.calls

    def gated(self, name, args):
        """Through call_tool (safety gate + error wrapping). Returns (reply dict, calls sent)."""
        c, rec = make_client()
        server._client = c
        try:
            out = run(server.call_tool(name, dict(args)))
        finally:
            server._client = None
        return json.loads(out[0].text), rec.calls

    def refused(self, name, args, words):
        reply, calls = self.gated(name, args)
        self.assertEqual(calls, [], "nothing may be sent when content_file is refused")
        self.assertIn("error", reply)
        for w in words:
            self.assertIn(w, reply["error"])
        return reply["error"]


class SendsFileUnchanged(Base):
    def test_create_sends_exact_file_text(self):
        path = self.write("page.md", SAMPLE)
        calls = self.dispatch("create_doc_page", {**CREATE, "content_file": path})
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["json"]["content"], SAMPLE)
        with open(path, "rb") as f:
            self.assertEqual(calls[0]["json"]["content"].encode("utf-8"), f.read())
        self.assertEqual(calls[0]["json"]["content_format"], "text/md")
        self.assertNotIn("content_file", calls[0]["json"])

    def test_update_sends_exact_file_text_in_each_mode(self):
        path = self.write("sub/page.md", SAMPLE)
        for mode in ("append", "prepend"):
            with self.subTest(mode):
                calls = self.dispatch("update_doc_page", {**UPDATE, "content_file": path, "content_edit_mode": mode})
                self.assertEqual(calls[0]["method"], "PUT")
                self.assertEqual(calls[0]["json"], {"content_edit_mode": mode, "content_format": "text/md", "content": SAMPLE})

    def test_large_page_like_the_filing_log(self):
        text = ("| 2026-09-28 | 📅 Sync | ✅ filed | 👉 [page](https://app.clickup.com/x) |\n" * 1200)[:77000]
        path = self.write("log.md", text)
        calls = self.dispatch("update_doc_page", {**UPDATE, "content_file": path, "content_edit_mode": "append"})
        self.assertEqual(calls[0]["json"]["content"], text)

    def test_empty_file_sends_empty_text_like_an_empty_string(self):
        path = self.write("empty.md", b"")
        self.assertEqual(self.dispatch("create_doc_page", {**CREATE, "content_file": path})[0]["json"]["content"],
                         self.dispatch("create_doc_page", {**CREATE, "content": ""})[0]["json"]["content"])

    def test_forward_slashes_and_other_letter_case_accepted(self):
        path = self.write("page.md", SAMPLE)
        for variant in (path.replace("\\", "/"), path.upper(), path.lower()):
            with self.subTest(variant):
                self.assertEqual(self.dispatch("create_doc_page", {**CREATE, "content_file": variant})[0]["json"]["content"], SAMPLE)

    def test_exactly_one_mib_accepted(self):
        path = self.write("big.md", b"a" * server.CONTENT_FILE_MAX_BYTES)
        calls = self.dispatch("create_doc_page", {**CREATE, "content_file": path})
        self.assertEqual(len(calls[0]["json"]["content"]), server.CONTENT_FILE_MAX_BYTES)


class ExactlyOneInput(Base):
    def test_both_refused_on_both_tools(self):
        path = self.write("page.md", SAMPLE)
        for name, ids in (("create_doc_page", CREATE), ("update_doc_page", UPDATE)):
            with self.subTest(name):
                self.refused(name, {**ids, "content": "x", "content_file": path}, ["not both"])

    def test_empty_string_content_plus_file_is_still_both(self):
        path = self.write("page.md", SAMPLE)
        self.refused("update_doc_page", {**UPDATE, "content": "", "content_file": path}, ["not both"])

    def test_neither_refused_on_create(self):
        self.refused("create_doc_page", dict(CREATE), ["content", "content_file"])

    def test_neither_on_update_is_a_name_only_change(self):
        calls = self.dispatch("update_doc_page", {**UPDATE, "name": "New"})
        self.assertEqual(calls[0]["json"], {"content_edit_mode": "append", "content_format": "text/md", "name": "New"})


class Encoding(Base):
    def test_invalid_utf8_refused(self):
        path = self.write("bad.md", b"ok \xff\xfe bad")
        err = self.refused("create_doc_page", {**CREATE, "content_file": path}, ["not valid UTF-8", "offset 3"])
        self.assertIn("content_file refused", err)

    def test_utf16_refused(self):
        path = self.write("u16.md", "hi 📅".encode("utf-16"))
        self.refused("create_doc_page", {**CREATE, "content_file": path}, ["UTF-8"])

    def test_byte_order_mark_refused(self):
        path = self.write("bom.md", b"\xef\xbb\xbf" + SAMPLE.encode("utf-8"))
        self.refused("update_doc_page", {**UPDATE, "content_file": path}, ["byte order mark"])


class AllowedFolders(Base):
    def test_default_roots_are_the_three_agreed_folders(self):
        self.assertEqual(
            self._roots,
            (r"I:\My Drive\TeamIS\_Systems", r"C:\Users\smls8\.claude\data", r"G:\My Drive\Nuage HQ"),
        )

    def test_outside_refused(self):
        path = self.write("page.md", SAMPLE, base=self.outside)
        self.refused("create_doc_page", {**CREATE, "content_file": path}, ["outside the allowed folders"])

    def test_sibling_with_shared_prefix_refused(self):
        twin = self.root + "-evil"
        os.makedirs(twin)
        path = self.write("page.md", SAMPLE, base=twin)
        self.refused("create_doc_page", {**CREATE, "content_file": path}, ["outside the allowed folders"])

    def test_the_root_folder_itself_refused(self):
        for p in (self.root, self.root + "\\"):
            with self.subTest(p):
                self.refused("create_doc_page", {**CREATE, "content_file": p}, ["an allowed folder, not a file"])

    def test_hard_link_to_outside_refused(self):
        target = self.write("page.md", SAMPLE, base=self.outside)
        link = os.path.join(self.root, "hl.md")
        os.link(target, link)
        self.refused("create_doc_page", {**CREATE, "content_file": link}, ["hard link"])

    def test_permission_errors_are_named_not_called_missing(self):
        path = self.write("page.md", SAMPLE)
        denied = PermissionError(13, "Access is denied")

        def boom(*a, **k):
            raise denied

        for attr, words in (("stat", ["cannot read", "Access is denied"]),):
            with self.subTest(attr):
                real = getattr(server.os, attr)
                setattr(server.os, attr, boom)
                try:
                    err = self.refused("create_doc_page", {**CREATE, "content_file": path}, words)
                finally:
                    setattr(server.os, attr, real)
                self.assertNotIn("not found", err)
        real_rp = server.os.path.realpath
        server.os.path.realpath = boom
        try:
            err = self.refused("create_doc_page", {**CREATE, "content_file": path}, ["cannot open", "Access is denied"])
        finally:
            server.os.path.realpath = real_rp
        self.assertNotIn("not found", err)

    def test_dot_dot_refused_even_when_it_lands_inside(self):
        self.write("page.md", SAMPLE, base=self.outside)
        self.write("page.md", SAMPLE)
        escape = os.path.join(self.root, "..", "outside", "page.md")
        inside = os.path.join(self.root, "sub", "..", "page.md")
        for p in (escape, inside, escape.replace("\\", "/")):
            with self.subTest(p):
                self.refused("create_doc_page", {**CREATE, "content_file": p}, ["'..'"])

    def test_relative_and_drive_relative_refused(self):
        for p in ("page.md", r"sub\page.md", "C:page.md", r"\Users\page.md"):
            with self.subTest(p):
                self.refused("create_doc_page", {**CREATE, "content_file": p}, ["absolute path"])

    def test_network_and_device_paths_refused(self):
        for p in (r"\\server\share\page.md", r"\\?\C:\x\page.md", r"\\.\C:\x\page.md", "//server/share/page.md"):
            with self.subTest(p):
                self.refused("create_doc_page", {**CREATE, "content_file": p}, ["network and device"])

    def test_alternate_data_stream_refused(self):
        path = self.write("page.md", SAMPLE)
        self.refused("create_doc_page", {**CREATE, "content_file": path + ":hidden"}, ["absolute path"])

    def test_not_a_string_or_empty_refused(self):
        for p in ("", 5, ["a"]):
            with self.subTest(p=p):
                self.refused("create_doc_page", {**CREATE, "content_file": p}, ["non-empty absolute path"])

    def test_missing_file_refused(self):
        self.refused("create_doc_page", {**CREATE, "content_file": os.path.join(self.root, "nope.md")}, ["not found"])

    def test_folder_refused(self):
        self.refused("create_doc_page", {**CREATE, "content_file": os.path.join(self.root, "sub")}, ["not a regular file"])

    def test_junction_to_outside_refused(self):
        self.write("page.md", SAMPLE, base=self.outside)
        link = os.path.join(self.root, "jx")
        import _winapi
        _winapi.CreateJunction(self.outside, link)
        self.refused("create_doc_page", {**CREATE, "content_file": os.path.join(link, "page.md")}, ["link, junction"])

    def test_junction_to_inside_refused(self):
        self.write("sub/page.md", SAMPLE)
        link = os.path.join(self.root, "jin")
        import _winapi
        _winapi.CreateJunction(os.path.join(self.root, "sub"), link)
        self.refused("create_doc_page", {**CREATE, "content_file": os.path.join(link, "page.md")}, ["link, junction"])

    def test_file_symlink_refused(self):
        target = self.write("page.md", SAMPLE, base=self.outside)
        link = os.path.join(self.root, "sl.md")
        try:
            os.symlink(target, link)
        except OSError:
            self.skipTest("this Windows account cannot create symbolic links")
        self.refused("create_doc_page", {**CREATE, "content_file": link}, ["link, junction"])

    def test_reparse_check_catches_a_link_that_resolves_to_itself(self):
        # Belt and braces: even if the real path matched, a reparse point below the root is refused.
        path = self.write("page.md", SAMPLE)
        real_lstat = os.lstat

        class Fake:
            def __init__(self, st):
                self.st_file_attributes = st.st_file_attributes | 0x400

        server.os.lstat = lambda p: Fake(real_lstat(p)) if os.path.normcase(p) == os.path.normcase(path) else real_lstat(p)
        try:
            self.refused("create_doc_page", {**CREATE, "content_file": path}, ["is a link or junction"])
        finally:
            server.os.lstat = real_lstat


class SizeCap(Base):
    def test_over_one_mib_refused(self):
        path = self.write("big.md", b"a" * (server.CONTENT_FILE_MAX_BYTES + 1))
        self.refused("update_doc_page", {**UPDATE, "content_file": path}, ["1,048,577 bytes", "1 MiB"])

    def test_cap_is_one_mib(self):
        self.assertEqual(server.CONTENT_FILE_MAX_BYTES, 1048576)


class SafetyGateUnchanged(Base):
    def test_replace_with_file_blocked_without_token_and_file_not_read(self):
        missing = os.path.join(self.root, "never-read.md")
        reply, calls = self.gated("update_doc_page", {**UPDATE, "content_file": missing, "content_edit_mode": "replace"})
        self.assertIn("blocked", reply)
        self.assertEqual(calls, [])

    def test_replace_with_file_and_token_sends_file_text(self):
        path = self.write("page.md", SAMPLE)
        reply, calls = self.gated("update_doc_page", {**UPDATE, "content_file": path, "content_edit_mode": "replace",
                                                      "confirm": "CONFIRM update_doc_page"})
        self.assertEqual(reply, {"ok": True})
        self.assertEqual(calls[0]["json"], {"content_edit_mode": "replace", "content_format": "text/md", "content": SAMPLE})

    def test_replace_with_string_still_blocked_without_token(self):
        reply, calls = self.gated("update_doc_page", {**UPDATE, "content": "x", "content_edit_mode": "replace"})
        self.assertIn("blocked", reply)
        self.assertEqual(calls, [])


class StringPathUnchanged(Base):
    def test_create_with_content_string_sends_the_same_body_as_before(self):
        calls = self.dispatch("create_doc_page", {**CREATE, "content": SAMPLE, "parent_page_id": "pp", "sub_title": "s"})
        self.assertEqual(calls[0]["method"], "POST")
        self.assertEqual(calls[0]["json"], {"name": "P", "content": SAMPLE, "content_format": "text/md",
                                            "parent_page_id": "pp", "sub_title": "s"})

    def test_update_with_content_string_sends_the_same_body_as_before(self):
        calls = self.dispatch("update_doc_page", {**UPDATE, "content": SAMPLE, "content_format": "text/plain"})
        self.assertEqual(calls[0]["json"], {"content_edit_mode": "append", "content_format": "text/plain", "content": SAMPLE})

    def test_update_empty_string_content_still_sent(self):
        calls = self.dispatch("update_doc_page", {**UPDATE, "content": ""})
        self.assertEqual(calls[0]["json"]["content"], "")


class Schema(unittest.TestCase):
    def tool(self, name):
        return next(t for t in server.TOOLS if t.name == name)

    def test_both_tools_offer_content_file(self):
        for name in ("create_doc_page", "update_doc_page"):
            with self.subTest(name):
                props = self.tool(name).inputSchema["properties"]
                self.assertEqual(props["content_file"]["type"], "string")
                self.assertIn("content_file", self.tool(name).description)

    def test_create_no_longer_requires_content_in_the_schema(self):
        self.assertEqual(self.tool("create_doc_page").inputSchema["required"], ["team_id", "doc_id", "name"])

    def test_no_top_level_combinators(self):
        # Claude's tool input schemas do not accept oneOf/anyOf/allOf at the top level.
        for name in ("create_doc_page", "update_doc_page"):
            schema = self.tool(name).inputSchema
            self.assertFalse({"oneOf", "anyOf", "allOf"} & set(schema))


G_ROOT = r"G:\My Drive\Nuage HQ"


class BusinessDriveRoot(unittest.TestCase):
    """The business tree root (added 2026-09-28, Scott's yes): same rules as the other roots.

    Uses the real default roots. Nothing is read or written: every case here is refused
    before any disk access. The shared rules themselves are tested on scratch folders above.
    """

    def refuse(self, path, words):
        with self.assertRaises(ValueError) as cm:
            server.read_content_file(path)
        for w in words:
            self.assertIn(w, str(cm.exception))

    def test_g_root_is_allowed_and_named_in_the_description(self):
        self.assertIn(G_ROOT, server.CONTENT_FILE_ROOTS)
        self.assertIn(G_ROOT + "\\", server.CONTENT_FILE_DESC)

    def test_outside_the_g_root_refused(self):
        for p in (r"G:\My Drive\other.md", r"G:\My Drive\Nuage HQ-copy\page.md", r"G:\page.md"):
            with self.subTest(p):
                self.refuse(p, ["outside the allowed folders"])

    def test_the_g_root_itself_refused(self):
        for p in (G_ROOT, G_ROOT + "\\", G_ROOT.lower()):
            with self.subTest(p):
                self.refuse(p, ["an allowed folder, not a file"])

    def test_dot_dot_under_the_g_root_refused(self):
        self.refuse(G_ROOT + r"\sub\..\page.md", ["'..' is not accepted"])

    def test_stream_under_the_g_root_refused(self):
        self.refuse(G_ROOT + r"\page.md:secret", ["absolute path"])


if __name__ == "__main__":
    unittest.main()
