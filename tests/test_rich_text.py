"""Unit tests for the comment markdown converter (clickup_mcp.rich_text): links and rich formats.

Run with the server's own Python (stdlib unittest, no extra installs), from the
server folder, in PowerShell:
    $env:PYTHONPATH = "src"; .venv\\Scripts\\python.exe -m unittest discover -s tests -v
"""

import time
import unittest

from clickup_mcp.rich_text import comment_body, is_web_url, markdown_to_comment

T = lambda s: {"text": s, "attributes": {}}  # noqa: E731
NL = {"text": "\n", "attributes": {}}
L = lambda s, u: {"text": s, "attributes": {"link": u}}  # noqa: E731
B = lambda s: {"text": s, "attributes": {"bold": True}}  # noqa: E731
I = lambda s: {"text": s, "attributes": {"italic": True}}  # noqa: E731,E741
C = lambda s: {"text": s, "attributes": {"code": True}}  # noqa: E731
CODE_NL = {"text": "\n", "attributes": {"code-block": {"code-block": "plain"}}}


class ConverterTests(unittest.TestCase):
    def test_single_link(self):
        self.assertEqual(
            markdown_to_comment("See [Mail scans](https://app.clickup.com/8424803/docs/abc) now"),
            [T("See "), L("Mail scans", "https://app.clickup.com/8424803/docs/abc"), T(" now")],
        )

    def test_several_links(self):
        self.assertEqual(
            markdown_to_comment("[A](https://a.com) and [B](http://b.com/x?y=1&z=2)"),
            [L("A", "https://a.com"), T(" and "), L("B", "http://b.com/x?y=1&z=2")],
        )

    def test_adjacent_links(self):
        self.assertEqual(
            markdown_to_comment("[A](https://a.com)[B](https://b.com)"),
            [L("A", "https://a.com"), L("B", "https://b.com")],
        )

    def test_emoji_in_text_and_label(self):
        self.assertEqual(
            markdown_to_comment("📬 [Mail scans 📬 — September 2026](https://x.io/d) ✅"),
            [T("📬 "), L("Mail scans 📬 — September 2026", "https://x.io/d"), T(" ✅")],
        )

    def test_unicode_url_and_label(self):
        self.assertEqual(
            markdown_to_comment("[Café ñ](https://例え.jp/パス?q=é)"),
            [L("Café ñ", "https://例え.jp/パス?q=é")],
        )

    def test_url_with_parentheses(self):
        self.assertEqual(
            markdown_to_comment("[Foo](https://en.wikipedia.org/wiki/Foo_(bar)) done"),
            [L("Foo", "https://en.wikipedia.org/wiki/Foo_(bar)"), T(" done")],
        )

    def test_url_with_nested_parentheses(self):
        self.assertEqual(
            markdown_to_comment("[x](https://a.com/p_(q_(r))) end"),
            [L("x", "https://a.com/p_(q_(r))"), T(" end")],
        )

    def test_close_paren_right_after_link(self):
        self.assertEqual(
            markdown_to_comment("(see [doc](https://a.com))"),
            [T("(see "), L("doc", "https://a.com"), T(")")],
        )

    def test_fragment_and_query(self):
        self.assertEqual(
            markdown_to_comment("[s](https://a.com/p?x=1&y=2#part-3)"),
            [L("s", "https://a.com/p?x=1&y=2#part-3")],
        )

    def test_no_links(self):
        self.assertEqual(markdown_to_comment("Just text, no link."), [T("Just text, no link.")])

    def test_line_breaks(self):
        self.assertEqual(
            markdown_to_comment("Line one\n[Two](https://t.com)\n\nLine four"),
            [T("Line one"), NL, L("Two", "https://t.com"), NL, NL, T("Line four")],
        )

    def test_crlf_normalized(self):
        self.assertEqual(markdown_to_comment("a\r\nb"), [T("a"), NL, T("b")])

    def test_trailing_newline_kept(self):
        self.assertEqual(markdown_to_comment("a\n"), [T("a"), NL])

    def test_bare_url_stays_text(self):
        self.assertEqual(markdown_to_comment("https://a.com"), [T("https://a.com")])

    def test_non_http_scheme_stays_literal(self):
        s = "[bad](javascript:alert(1)) [m](mailto:x@y.com) [f](ftp://a.com)"
        self.assertEqual(markdown_to_comment(s), [T(s)])

    def test_hostless_urls_stay_literal(self):
        for s in ("[x](https://)", "[x](https://?q)", "[x](http:///path)", "[x](https://#frag)"):
            with self.subTest(s):
                self.assertEqual(markdown_to_comment(s), [T(s)])

    def test_control_character_in_url_stays_literal(self):
        s = "[x](https://a.com/\x07b)"
        self.assertEqual(markdown_to_comment(s), [T(s)])

    def test_bracket_in_url_stays_literal(self):
        s = "[x](https://a.com/[1])"
        self.assertEqual(markdown_to_comment(s), [T(s)])

    def test_short_http_url_is_a_link(self):
        self.assertEqual(markdown_to_comment("[x](http://a)"), [L("x", "http://a")])

    def test_unclosed_paren_stays_literal(self):
        self.assertEqual(markdown_to_comment("[x](https://a.com"), [T("[x](https://a.com")])

    def test_space_in_url_stays_literal(self):
        self.assertEqual(markdown_to_comment("[x](https://a.com/b c)"), [T("[x](https://a.com/b c)")])

    def test_empty_label_uses_url(self):
        self.assertEqual(markdown_to_comment("[](https://a.com)"), [L("https://a.com", "https://a.com")])

    def test_bracket_before_real_link(self):
        self.assertEqual(
            markdown_to_comment("[note [A](https://a.com)"),
            [T("[note "), L("A", "https://a.com")],
        )

    def test_plain_brackets_stay(self):
        self.assertEqual(markdown_to_comment("[draft] ready (v2)"), [T("[draft] ready (v2)")])

    def test_bold_next_to_link(self):
        # Before rich comments this bold stayed literal; the link block is unchanged.
        self.assertEqual(markdown_to_comment("**bold** [A](https://a.com)"), [B("bold"), T(" "), L("A", "https://a.com")])

    def test_escaped_opener_stays_literal(self):
        s = "\\[a](https://x.com)"
        self.assertEqual(markdown_to_comment(s), [T(s)])

    def test_image_stays_literal(self):
        s = "![logo](https://x.com/a.png)"
        self.assertEqual(markdown_to_comment(s), [T(s)])

    def test_link_inside_inline_code_is_never_a_link(self):
        self.assertEqual(
            markdown_to_comment("Use `[a](https://x.com)` then [b](https://y.com)"),
            [T("Use "), C("[a](https://x.com)"), T(" then "), L("b", "https://y.com")],
        )

    def test_link_inside_double_backtick_code_is_never_a_link(self):
        self.assertEqual(markdown_to_comment("``a ` [b](https://x.com) ``"), [C("a ` [b](https://x.com) ")])

    def test_unmatched_backtick_does_not_block_links(self):
        self.assertEqual(
            markdown_to_comment("it`s [a](https://x.com)"),
            [T("it`s "), L("a", "https://x.com")],
        )

    def test_link_inside_fenced_code_is_never_a_link(self):
        self.assertEqual(
            markdown_to_comment("```\n[a](https://x.com)\n```\n[b](https://y.com)"),
            [T("[a](https://x.com)"), CODE_NL, L("b", "https://y.com")],
        )

    def test_empty_rejected(self):
        with self.assertRaises(ValueError):
            markdown_to_comment("")


