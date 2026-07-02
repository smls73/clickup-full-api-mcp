"""Write-safety gate for the ClickUp MCP server.

Mirrors the write-safety tiers in the global `clickup` skill
(~/.claude/skills/clickup/reference/write-safety.md):

- GREEN  (reads + single-task writes): pass through.
- RED    (deletions, webhooks, standing config): require an explicit
         per-call confirmation token. The caller must pass
         confirm="CONFIRM <tool_name>" — only after the human has given
         an explicit, named yes in chat.
- ADMIN  (workspace membership, guests, permissions): always blocked.
         These are human-only actions. Set CLICKUP_MCP_ALLOW_ADMIN=true
         to unblock (not recommended).
"""

import os
from typing import Any

# Deletions and standing-config changes: need a per-call confirm token.
RED_TOOLS = {
    "delete_space",
    "delete_folder",
    "delete_list",
    "delete_task",
    "delete_checklist",
    "delete_checklist_item",
    "delete_dependency",
    "delete_task_link",
    "delete_comment",
    "delete_space_tag",
    "delete_goal",
    "delete_key_result",
    "delete_time_entry",
    "delete_view",
    "delete_user_group",
    "create_webhook",
    "update_webhook",
    "delete_webhook",
    # Outbound messaging: human must approve the exact text + account first.
    "send_chat_message",
}

# Workspace access control: always blocked (human-only).
ADMIN_TOOLS = {
    "invite_user_to_workspace",
    "update_user",
    "remove_user_from_workspace",
    "invite_guest_to_workspace",
    "update_guest",
    "remove_guest_from_workspace",
    "add_guest_to_task",
    "remove_guest_from_task",
    "add_guest_to_list",
    "remove_guest_from_list",
    "add_guest_to_folder",
    "remove_guest_from_folder",
}

CONFIRM_KEY = "confirm"


class SafetyError(Exception):
    """Raised when a call is blocked by the write-safety gate."""


def check(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Gate a tool call. Returns the arguments to forward (confirm key
    stripped). Raises SafetyError when the call must not proceed."""
    if name in ADMIN_TOOLS:
        if os.environ.get("CLICKUP_MCP_ALLOW_ADMIN", "").lower() != "true":
            raise SafetyError(
                f"'{name}' is blocked: workspace membership/guest/permission "
                "changes are human-only. Scott must do this in the ClickUp UI."
            )
        return arguments

    # Doc page rewrite: 'replace' flattens live task chips -> RED.
    # 'append'/'prepend' stay green.
    if name == "update_doc_page" and arguments.get("content_edit_mode", "append") == "replace":
        expected = f"CONFIRM {name}"
        if arguments.get(CONFIRM_KEY) != expected:
            raise SafetyError(
                "update_doc_page with content_edit_mode='replace' REWRITES the page "
                "and flattens live task chips. Default to 'append'. A replace needs "
                "Scott's explicit, named confirmation, then retry with "
                f'{CONFIRM_KEY}="{expected}".'
            )
        return {k: v for k, v in arguments.items() if k != CONFIRM_KEY}

    if name in RED_TOOLS:
        expected = f"CONFIRM {name}"
        if arguments.get(CONFIRM_KEY) != expected:
            raise SafetyError(
                f"'{name}' is a RED-tier (destructive/standing-config) action. "
                "It requires an explicit, NAMED confirmation from Scott in chat "
                "for this specific item. After he confirms, retry with the "
                f'extra argument {CONFIRM_KEY}="{expected}". Never pre-fill '
                "this token without his explicit yes."
            )
        arguments = {k: v for k, v in arguments.items() if k != CONFIRM_KEY}

    return arguments
