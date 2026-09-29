"""Markdown for ClickUp comments.

ClickUp's v2 comment endpoints take either plain `comment_text` or a rich-text
`comment` array of blocks (https://developer.clickup.com/docs/comment-formatting).
This module turns the markdown a model already writes into those blocks, so a
comment written like a task description comes out formatted the same way.

Text formats (attributes on the text block):
- [text](url)            {"link": url}        (the rules below are unchanged from the links-only version)
- **bold** or __bold__   {"bold": true}
- *italic* or _italic_   {"italic": true}     (***both*** gives both)
- `code`                 {"code": true}

Line formats (attributes on the "\\n" block that ends the line, as ClickUp stores them):
- ``` fenced block ```   {"code-block": {"code-block": "plain"}} on every code line
- - item / * item / + item            {"list": {"list": "bullet"}}
- 1. item / 1) item                   {"list": {"list": "ordered"}}  (ClickUp numbers the items)
- - [ ] item / - [x] item             {"list": {"list": "unchecked" | "checked"}}
  Two leading spaces per level add {"indent": n}.
- A pipe table (header row, then a --- separator row, then rows):
  one {"text": "\\n", "attributes": {"table-col": {"width": "150"}}} per column, then each
  cell's text followed by {"text": "\\n", "attributes": {"table-cell-line": {"row": id,
  "cell": id-N, "colspan": "1", "rowspan": "1"}}}. This is the shape of the tables Scott and
  Irina typed by hand in ClickUp (read back from real comments, 2025-02 to 2026-06); the
  docs page does not describe tables.

Link rules (unchanged):
- Only web links convert: http or https, with a real host (checked by urlsplit),
  no whitespace or control characters. Anything else stays literal text.
- A URL may contain balanced parentheses: [Foo](https://x.org/wiki/Foo_(bar)).
  It may not contain a raw "[" or "]" (percent-encode them).
- A label may not contain "[", "]" or a newline. The label is used as typed.
- Not converted, left exactly as typed: an escaped character (\\[text](url), \\*),
  an image (![alt](url)), anything inside `inline code` or a ``` fenced block.
- Empty label: [](https://x) shows the URL itself as the link text.

General rules:
- Anything the converter does not understand stays literal text; nothing is dropped
  except the markdown markers it converted (and a fence line's language name).
  Examples that stay literal: headings, quotes, images, ~~strike~~, an unclosed ``` fence
  (everything after it), an unmatched * or _. A table row with more cells than its header
  ends the table; that row and what follows are handled as ordinary lines.
- A bare http(s) URL is never split by emphasis (snake_case_names are safe too).
- Line breaks become their own {"text": "\\n"} blocks. CRLF is normalized to LF.
- Emoji and every other character pass through unchanged as text.
- Text with NO formatting at all is sent as plain `comment_text`, exactly as before.
- Linear time: every scan stops at a known boundary, so hostile input stays fast.
"""

import re
from typing import Any, Optional
from urllib.parse import urlsplit

COMMENT_INPUT_KEYS = ("comment_text", "markdown_text")

TABLE_COL_WIDTH = "150"
CODE_LINE = {"code-block": {"code-block": "plain"}}

_BULLET = re.compile(r"( *)[-*+] (.*)")
_CHECK = re.compile(r"( *)[-*+] \[([ xX])\](?: (.*))?")
_ORDERED = re.compile(r"( *)\d{1,9}[.)] (.*)")
_SEP_CELL = re.compile(r":?-+:?")
_INLINE_MARKUP = re.compile(r"[\\`\[*_]")  # without one of these, a line has no inline format


def is_web_url(url: str) -> bool:
    """True for an http(s) URL with a host and no whitespace/control characters."""
    if not url or any(ch.isspace() or ord(ch) < 32 or ord(ch) == 127 for ch in url):
        return False
    try:
        parts = urlsplit(url)
        host = parts.hostname
    except ValueError:
        return False
    return parts.scheme.lower() in ("http", "https") and bool(host)