class HostileInputTests(unittest.TestCase):
    """Parsing stays linear: 200,000 characters of worst-case input in well under 2 s."""

    def assert_fast(self, s):
        t0 = time.perf_counter()
        markdown_to_comment(s)
        self.assertLess(time.perf_counter() - t0, 2.0)

    def test_many_openers(self):
        self.assert_fast("[" * 200_000)

    def test_many_unterminated_links(self):
        self.assert_fast("[x](https://a" * 15_000)

    def test_many_open_parens(self):
        self.assert_fast("[x](" + "(" * 200_000)

    def test_many_labels_without_url(self):
        self.assert_fast("[ab]" * 50_000)

    def test_many_backticks(self):
        self.assert_fast("`x" * 100_000)

    def test_many_links(self):
        out = markdown_to_comment("[a](https://a.com) " * 10_000)
        self.assertEqual(sum("link" in b["attributes"] for b in out), 10_000)


class UrlCheckTests(unittest.TestCase):
    def test_accepts(self):
        for u in ("https://a.com", "http://a", "https://app.clickup.com/8424803/docs/x?y=1#z"):
            with self.subTest(u):
                self.assertTrue(is_web_url(u))

    def test_rejects(self):
        for u in ("", "https://", "https://?q", "javascript:alert(1)", "https://a.com/ b", "https://[bad", "HTTPX://a.com"):
            with self.subTest(u):
                self.assertFalse(is_web_url(u))


class CommentBodyTests(unittest.TestCase):
    def test_comment_text_unchanged(self):
        self.assertEqual(comment_body({"comment_text": "hi https://a.com"}), {"comment_text": "hi https://a.com"})

    def test_markdown_with_link_gives_blocks(self):
        self.assertEqual(
            comment_body({"markdown_text": "[A](https://a.com)"}),
            {"comment": [L("A", "https://a.com")]},
        )

    def test_markdown_without_link_falls_back_to_plain(self):
        self.assertEqual(comment_body({"markdown_text": "line 1\nline 2"}), {"comment_text": "line 1\nline 2"})

    def test_none_given_rejected(self):
        with self.assertRaises(ValueError):
            comment_body({})

    def test_two_given_rejected(self):
        with self.assertRaises(ValueError):
            comment_body({"comment_text": "a", "markdown_text": "b"})

    def test_raw_comment_refused(self):
        for args in ({"comment": [{"text": "x"}]}, {"comment_text": "a", "comment": [{"text": "x"}]}, {"comment_text": "a", "comment": None}):
            with self.subTest(args):
                with self.assertRaises(ValueError):
                    comment_body(args)

    def test_explicit_none_ignored(self):
        self.assertEqual(comment_body({"comment_text": "a", "markdown_text": None}), {"comment_text": "a"})


BI = lambda s: {"text": s, "attributes": {"bold": True, "italic": True}}  # noqa: E731


def LN(kind, indent=0):
    a = {"list": {"list": kind}}
    if indent:
        a["indent"] = indent
    return {"text": "\n", "attributes": a}


COL = {"text": "\n", "attributes": {"table-col": {"width": "150"}}}


def CELL(row, n):
    return {"text": "\n", "attributes": {"table-cell-line": {"row": row, "cell": f"{row}-{n}", "colspan": "1", "rowspan": "1"}}}