def _parse_link(text: str, start: int, web_only: bool = True) -> Optional[tuple[str, str, int]]:
    """At text[start] == '[', try to read [label](url).

    Returns (label, url, index_after_closing_paren) or None. Every scan stops at
    the next '[' so the total work over a whole text stays linear. With web_only
    False (used only to find an image's full extent) any destination is accepted.
    """
    n = len(text)
    pos = start + 1
    while pos < n and text[pos] not in "[]\n":
        pos += 1
    if pos >= n or text[pos] != "]":
        return None
    label = text[start + 1 : pos]
    if pos + 1 >= n or text[pos + 1] != "(":
        return None
    url_start = pos + 2
    depth = 1
    pos = url_start
    while pos < n:
        ch = text[pos]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                break
        elif ch in "[]" or ch.isspace():
            return None
        pos += 1
    else:
        return None  # no closing parenthesis
    url = text[url_start:pos]
    if web_only and not is_web_url(url):
        return None
    return label, url, pos + 1


# ---------- inline formats (one line, or one table cell) ----------

def _inline(s: str) -> list[dict[str, Any]]:
    """One line of text (no newline) -> text blocks with link/bold/italic/code attributes."""
    if not _INLINE_MARKUP.search(s):  # fast path: nothing here can format
        return [{"text": s, "attributes": {}}] if s else []
    n = len(s)
    # atoms: ("t", text, extra_attrs) | ("d", char, run_length, atom_state)
    atoms: list[list[Any]] = []
    buf: list[str] = []
    # Every backtick run on the line, found once: start -> (length, start of the next run of the
    # same length, or -1). A code span closes at the next run of exactly its length.
    runs: dict[int, tuple[int, int]] = {}
    starts: list[tuple[int, int]] = []
    p = s.find("`")
    while p != -1:
        q = p
        while q < n and s[q] == "`":
            q += 1
        starts.append((p, q - p))
        p = s.find("`", q)
    next_of_len: dict[int, int] = {}
    for p, k in reversed(starts):
        runs[p] = (k, next_of_len.get(k, -1))
        next_of_len[k] = p

    def flush() -> None:
        if buf:
            atoms.append(["t", "".join(buf), {}])
            buf.clear()

    i = 0
    while i < n:
        ch = s[i]
        if ch == "\\" and i + 1 < n:  # escaped character: keep both, never markup
            buf.append(s[i : i + 2])
            i += 2
            continue
        if ch == "`":  # inline code span: through the next run of the same length
            if i not in runs:  # the rest of a run whose first backtick was escaped: literal
                j = i
                while j < n and s[j] == "`":
                    j += 1
                buf.append(s[i:j])
                i = j
                continue
            k, close = runs[i]
            if close == -1:
                buf.append("`" * k)
                i += k
                continue
            body = s[i + k : close]
            if len(body) >= 2 and body[0] == " " and body[-1] == " " and body.strip(" "):
                body = body[1:-1]
            flush()
            if body:
                atoms.append(["t", body, {"code": True}])
            i = close + k
            continue
        if ch == "!" and i + 1 < n and s[i + 1] == "[":  # an image stays literal, label included
            image = _parse_link(s, i + 1, web_only=False)
            if image is not None:
                buf.append(s[i : image[2]])
                i = image[2]
                continue
        if ch == "[" and not (i > 0 and s[i - 1] == "!"):
            parsed = _parse_link(s, i)
            if parsed is not None:
                flush()
                label, url, i = parsed
                atoms.append(["t", label or url, {"link": url}])
                continue
        if ch in "hH" and (i == 0 or not s[i - 1].isalnum()) and (
            s[i : i + 8].lower() == "https://" or s[i : i + 7].lower() == "http://"
        ):
            # A bare URL is literal text; emphasis never splits it. It ends at whitespace, "[" or "*".
            j = i
            while j < n and not s[j].isspace() and s[j] not in "[*":
                j += 1
            buf.append(s[i:j])
            i = j
            continue
        if ch in "*_":
            k = 1
            while i + k < n and s[i + k] == ch:
                k += 1
            prev = s[i - 1] if i > 0 else None
            nxt = s[i + k] if i + k < n else None
            can_open = nxt is not None and not nxt.isspace()
            can_close = prev is not None and not prev.isspace()
            if ch == "_":  # intraword underscores never format (snake_case)
                can_open = can_open and not (prev is not None and prev.isalnum())
                can_close = can_close and not (nxt is not None and nxt.isalnum())
            if k <= 3 and (can_open or can_close):
                flush()
                atoms.append(["d", ch, k, {"open": can_open, "close": can_close, "pair": None}])
            else:
                buf.append(ch * k)
            i += k
            continue
        buf.append(ch)
        i += 1
    flush()

    # Pair delimiter runs of the same character and length. Openers left open inside a
    # matched pair are dropped from the stack (they stay literal), so pairs never cross.
    stack: list[int] = []  # atom indexes of open runs
    by_kind: dict[tuple[str, int], list[int]] = {}  # kind -> positions in stack
    for idx, atom in enumerate(atoms):
        if atom[0] != "d":
            continue
        kind = (atom[1], atom[2])
        st = atom[3]
        if st["close"] and by_kind.get(kind):
            depth = by_kind[kind][-1]
            while len(stack) > depth + 1:  # unmatched openers inside: literal
                inner = stack.pop()
                by_kind[(atoms[inner][1], atoms[inner][2])].pop()
            opener = stack.pop()
            by_kind[kind].pop()
            atoms[opener][3]["pair"] = "open"
            st["pair"] = "close"
            continue
        if st["open"]:
            by_kind.setdefault(kind, []).append(len(stack))
            stack.append(idx)

    blocks: list[dict[str, Any]] = []
    bold = italic = 0

    def emit(text: str, extra: dict[str, Any]) -> None:
        attrs: dict[str, Any] = {}
        if bold:
            attrs["bold"] = True
        if italic:
            attrs["italic"] = True
        attrs.update(extra)
        if blocks and "link" not in attrs and blocks[-1]["attributes"] == attrs:
            blocks[-1]["text"] += text
        else:
            blocks.append({"text": text, "attributes": attrs})

    for atom in atoms:
        if atom[0] == "t":
            emit(atom[1], atom[2])
            continue
        _, ch, k, st = atom
        step = 1 if st["pair"] == "open" else (-1 if st["pair"] == "close" else 0)
        if step == 0:
            emit(ch * k, {})
            continue
        if k in (2, 3):
            bold += step
        if k in (1, 3):
            italic += step
    return blocks