class InlineFormatTests(unittest.TestCase):
    def test_bold_both_markers(self):
        self.assertEqual(markdown_to_comment("a **b** c __d__"), [T("a "), B("b"), T(" c "), B("d")])

    def test_italic_both_markers(self):
        self.assertEqual(markdown_to_comment("a *b* c _d_"), [T("a "), I("b"), T(" c "), I("d")])

    def test_bold_italic(self):
        self.assertEqual(markdown_to_comment("***x***"), [BI("x")])

    def test_italic_inside_bold(self):
        self.assertEqual(markdown_to_comment("**a *b* c**"), [B("a "), BI("b"), B(" c")])

    def test_inline_code(self):
        self.assertEqual(markdown_to_comment("run `ls -la` now"), [T("run "), C("ls -la"), T(" now")])

    def test_markers_inside_code_stay(self):
        self.assertEqual(markdown_to_comment("`**not bold**`"), [C("**not bold**")])

    def test_code_inside_bold(self):
        self.assertEqual(markdown_to_comment("**see `x`**"), [B("see "), {"text": "x", "attributes": {"bold": True, "code": True}}])

    def test_bold_link(self):
        self.assertEqual(
            markdown_to_comment("**[Doc](https://a.com)** done"),
            [{"text": "Doc", "attributes": {"bold": True, "link": "https://a.com"}}, T(" done")],
        )

    def test_link_label_is_used_as_typed(self):
        self.assertEqual(markdown_to_comment("[**x**](https://a.com)"), [L("**x**", "https://a.com")])

    def test_emoji_inside_bold(self):
        self.assertEqual(markdown_to_comment("**📋 Update ✅**"), [B("📋 Update ✅")])

    def test_spaced_asterisks_stay_literal(self):
        self.assertEqual(markdown_to_comment("5 * 3 * 2"), [T("5 * 3 * 2")])

    def test_snake_case_stays_literal(self):
        self.assertEqual(markdown_to_comment("my_var_name and __init__x"), [T("my_var_name and __init__x")])

    def test_unmatched_markers_stay_literal(self):
        for s in ("**open only", "close only**", "*a", "a_", "** spaced **", "****", "*****x*****"):
            with self.subTest(s):
                self.assertEqual(markdown_to_comment(s), [T(s)])

    def test_crossing_markers_never_cross(self):
        self.assertEqual(markdown_to_comment("*a **b* c**"), [I("a **b"), T(" c**")])

    def test_bare_url_never_split_by_underscores(self):
        s = "https://x.com/_a_/b and http://y.org/__c__"
        self.assertEqual(markdown_to_comment(s), [T(s)])

    def test_bold_around_bare_url(self):
        self.assertEqual(markdown_to_comment("**https://a.com**"), [B("https://a.com")])

    def test_escaped_markers_stay_literal_with_backslash(self):
        s = "\\*not italic\\* and \\`not code\\`"
        self.assertEqual(markdown_to_comment(s), [T(s)])

    def test_unmatched_backtick_stays(self):
        self.assertEqual(markdown_to_comment("it`s **ok**"), [T("it`s "), B("ok")])

    def test_code_span_needs_same_length_run(self):
        self.assertEqual(markdown_to_comment("`a``b`"), [C("a``b")])


class LineFormatTests(unittest.TestCase):
    def test_bullets_all_markers(self):
        self.assertEqual(
            markdown_to_comment("- one\n* two\n+ three"),
            [T("one"), LN("bullet"), T("two"), LN("bullet"), T("three"), LN("bullet")],
        )

    def test_numbered(self):
        self.assertEqual(
            markdown_to_comment("1. one\n2) two\n10. ten"),
            [T("one"), LN("ordered"), T("two"), LN("ordered"), T("ten"), LN("ordered")],
        )

    def test_checklist(self):
        self.assertEqual(
            markdown_to_comment("- [ ] todo\n- [x] done\n* [X] also done\n- [ ]"),
            [T("todo"), LN("unchecked"), T("done"), LN("checked"), T("also done"), LN("checked"), LN("unchecked")],
        )

    def test_nested_indent(self):
        self.assertEqual(
            markdown_to_comment("- a\n  - b\n    1. c"),
            [T("a"), LN("bullet"), T("b"), LN("bullet", 1), T("c"), LN("ordered", 2)],
        )

    def test_list_item_with_formatting_and_link(self):
        self.assertEqual(
            markdown_to_comment("- **Due:** see [task](https://app.clickup.com/t/1)"),
            [B("Due:"), T(" see "), L("task", "https://app.clickup.com/t/1"), LN("bullet")],
        )

    def test_link_that_looks_like_a_checkbox_is_a_link(self):
        self.assertEqual(markdown_to_comment("- [x](https://a.com)"), [L("x", "https://a.com"), LN("bullet")])

    def test_list_trailing_newline_adds_nothing(self):
        self.assertEqual(markdown_to_comment("- a\n"), [T("a"), LN("bullet")])

    def test_text_after_list(self):
        self.assertEqual(markdown_to_comment("- a\nafter"), [T("a"), LN("bullet"), T("after")])

    def test_not_a_list(self):
        for s in ("-no space", "1.no space", "---", "***", "2026 was a year"):
            with self.subTest(s):
                self.assertEqual(markdown_to_comment(s), [T(s)])

    def test_code_block(self):
        self.assertEqual(
            markdown_to_comment("before\n```python\nx = 1\n\n  y = **2**\n```\nafter"),
            [T("before"), NL, T("x = 1"), CODE_NL, CODE_NL, T("  y = **2**"), CODE_NL, T("after")],
        )

    def test_empty_code_block(self):
        self.assertEqual(markdown_to_comment("```\n```"), [CODE_NL])

    def test_longer_closing_fence(self):
        self.assertEqual(markdown_to_comment("```\na\n````"), [T("a"), CODE_NL])

    def test_unclosed_fence_stays_literal_to_the_end(self):
        self.assertEqual(
            markdown_to_comment("**b**\n```\n- x [l](https://a.com)\n"),
            [B("b"), NL, T("```"), NL, T("- x [l](https://a.com)"), NL],
        )

    def test_headings_and_quotes_stay_literal(self):
        s = "# Title\n> quote\n~~strike~~"
        self.assertEqual(markdown_to_comment(s), [T("# Title"), NL, T("> quote"), NL, T("~~strike~~")])


class TableTests(unittest.TestCase):
    def test_simple_table(self):
        self.assertEqual(
            markdown_to_comment("| Client | Status |\n|---|:---:|\n| JEL | **done** |\n| Pell | [t](https://a.com) |"),
            [COL, COL,
             T("Client"), CELL("row-0000", 1), T("Status"), CELL("row-0000", 2),
             T("JEL"), CELL("row-0001", 1), B("done"), CELL("row-0001", 2),
             T("Pell"), CELL("row-0002", 1), L("t", "https://a.com"), CELL("row-0002", 2)],
        )

    def test_same_shape_as_scotts_hand_made_table(self):
        # Keys and value types of a real table comment read back from ClickUp (task "QBO billing",
        # 2026-06-02), minus ClickUp's own block-id: one table-col line per column, then each
        # cell's text and a "\n" carrying table-cell-line {row, cell, colspan, rowspan}.
        out = markdown_to_comment("| Client |\n| --- |\n| JEL |")
        self.assertEqual(out[0], {"text": "\n", "attributes": {"table-col": {"width": "150"}}})
        tcl = out[2]["attributes"]["table-cell-line"]
        self.assertEqual(sorted(tcl), ["cell", "colspan", "row", "rowspan"])
        self.assertTrue(all(isinstance(v, str) for v in tcl.values()))
        self.assertTrue(tcl["cell"].startswith(tcl["row"] + "-"))
        self.assertRegex(tcl["row"], r"^row-[0-9a-z]{4}$")

    def test_no_outer_pipes(self):
        self.assertEqual(
            markdown_to_comment("a | b\n--|--\n1 | 2"),
            [COL, COL, T("a"), CELL("row-0000", 1), T("b"), CELL("row-0000", 2),
             T("1"), CELL("row-0001", 1), T("2"), CELL("row-0001", 2)],
        )

    def test_short_row_padded_with_empty_cells(self):
        self.assertEqual(
            markdown_to_comment("| a | b |\n|---|---|\n| 1 |"),
            [COL, COL, T("a"), CELL("row-0000", 1), T("b"), CELL("row-0000", 2),
             T("1"), CELL("row-0001", 1), CELL("row-0001", 2)],
        )

    def test_escaped_pipe_inside_cell(self):
        self.assertEqual(
            markdown_to_comment("| a \\| b |\n|---|"),
            [COL, T("a | b"), CELL("row-0000", 1)],
        )

    def test_long_row_ends_the_table_and_stays_as_text(self):
        self.assertEqual(
            markdown_to_comment("| a |\n|---|\n| 1 |\n| 2 | 3 |"),
            [COL, T("a"), CELL("row-0000", 1), T("1"), CELL("row-0001", 1), T("| 2 | 3 |")],
        )

    def test_table_ends_at_blank_line_and_text_follows(self):
        self.assertEqual(
            markdown_to_comment("Intro:\n| a |\n|---|\n| 1 |\n\nafter"),
            [T("Intro:"), NL, COL, T("a"), CELL("row-0000", 1), T("1"), CELL("row-0001", 1), NL, T("after")],
        )

    def test_two_tables_get_different_row_ids(self):
        out = markdown_to_comment("| a |\n|---|\n\n| b |\n|---|")
        rows = [b["attributes"]["table-cell-line"]["row"] for b in out if "table-cell-line" in b["attributes"]]
        self.assertEqual(len(rows), 2)
        self.assertNotEqual(rows[0], rows[1])

    def test_not_a_table(self):
        for s in ("a | b", "a | b\n---", "| a | b |\n|---|", "| a |\n| x |", "a | b\n|--|--|--|"):
            with self.subTest(s):
                out = markdown_to_comment(s)
                self.assertFalse(any("table-col" in b["attributes"] or "table-cell-line" in b["attributes"] for b in out))
                self.assertEqual("".join(b["text"] for b in out), s)