# ---------- tables ----------

def _has_pipe(line: str) -> bool:
    i = line.find("|")
    while i != -1:
        if i == 0 or line[i - 1] != "\\":
            return True
        i = line.find("|", i + 1)
    return False


def _cells(line: str) -> list[str]:
    """Split a table row on unescaped pipes; an escaped \\| becomes a plain |."""
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    cells, cur, i = [], [], 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s) and s[i + 1] == "|":
            cur.append("|")
            i += 2
            continue
        if s[i] == "|":
            cells.append("".join(cur).strip())
            cur = []
        else:
            cur.append(s[i])
        i += 1
    cells.append("".join(cur).strip())
    return cells


def _is_separator(line: str, ncols: int) -> bool:
    if not _has_pipe(line):
        return False
    cells = _cells(line)
    return len(cells) == ncols and all(_SEP_CELL.fullmatch(c) for c in cells)


def _row_id(row_no: int) -> str:
    """row-XXXX from one counter per comment, so no two rows in a comment share an id."""
    n, digits = row_no, "0123456789abcdefghijklmnopqrstuvwxyz"
    out = ""
    while True:
        n, r = divmod(n, 36)
        out = digits[r] + out
        if n == 0:
            break
    return "row-" + out.rjust(4, "0")


def _table_blocks(rows: list[list[str]], ncols: int, first_row_no: int) -> list[dict[str, Any]]:
    blocks = [{"text": "\n", "attributes": {"table-col": {"width": TABLE_COL_WIDTH}}} for _ in range(ncols)]
    for r, cells in enumerate(rows):
        rid = _row_id(first_row_no + r)
        for c in range(ncols):
            text = cells[c] if c < len(cells) else ""
            if text:
                blocks.extend(_inline(text))
            blocks.append({"text": "\n", "attributes": {"table-cell-line": {
                "row": rid, "cell": f"{rid}-{c + 1}", "colspan": "1", "rowspan": "1"}}})
    return blocks


# ---------- whole text ----------

def _plain_lines(lines: list[str], last_has_newline: bool) -> list[dict[str, Any]]:
    """Literal lines, no parsing at all (used after an unclosed fence)."""
    out: list[dict[str, Any]] = []
    for k, line in enumerate(lines):
        if line:
            out.append({"text": line, "attributes": {}})
        if k < len(lines) - 1 or last_has_newline:
            out.append({"text": "\n", "attributes": {}})
    return out