class MixedContentTests(unittest.TestCase):
    def test_everything_together(self):
        md = (
            "📋 **Update** for *Scott*\n"
            "- [x] emailed [JEL](https://a.com)\n"
            "- [ ] call `Pell`\n"
            "1. first\n"
            "\n"
            "| Who | When |\n"
            "|-----|------|\n"
            "| IR | 7/1 |\n"
            "```\n"
            "raw *text*\n"
            "```\n"
            "Done ✅"
        )
        self.assertEqual(
            markdown_to_comment(md),
            [T("📋 "), B("Update"), T(" for "), I("Scott"), NL,
             T("emailed "), L("JEL", "https://a.com"), LN("checked"),
             T("call "), C("Pell"), LN("unchecked"),
             T("first"), LN("ordered"),
             NL,
             COL, COL, T("Who"), CELL("row-0000", 1), T("When"), CELL("row-0000", 2),
             T("IR"), CELL("row-0001", 1), T("7/1"), CELL("row-0001", 2),
             T("raw *text*"), CODE_NL,
             T("Done ✅")],
        )

    def test_no_text_is_lost(self):
        # Every character of the input either appears in a block or is a converted marker.
        md = "a **b** *c* `d` [e](https://f.com) \\[g](https://h.com) ![i](https://j.com) 5 * 6"
        text = "".join(b["text"] for b in markdown_to_comment(md))
        self.assertEqual(text, "a b c d e \\[g](https://h.com) ![i](https://j.com) 5 * 6")


class BadInputTests(unittest.TestCase):
    def test_not_a_string_rejected(self):
        for bad in (None, 5, ["a"], b"x"):
            with self.subTest(bad):
                with self.assertRaises(ValueError):
                    markdown_to_comment(bad)

    def test_whitespace_and_markers_only(self):
        for s in (" ", "\n", "**", "`", "|", "- ", "```"):
            with self.subTest(repr(s)):
                out = markdown_to_comment(s)
                self.assertIsInstance(out, list)
                self.assertTrue(all(isinstance(b["text"], str) and b["text"] for b in out))

    def test_control_characters_pass_through(self):
        self.assertEqual(markdown_to_comment("a\tb\x00c"), [T("a\tb\x00c")])


class RichHostileInputTests(unittest.TestCase):
    """Sized so a linear pass takes well under 0.5 s even on a loaded laptop (the first live
    install run hit 2.28 s on a 210,000-character case under load). A quadratic pass on
    these sizes would still take minutes, so the 2 s bound still catches it."""

    def assert_fast(self, s):
        t0 = time.perf_counter()
        markdown_to_comment(s)
        self.assertLess(time.perf_counter() - t0, 2.0)

    def test_many_asterisk_pairs(self):
        self.assert_fast("*a" * 30_000)

    def test_many_crossing_openers(self):
        self.assert_fast("*a **b " * 10_000)

    def test_many_underscores(self):
        self.assert_fast("_" * 70_000)

    def test_many_table_rows(self):
        self.assert_fast("| a | b |\n|---|---|\n" + "| 1 | 2 |\n" * 10_000)

    def test_failed_tables_do_not_rescan(self):
        self.assert_fast("| a |\n|---|\n" * 7_000 + "| 1 | 2 | 3 |")

    def test_many_list_lines(self):
        self.assert_fast("- [ ] item **b**\n" * 10_000)

    def test_unclosed_fence_after_many_lines(self):
        self.assert_fast("x\n" * 20_000 + "```\n" + "y\n" * 20_000)

    def test_many_closed_fences(self):
        self.assert_fast("```\na\n```\n" * 10_000)


class RichCommentBodyTests(unittest.TestCase):
    def test_bold_only_gives_blocks(self):
        self.assertEqual(comment_body({"markdown_text": "**hi**"}), {"comment": [B("hi")]})

    def test_list_only_gives_blocks(self):
        self.assertEqual(comment_body({"markdown_text": "- a"}), {"comment": [T("a"), LN("bullet")]})

    def test_nothing_to_format_is_sent_as_typed(self):
        s = "Plain 5 * 3, my_var, `unclosed, # heading\r\nline two"
        self.assertEqual(comment_body({"markdown_text": s}), {"comment_text": s})


class CodexRound1FixTests(unittest.TestCase):
    """Fixes from the Codex review, round 1 (2026-09-29)."""

    def test_image_label_markers_stay_literal(self):
        self.assertEqual(
            markdown_to_comment("![**alt**](https://x.com/a.png) **b**"),
            [T("![**alt**](https://x.com/a.png) "), B("b")],
        )

    def test_image_with_local_path_stays_literal(self):
        s = "![*a* `b`](pics/a_b_.png)"
        self.assertEqual(markdown_to_comment(s), [T(s)])

    def test_rest_of_escaped_backtick_run_is_literal(self):
        s = "\\``a`"
        self.assertEqual(markdown_to_comment(s), [T(s)])

    def test_backslash_before_closing_backtick_closes_the_span(self):
        self.assertEqual(markdown_to_comment("`a\\` b"), [C("a\\"), T(" b")])

    def test_many_distinct_backtick_run_lengths_stay_fast(self):
        s = "".join("`" * k + "x" for k in range(1, 601))  # about 180,000 characters
        t0 = time.perf_counter()
        markdown_to_comment(s)
        self.assertLess(time.perf_counter() - t0, 2.0)

    def test_row_ids_unique_across_tables_past_10000_rows(self):
        md = "| a |\n|---|\n" + "| r |\n" * 10_001 + "\n| b |\n|---|\n| s |"
        out = markdown_to_comment(md)
        cells = [b["attributes"]["table-cell-line"] for b in out if "table-cell-line" in b["attributes"]]
        self.assertEqual(len(cells), 10_002 + 2)
        self.assertEqual(len({c["row"] for c in cells}), len(cells))
        self.assertEqual(len({c["cell"] for c in cells}), len(cells))


if __name__ == "__main__":
    unittest.main()