def _indent(spaces: str) -> dict[str, Any]:
    level = len(spaces) // 2
    return {"indent": level} if level else {}


def markdown_to_comment(text: str) -> list[dict[str, Any]]:
    """Turn markdown text into ClickUp comment blocks."""
    if not isinstance(text, str) or text == "":
        raise ValueError("markdown_text must be a non-empty string")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    last = len(lines) - 1
    blocks: list[dict[str, Any]] = []
    rows_used = 0  # one row counter for the whole comment
    i = 0
    while i <= last:
        line = lines[i]
        has_nl = i < last
        # Fenced code block: ``` ... ``` (closing fence at least as long, nothing else on its line).
        if line.startswith("```"):
            fence = len(line) - len(line.lstrip("`"))
            j = i + 1
            while j <= last and not (lines[j].rstrip(" ").strip("`") == "" and len(lines[j].rstrip(" ")) >= fence):
                j += 1
            if j > last:  # never closed: everything from here on stays literal
                blocks.extend(_plain_lines(lines[i:], False))
                break
            body = lines[i + 1 : j] or [""]
            for code_line in body:
                if code_line:
                    blocks.append({"text": code_line, "attributes": {}})
                blocks.append({"text": "\n", "attributes": dict(CODE_LINE)})
            i = j + 1
            continue
        # Pipe table: header row, separator row, then rows that contain a pipe. A row with
        # more cells than the header ends the table and is handled as an ordinary line.
        if _has_pipe(line) and i + 1 <= last:
            header = _cells(line)
            if _is_separator(lines[i + 1], len(header)):
                rows = [header]
                j = i + 2
                while j <= last and lines[j].strip() and _has_pipe(lines[j]):
                    cells = _cells(lines[j])
                    if len(cells) > len(header):
                        break
                    rows.append(cells)
                    j += 1
                blocks.extend(_table_blocks(rows, len(header), rows_used))
                rows_used += len(rows)
                i = j
                continue
        m = _CHECK.fullmatch(line)
        if m:
            state = "checked" if m.group(2) in "xX" else "unchecked"
            blocks.extend(_inline(m.group(3) or ""))
            blocks.append({"text": "\n", "attributes": {"list": {"list": state}, **_indent(m.group(1))}})
            i += 1
            continue
        m = _BULLET.fullmatch(line) or _ORDERED.fullmatch(line)
        if m:
            kind = "bullet" if m.re is _BULLET else "ordered"
            blocks.extend(_inline(m.group(2)))
            blocks.append({"text": "\n", "attributes": {"list": {"list": kind}, **_indent(m.group(1))}})
            i += 1
            continue
        blocks.extend(_inline(line))
        if has_nl:
            blocks.append({"text": "\n", "attributes": {}})
        i += 1
    return blocks


def has_format(blocks: list[dict[str, Any]]) -> bool:
    return any(b.get("attributes") for b in blocks)


def has_link(blocks: list[dict[str, Any]]) -> bool:
    return any("link" in b.get("attributes", {}) for b in blocks)


def comment_body(args: dict[str, Any]) -> dict[str, Any]:
    """Pick the comment body from exactly one of comment_text | markdown_text.

    Returns {"comment_text": str} or {"comment": [blocks]}. Raises ValueError on
    zero or both inputs, so a caller never gets a silently dropped field.
    """
    if "comment" in args:  # refused even when null: this tool has no raw-block input
        raise ValueError("Raw comment blocks are not accepted by this tool; use markdown_text for formatting.")
    given = [k for k in COMMENT_INPUT_KEYS if args.get(k) is not None]
    if len(given) != 1:
        raise ValueError(
            "Exactly one of comment_text (plain) or markdown_text (markdown: links, bold, italic, "
            f"code, lists, checklists, tables) is accepted; got {given or 'none'}."
        )
    if given[0] == "comment_text":
        return {"comment_text": args["comment_text"]}
    blocks = markdown_to_comment(args["markdown_text"])
    if not has_format(blocks):
        # No formatting in it: send exactly what comment_text would have sent.
        return {"comment_text": args["markdown_text"]}
    return {"comment": blocks}
