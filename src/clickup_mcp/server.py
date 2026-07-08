"""ClickUp MCP Server - Comprehensive API coverage."""

import json
from typing import Any

from mcp.server import Server
from mcp.types import TextContent, Tool

from .client import ClickUpClient
from .safety import SafetyError, check as safety_check

# Initialize server
server = Server("clickup-mcp")

# Client instance (initialized on first use)
_client: ClickUpClient | None = None


def get_client() -> ClickUpClient:
    """Get or create the ClickUp client."""
    global _client
    if _client is None:
        _client = ClickUpClient()
    return _client


# ===== Tool Definitions =====

TOOLS = [
    # ----- Authorization -----
    Tool(
        name="get_authorized_user",
        description="Get the currently authenticated user's information",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    # ----- Workspaces -----
    Tool(
        name="get_workspaces",
        description="Get all workspaces (teams) the user has access to",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="get_workspace_seats",
        description="Get seat information for a workspace",
        inputSchema={
            "type": "object",
            "properties": {"team_id": {"type": "string", "description": "Workspace/Team ID"}},
            "required": ["team_id"],
        },
    ),
    Tool(
        name="get_workspace_plan",
        description="Get plan information for a workspace",
        inputSchema={
            "type": "object",
            "properties": {"team_id": {"type": "string", "description": "Workspace/Team ID"}},
            "required": ["team_id"],
        },
    ),
    # ----- Spaces -----
    Tool(
        name="get_spaces",
        description="Get all spaces in a workspace",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "archived": {"type": "boolean", "description": "Include archived spaces", "default": False},
            },
            "required": ["team_id"],
        },
    ),
    Tool(
        name="create_space",
        description="Create a new space in a workspace",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "name": {"type": "string", "description": "Space name"},
                "multiple_assignees": {"type": "boolean", "description": "Allow multiple assignees"},
                "features": {"type": "object", "description": "Space features configuration"},
            },
            "required": ["team_id", "name"],
        },
    ),
    Tool(
        name="get_space",
        description="Get a specific space",
        inputSchema={
            "type": "object",
            "properties": {"space_id": {"type": "string", "description": "Space ID"}},
            "required": ["space_id"],
        },
    ),
    Tool(
        name="update_space",
        description="Update a space",
        inputSchema={
            "type": "object",
            "properties": {
                "space_id": {"type": "string", "description": "Space ID"},
                "name": {"type": "string", "description": "New space name"},
                "color": {"type": "string", "description": "Space color"},
                "private": {"type": "boolean", "description": "Make space private"},
                "admin_can_manage": {"type": "boolean", "description": "Only admins can manage"},
                "multiple_assignees": {"type": "boolean", "description": "Allow multiple assignees"},
            },
            "required": ["space_id"],
        },
    ),
    Tool(
        name="delete_space",
        description="Delete a space",
        inputSchema={
            "type": "object",
            "properties": {"space_id": {"type": "string", "description": "Space ID"}},
            "required": ["space_id"],
        },
    ),
    # ----- Folders -----
    Tool(
        name="get_folders",
        description="Get all folders in a space",
        inputSchema={
            "type": "object",
            "properties": {
                "space_id": {"type": "string", "description": "Space ID"},
                "archived": {"type": "boolean", "description": "Include archived folders", "default": False},
            },
            "required": ["space_id"],
        },
    ),
    Tool(
        name="create_folder",
        description="Create a new folder in a space",
        inputSchema={
            "type": "object",
            "properties": {
                "space_id": {"type": "string", "description": "Space ID"},
                "name": {"type": "string", "description": "Folder name"},
            },
            "required": ["space_id", "name"],
        },
    ),
    Tool(
        name="get_folder",
        description="Get a specific folder",
        inputSchema={
            "type": "object",
            "properties": {"folder_id": {"type": "string", "description": "Folder ID"}},
            "required": ["folder_id"],
        },
    ),
    Tool(
        name="update_folder",
        description="Update a folder",
        inputSchema={
            "type": "object",
            "properties": {
                "folder_id": {"type": "string", "description": "Folder ID"},
                "name": {"type": "string", "description": "New folder name"},
            },
            "required": ["folder_id", "name"],
        },
    ),
    Tool(
        name="delete_folder",
        description="Delete a folder",
        inputSchema={
            "type": "object",
            "properties": {"folder_id": {"type": "string", "description": "Folder ID"}},
            "required": ["folder_id"],
        },
    ),
    # ----- Lists -----
    Tool(
        name="get_lists",
        description="Get all lists in a folder",
        inputSchema={
            "type": "object",
            "properties": {
                "folder_id": {"type": "string", "description": "Folder ID"},
                "archived": {"type": "boolean", "description": "Include archived lists", "default": False},
            },
            "required": ["folder_id"],
        },
    ),
    Tool(
        name="create_list",
        description="Create a new list in a folder",
        inputSchema={
            "type": "object",
            "properties": {
                "folder_id": {"type": "string", "description": "Folder ID"},
                "name": {"type": "string", "description": "List name"},
                "content": {"type": "string", "description": "List description"},
                "due_date": {"type": "integer", "description": "Due date timestamp (ms)"},
                "due_date_time": {"type": "boolean", "description": "Include time in due date"},
                "priority": {"type": "integer", "description": "Priority (1=urgent, 4=low)"},
                "assignee": {"type": "integer", "description": "Assignee user ID"},
                "status": {"type": "string", "description": "Status name"},
            },
            "required": ["folder_id", "name"],
        },
    ),
    Tool(
        name="get_folderless_lists",
        description="Get lists in a space that are not in any folder",
        inputSchema={
            "type": "object",
            "properties": {
                "space_id": {"type": "string", "description": "Space ID"},
                "archived": {"type": "boolean", "description": "Include archived lists", "default": False},
            },
            "required": ["space_id"],
        },
    ),
    Tool(
        name="create_folderless_list",
        description="Create a list directly in a space (not in a folder)",
        inputSchema={
            "type": "object",
            "properties": {
                "space_id": {"type": "string", "description": "Space ID"},
                "name": {"type": "string", "description": "List name"},
                "content": {"type": "string", "description": "List description"},
                "due_date": {"type": "integer", "description": "Due date timestamp (ms)"},
                "priority": {"type": "integer", "description": "Priority (1=urgent, 4=low)"},
                "assignee": {"type": "integer", "description": "Assignee user ID"},
                "status": {"type": "string", "description": "Status name"},
            },
            "required": ["space_id", "name"],
        },
    ),
    Tool(
        name="get_list",
        description="Get a specific list",
        inputSchema={
            "type": "object",
            "properties": {"list_id": {"type": "string", "description": "List ID"}},
            "required": ["list_id"],
        },
    ),
    Tool(
        name="update_list",
        description="Update a list",
        inputSchema={
            "type": "object",
            "properties": {
                "list_id": {"type": "string", "description": "List ID"},
                "name": {"type": "string", "description": "New list name"},
                "content": {"type": "string", "description": "New description"},
                "due_date": {"type": "integer", "description": "Due date timestamp (ms)"},
                "due_date_time": {"type": "boolean", "description": "Include time in due date"},
                "priority": {"type": "integer", "description": "Priority (1=urgent, 4=low)"},
                "assignee": {"type": "string", "description": "Assignee user ID or 'none'"},
                "unset_status": {"type": "boolean", "description": "Remove status"},
            },
            "required": ["list_id"],
        },
    ),
    Tool(
        name="delete_list",
        description="Delete a list",
        inputSchema={
            "type": "object",
            "properties": {"list_id": {"type": "string", "description": "List ID"}},
            "required": ["list_id"],
        },
    ),
    Tool(
        name="add_task_to_list",
        description="Add a task to an additional list (requires Tasks in Multiple List ClickApp)",
        inputSchema={
            "type": "object",
            "properties": {
                "list_id": {"type": "string", "description": "List ID to add task to"},
                "task_id": {"type": "string", "description": "Task ID"},
            },
            "required": ["list_id", "task_id"],
        },
    ),
    Tool(
        name="remove_task_from_list",
        description="Remove a task from a list",
        inputSchema={
            "type": "object",
            "properties": {
                "list_id": {"type": "string", "description": "List ID"},
                "task_id": {"type": "string", "description": "Task ID"},
            },
            "required": ["list_id", "task_id"],
        },
    ),
    # ----- Tasks -----
    Tool(
        name="get_tasks",
        description="Get tasks in a list with filtering options",
        inputSchema={
            "type": "object",
            "properties": {
                "list_id": {"type": "string", "description": "List ID"},
                "archived": {"type": "boolean", "description": "Include archived tasks", "default": False},
                "include_closed": {"type": "boolean", "description": "Include closed tasks", "default": False},
                "page": {"type": "integer", "description": "Page number (0-indexed)", "default": 0},
                "order_by": {"type": "string", "description": "Order by field (id, created, updated, due_date)"},
                "reverse": {"type": "boolean", "description": "Reverse order", "default": False},
                "subtasks": {"type": "boolean", "description": "Include subtasks", "default": False},
                "statuses": {"type": "array", "items": {"type": "string"}, "description": "Filter by statuses"},
                "assignees": {"type": "array", "items": {"type": "string"}, "description": "Filter by assignee IDs"},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "Filter by tag names"},
                "due_date_gt": {"type": "integer", "description": "Due date greater than (ms timestamp)"},
                "due_date_lt": {"type": "integer", "description": "Due date less than (ms timestamp)"},
                "date_created_gt": {"type": "integer", "description": "Created after (ms timestamp)"},
                "date_created_lt": {"type": "integer", "description": "Created before (ms timestamp)"},
                "date_updated_gt": {"type": "integer", "description": "Updated after (ms timestamp)"},
                "date_updated_lt": {"type": "integer", "description": "Updated before (ms timestamp)"},
                "date_done_gt": {"type": "integer", "description": "Completed after (ms timestamp)"},
                "date_done_lt": {"type": "integer", "description": "Completed before (ms timestamp)"},
                "watchers": {"type": "array", "items": {"type": "string"}, "description": "Filter by watcher user IDs"},
                "custom_fields": {"type": "array", "items": {"type": "object"}, "description": "Custom field filters: [{field_id, operator, value}] ('=' unsupported for Label fields)"},
                "custom_items": {"type": "array", "items": {"type": "integer"}, "description": "Filter by task type (0=task, 1=Milestone)"},
                "include_timl": {"type": "boolean", "description": "Include tasks whose home list is elsewhere (tasks in multiple lists)"},
                "include_markdown_description": {"type": "boolean", "description": "Include markdown description"},
            },
            "required": ["list_id"],
        },
    ),
    Tool(
        name="create_task",
        description="Create a new task in a list",
        inputSchema={
            "type": "object",
            "properties": {
                "list_id": {"type": "string", "description": "List ID"},
                "name": {"type": "string", "description": "Task name"},
                "description": {"type": "string", "description": "Task description (plain text)"},
                "markdown_content": {"type": "string", "description": "Markdown description (overrides description if both sent)"},
                "markdown_description": {"type": "string", "description": "DEPRECATED alias of markdown_content"},
                "assignees": {"type": "array", "items": {"type": "integer"}, "description": "Assignee user IDs"},
                "group_assignees": {"type": "array", "items": {"type": "string"}, "description": "User group IDs to assign"},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "Tag names"},
                "status": {"type": "string", "description": "Status name"},
                "priority": {"type": ["integer", "null"], "description": "Priority (1=urgent, 2=high, 3=normal, 4=low, null=none)"},
                "due_date": {"type": ["integer", "null"], "description": "Due date timestamp (ms), or null for none"},
                "due_date_time": {"type": "boolean", "description": "Include time in due date"},
                "time_estimate": {"type": "integer", "description": "Time estimate in milliseconds"},
                "start_date": {"type": ["integer", "null"], "description": "Start date timestamp (ms), or null for none"},
                "start_date_time": {"type": "boolean", "description": "Include time in start date"},
                "points": {"type": "number", "description": "Sprint points"},
                "notify_all": {"type": "boolean", "description": "Also notify the creator (assignees/watchers always notified)"},
                "parent": {"type": ["string", "null"], "description": "Parent task ID for subtasks (must be in the same list)"},
                "links_to": {"type": ["string", "null"], "description": "Task ID to create a linked dependency with"},
                "check_required_custom_fields": {"type": "boolean", "description": "Enforce required custom fields (API default: false)"},
                "custom_fields": {"type": "array", "description": "Custom field values: [{id, value}]"},
                "custom_item_id": {"type": ["number", "null"], "description": "Custom task type ID (0/omitted = standard Task)"},
                "archived": {"type": "boolean", "description": "Create as archived"},
            },
            "required": ["list_id", "name"],
        },
    ),
    Tool(
        name="get_task",
        description="Get a specific task by ID",
        inputSchema={
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task ID (or custom task ID)"},
                "custom_task_ids": {"type": "boolean", "description": "task_id is a custom ID", "default": False},
                "team_id": {"type": "string", "description": "Team ID (required with custom_task_ids)"},
                "include_subtasks": {"type": "boolean", "description": "Include subtasks", "default": False},
                "include_markdown_description": {"type": "boolean", "description": "Include markdown", "default": False},
            },
            "required": ["task_id"],
        },
    ),
    Tool(
        name="update_task",
        description="Update a task",
        inputSchema={
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task ID"},
                "custom_task_ids": {"type": "boolean", "description": "task_id is a custom ID", "default": False},
                "team_id": {"type": "string", "description": "Team ID (required with custom_task_ids)"},
                "name": {"type": "string", "description": "New task name"},
                "description": {"type": "string", "description": "New description (send a single space \" \" to clear it)"},
                "markdown_content": {"type": "string", "description": "New markdown description (overrides description if both sent)"},
                "markdown_description": {"type": "string", "description": "DEPRECATED alias of markdown_content"},
                "assignees": {"type": "object", "description": "Assignees to add/remove: {add: [ids], rem: [ids]}"},
                "group_assignees": {"type": "object", "description": "User groups to add/remove: {add: [uuids], rem: [uuids]}"},
                "watchers": {"type": "object", "description": "Watchers to add/remove: {add: [ids], rem: [ids]}"},
                "status": {"type": "string", "description": "New status"},
                "priority": {"type": ["integer", "null"], "description": "New priority (1-4), or null to CLEAR it"},
                "due_date": {"type": ["integer", "null"], "description": "New due date (ms timestamp), or null to CLEAR it"},
                "due_date_time": {"type": "boolean", "description": "Include time in due date"},
                "time_estimate": {"type": "integer", "description": "Time estimate in ms"},
                "start_date": {"type": ["integer", "null"], "description": "Start date (ms timestamp), or null to CLEAR it"},
                "start_date_time": {"type": "boolean", "description": "Include time in start date"},
                "points": {"type": "number", "description": "Sprint points"},
                "custom_item_id": {"type": ["integer", "null"], "description": "Task type (null/0=Task, 1=Milestone, other=custom type)"},
                "archived": {"type": "boolean", "description": "Archive/unarchive task"},
                "parent": {"type": "string", "description": "Move subtask to a different parent (cannot null-out a parent)"},
            },
            "required": ["task_id"],
        },
    ),
    Tool(
        name="delete_task",
        description="Delete a task",
        inputSchema={
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task ID"},
                "custom_task_ids": {"type": "boolean", "description": "task_id is a custom ID", "default": False},
                "team_id": {"type": "string", "description": "Team ID (required with custom_task_ids)"},
            },
            "required": ["task_id"],
        },
    ),
    Tool(
        name="get_filtered_team_tasks",
        description="Get filtered tasks across a workspace",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "page": {"type": "integer", "description": "Page number", "default": 0},
                "order_by": {"type": "string", "description": "Order by field"},
                "reverse": {"type": "boolean", "description": "Reverse order"},
                "subtasks": {"type": "boolean", "description": "Include subtasks"},
                "space_ids": {"type": "array", "items": {"type": "string"}, "description": "Filter by space IDs"},
                "project_ids": {"type": "array", "items": {"type": "string"}, "description": "Filter by folder IDs"},
                "list_ids": {"type": "array", "items": {"type": "string"}, "description": "Filter by list IDs"},
                "statuses": {"type": "array", "items": {"type": "string"}, "description": "Filter by statuses"},
                "include_closed": {"type": "boolean", "description": "Include closed tasks"},
                "assignees": {"type": "array", "items": {"type": "string"}, "description": "Filter by assignees"},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "Filter by tags"},
                "due_date_gt": {"type": "integer", "description": "Due date after (ms)"},
                "due_date_lt": {"type": "integer", "description": "Due date before (ms)"},
                "date_created_gt": {"type": "integer", "description": "Created after (ms)"},
                "date_created_lt": {"type": "integer", "description": "Created before (ms)"},
                "date_updated_gt": {"type": "integer", "description": "Updated after (ms)"},
                "date_updated_lt": {"type": "integer", "description": "Updated before (ms)"},
                "date_done_gt": {"type": "integer", "description": "Completed after (ms)"},
                "date_done_lt": {"type": "integer", "description": "Completed before (ms)"},
                "parent": {"type": "string", "description": "Parent task ID (returns its subtasks)"},
                "include_markdown_description": {"type": "boolean", "description": "Include markdown description"},
                "custom_fields": {"type": "array", "items": {"type": "object"}, "description": "Custom field filters: [{field_id, operator, value}] ('=' unsupported for Label fields)"},
                "custom_items": {"type": "array", "items": {"type": "integer"}, "description": "Filter by task type (0=task, 1=Milestone)"},
            },
            "required": ["team_id"],
        },
    ),
    Tool(
        name="get_task_time_in_status",
        description="Get time a task has spent in each status",
        inputSchema={
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task ID"},
                "custom_task_ids": {"type": "boolean", "description": "task_id is a custom ID"},
                "team_id": {"type": "string", "description": "Team ID (required with custom_task_ids)"},
            },
            "required": ["task_id"],
        },
    ),
    Tool(
        name="get_bulk_tasks_time_in_status",
        description="Get time multiple tasks have spent in each status",
        inputSchema={
            "type": "object",
            "properties": {
                "task_ids": {"type": "array", "items": {"type": "string"}, "description": "Task IDs"},
                "custom_task_ids": {"type": "boolean", "description": "task_ids are custom IDs"},
                "team_id": {"type": "string", "description": "Team ID (required with custom_task_ids)"},
            },
            "required": ["task_ids"],
        },
    ),
    Tool(
        name="create_task_from_template",
        description="Create a task from a template",
        inputSchema={
            "type": "object",
            "properties": {
                "list_id": {"type": "string", "description": "List ID to create task in"},
                "template_id": {"type": "string", "description": "Template ID"},
                "name": {"type": "string", "description": "Task name"},
            },
            "required": ["list_id", "template_id", "name"],
        },
    ),
    Tool(
        name="move_task",
        description=(
            "Move a task to a new home list (API v3). RED tier: statuses/custom fields can be "
            "clobbered by the remap, so it requires the confirm token. For tasks in multiple "
            "lists only the HOME list changes."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "task_id": {"type": "string", "description": "Task ID (custom task IDs not supported)"},
                "list_id": {"type": "string", "description": "Destination list ID (the new home list)"},
                "move_custom_fields": {"type": "boolean", "description": "Add the current list's custom fields to the new list"},
                "custom_fields_to_move": {"type": "array", "items": {"type": "string"}, "description": "Specific custom field IDs to move"},
                "status_mappings": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "[{source_status_id, destination_status_id}] — required if the current status doesn't exist in the new list",
                },
            },
            "required": ["team_id", "task_id", "list_id"],
        },
    ),
    Tool(
        name="merge_tasks",
        description=(
            "Merge source tasks INTO a target task — the target survives, sources are absorbed. "
            "CANNOT BE UNDONE. RED tier: requires the confirm token. Custom task IDs not supported."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "TARGET task ID (survives the merge)"},
                "source_task_ids": {"type": "array", "items": {"type": "string"}, "description": "Task IDs merged INTO the target (absorbed)"},
            },
            "required": ["task_id", "source_task_ids"],
        },
    ),
    Tool(
        name="update_time_estimates_by_user",
        description=(
            "Set per-user time estimates on a task for the named assignees only (others untouched). "
            "API v3, Business plan+. Max 10 per call."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "task_id": {"type": "string", "description": "Task ID"},
                "estimates": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "[{assignee: <user id int or 'unassigned'>, time: <ms, >=0>}] (max 10)",
                },
            },
            "required": ["team_id", "task_id", "estimates"],
        },
    ),
    Tool(
        name="replace_time_estimates_by_user",
        description=(
            "REPLACE ALL per-user time estimates on a task — any estimate not re-sent is REMOVED. "
            "RED tier: requires the confirm token. API v3, Business plan+."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "task_id": {"type": "string", "description": "Task ID"},
                "estimates": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "The FULL desired set: [{assignee, time}] (max 10). Anything omitted is wiped.",
                },
            },
            "required": ["team_id", "task_id", "estimates"],
        },
    ),
    # ----- Task Checklists -----
    Tool(
        name="create_checklist",
        description="Create a checklist on a task",
        inputSchema={
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task ID"},
                "name": {"type": "string", "description": "Checklist name"},
                "custom_task_ids": {"type": "boolean", "description": "task_id is a custom ID"},
                "team_id": {"type": "string", "description": "Team ID (required with custom_task_ids)"},
            },
            "required": ["task_id", "name"],
        },
    ),
    Tool(
        name="update_checklist",
        description="Update a checklist name",
        inputSchema={
            "type": "object",
            "properties": {
                "checklist_id": {"type": "string", "description": "Checklist ID"},
                "name": {"type": "string", "description": "New checklist name"},
            },
            "required": ["checklist_id", "name"],
        },
    ),
    Tool(
        name="delete_checklist",
        description="Delete a checklist",
        inputSchema={
            "type": "object",
            "properties": {"checklist_id": {"type": "string", "description": "Checklist ID"}},
            "required": ["checklist_id"],
        },
    ),
    Tool(
        name="create_checklist_item",
        description="Create an item in a checklist",
        inputSchema={
            "type": "object",
            "properties": {
                "checklist_id": {"type": "string", "description": "Checklist ID"},
                "name": {"type": "string", "description": "Item name"},
                "assignee": {"type": "string", "description": "Assignee user ID"},
            },
            "required": ["checklist_id", "name"],
        },
    ),
    Tool(
        name="update_checklist_item",
        description="Update a checklist item",
        inputSchema={
            "type": "object",
            "properties": {
                "checklist_id": {"type": "string", "description": "Checklist ID"},
                "checklist_item_id": {"type": "string", "description": "Checklist item ID"},
                "name": {"type": "string", "description": "New item name"},
                "resolved": {"type": "boolean", "description": "Mark as resolved/unresolved"},
                "assignee": {"type": "string", "description": "Assignee user ID"},
                "parent": {"type": "string", "description": "Parent checklist item ID (for nesting)"},
            },
            "required": ["checklist_id", "checklist_item_id"],
        },
    ),
    Tool(
        name="delete_checklist_item",
        description="Delete a checklist item",
        inputSchema={
            "type": "object",
            "properties": {
                "checklist_id": {"type": "string", "description": "Checklist ID"},
                "checklist_item_id": {"type": "string", "description": "Checklist item ID"},
            },
            "required": ["checklist_id", "checklist_item_id"],
        },
    ),
    # ----- Task Relationships -----
    Tool(
        name="add_dependency",
        description="Add a dependency between tasks",
        inputSchema={
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task ID"},
                "depends_on": {"type": "string", "description": "Task ID this task depends on"},
                "dependency_of": {"type": "string", "description": "Task ID that depends on this task"},
                "custom_task_ids": {"type": "boolean", "description": "task_ids are custom IDs"},
                "team_id": {"type": "string", "description": "Team ID (required with custom_task_ids)"},
            },
            "required": ["task_id"],
        },
    ),
    Tool(
        name="delete_dependency",
        description="Remove a dependency between tasks",
        inputSchema={
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task ID"},
                "depends_on": {"type": "string", "description": "Task ID this task depends on"},
                "dependency_of": {"type": "string", "description": "Task ID that depends on this task"},
                "custom_task_ids": {"type": "boolean", "description": "task_ids are custom IDs"},
                "team_id": {"type": "string", "description": "Team ID (required with custom_task_ids)"},
            },
            "required": ["task_id"],
        },
    ),
    Tool(
        name="add_task_link",
        description="Link two tasks together",
        inputSchema={
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task ID"},
                "links_to": {"type": "string", "description": "Task ID to link to"},
                "custom_task_ids": {"type": "boolean", "description": "task_ids are custom IDs"},
                "team_id": {"type": "string", "description": "Team ID (required with custom_task_ids)"},
            },
            "required": ["task_id", "links_to"],
        },
    ),
    Tool(
        name="delete_task_link",
        description="Unlink two tasks",
        inputSchema={
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task ID"},
                "links_to": {"type": "string", "description": "Task ID to unlink"},
                "custom_task_ids": {"type": "boolean", "description": "task_ids are custom IDs"},
                "team_id": {"type": "string", "description": "Team ID (required with custom_task_ids)"},
            },
            "required": ["task_id", "links_to"],
        },
    ),
    # ----- Comments -----
    Tool(
        name="get_task_comments",
        description="Get comments on a task",
        inputSchema={
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task ID"},
                "custom_task_ids": {"type": "boolean", "description": "task_id is a custom ID"},
                "team_id": {"type": "string", "description": "Team ID (required with custom_task_ids)"},
                "start": {"type": "integer", "description": "Start timestamp for pagination"},
                "start_id": {"type": "string", "description": "Start comment ID for pagination"},
            },
            "required": ["task_id"],
        },
    ),
    Tool(
        name="create_task_comment",
        description="Create a comment on a task",
        inputSchema={
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task ID"},
                "comment_text": {"type": "string", "description": "Comment text"},
                "assignee": {"type": "string", "description": "Assign comment to user ID"},
                "notify_all": {"type": "boolean", "description": "Notify all assignees", "default": False},
                "custom_task_ids": {"type": "boolean", "description": "task_id is a custom ID"},
                "team_id": {"type": "string", "description": "Team ID (required with custom_task_ids)"},
            },
            "required": ["task_id", "comment_text"],
        },
    ),
    Tool(
        name="get_list_comments",
        description="Get comments on a list",
        inputSchema={
            "type": "object",
            "properties": {
                "list_id": {"type": "string", "description": "List ID"},
                "start": {"type": "integer", "description": "Start timestamp for pagination"},
                "start_id": {"type": "string", "description": "Start comment ID for pagination"},
            },
            "required": ["list_id"],
        },
    ),
    Tool(
        name="create_list_comment",
        description="Create a comment on a list",
        inputSchema={
            "type": "object",
            "properties": {
                "list_id": {"type": "string", "description": "List ID"},
                "comment_text": {"type": "string", "description": "Comment text"},
                "assignee": {"type": "string", "description": "Assign comment to user ID"},
                "notify_all": {"type": "boolean", "description": "Notify all assignees", "default": False},
            },
            "required": ["list_id", "comment_text"],
        },
    ),
    Tool(
        name="get_chat_view_comments",
        description="Get comments in a chat view",
        inputSchema={
            "type": "object",
            "properties": {
                "view_id": {"type": "string", "description": "View ID"},
                "start": {"type": "integer", "description": "Start timestamp for pagination"},
                "start_id": {"type": "string", "description": "Start comment ID for pagination"},
            },
            "required": ["view_id"],
        },
    ),
    Tool(
        name="create_chat_view_comment",
        description="Create a comment in a chat view",
        inputSchema={
            "type": "object",
            "properties": {
                "view_id": {"type": "string", "description": "View ID"},
                "comment_text": {"type": "string", "description": "Comment text"},
                "notify_all": {"type": "boolean", "description": "Notify all", "default": False},
            },
            "required": ["view_id", "comment_text"],
        },
    ),
    Tool(
        name="update_comment",
        description="Update a comment",
        inputSchema={
            "type": "object",
            "properties": {
                "comment_id": {"type": "string", "description": "Comment ID"},
                "comment_text": {"type": "string", "description": "New comment text"},
                "resolved": {"type": "boolean", "description": "Mark as resolved/unresolved"},
            },
            "required": ["comment_id", "comment_text"],
        },
    ),
    Tool(
        name="delete_comment",
        description="Delete a comment",
        inputSchema={
            "type": "object",
            "properties": {"comment_id": {"type": "string", "description": "Comment ID"}},
            "required": ["comment_id"],
        },
    ),
    Tool(
        name="get_threaded_comments",
        description="Get replies to a comment",
        inputSchema={
            "type": "object",
            "properties": {
                "comment_id": {"type": "string", "description": "Parent comment ID"},
                "start": {"type": "integer", "description": "Start timestamp for pagination"},
                "start_id": {"type": "string", "description": "Start comment ID for pagination"},
            },
            "required": ["comment_id"],
        },
    ),
    Tool(
        name="create_threaded_comment",
        description="Reply to a comment",
        inputSchema={
            "type": "object",
            "properties": {
                "comment_id": {"type": "string", "description": "Parent comment ID"},
                "comment_text": {"type": "string", "description": "Reply text"},
                "notify_all": {"type": "boolean", "description": "Notify all", "default": False},
            },
            "required": ["comment_id", "comment_text"],
        },
    ),
    # ----- Attachments -----
    Tool(
        name="create_task_attachment",
        description="Upload an attachment to a task",
        inputSchema={
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task ID"},
                "file_path": {"type": "string", "description": "Local path to the file"},
                "filename": {"type": "string", "description": "Override filename"},
                "custom_task_ids": {"type": "boolean", "description": "task_id is a custom ID"},
                "team_id": {"type": "string", "description": "Team ID (required with custom_task_ids)"},
            },
            "required": ["task_id", "file_path"],
        },
    ),
    Tool(
        name="get_attachments",
        description=(
            "Get attachments on a task or a Files custom field (API v3). "
            "entity_type='tasks' (default) with entity_id=<task_id> for a task; "
            "entity_type='custom_fields' with entity_id=<field_id> for a Files field."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "entity_id": {"type": "string", "description": "Task ID or Files-custom-field ID"},
                "entity_type": {"type": "string", "description": "'tasks' (task, default) or 'custom_fields'", "default": "tasks"},
                "cursor": {"type": "string", "description": "Pagination cursor (optional)"},
                "limit": {"type": "integer", "description": "Page size 1-100 (default 50)"},
            },
            "required": ["team_id", "entity_id"],
        },
    ),
    Tool(
        name="create_attachment_v3",
        description=(
            "Upload a file to a task or a Files custom field (API v3). For a Files field, "
            "follow with set_custom_field_value to associate the upload."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "entity_id": {"type": "string", "description": "Task ID or Files-custom-field ID"},
                "file_path": {"type": "string", "description": "Local path to the file"},
                "entity_type": {"type": "string", "description": "'tasks' (task, default) or 'custom_fields'", "default": "tasks"},
                "filename": {"type": "string", "description": "Override filename"},
            },
            "required": ["team_id", "entity_id", "file_path"],
        },
    ),
    # ----- Custom Fields -----
    Tool(
        name="get_list_custom_fields",
        description="Get custom fields available on a list",
        inputSchema={
            "type": "object",
            "properties": {"list_id": {"type": "string", "description": "List ID"}},
            "required": ["list_id"],
        },
    ),
    Tool(
        name="get_folder_custom_fields",
        description="Get custom fields available on a folder",
        inputSchema={
            "type": "object",
            "properties": {"folder_id": {"type": "string", "description": "Folder ID"}},
            "required": ["folder_id"],
        },
    ),
    Tool(
        name="get_space_custom_fields",
        description="Get custom fields available on a space",
        inputSchema={
            "type": "object",
            "properties": {"space_id": {"type": "string", "description": "Space ID"}},
            "required": ["space_id"],
        },
    ),
    Tool(
        name="get_workspace_custom_fields",
        description="Get all custom fields in a workspace",
        inputSchema={
            "type": "object",
            "properties": {"team_id": {"type": "string", "description": "Workspace/Team ID"}},
            "required": ["team_id"],
        },
    ),
    Tool(
        name="set_custom_field_value",
        description="Set a custom field value on a task",
        inputSchema={
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task ID"},
                "field_id": {"type": "string", "description": "Custom field ID"},
                "value": {"description": "Field value (type depends on field type)"},
                "custom_task_ids": {"type": "boolean", "description": "task_id is a custom ID"},
                "team_id": {"type": "string", "description": "Team ID (required with custom_task_ids)"},
            },
            "required": ["task_id", "field_id", "value"],
        },
    ),
    Tool(
        name="remove_custom_field_value",
        description="Remove a custom field value from a task",
        inputSchema={
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task ID"},
                "field_id": {"type": "string", "description": "Custom field ID"},
                "custom_task_ids": {"type": "boolean", "description": "task_id is a custom ID"},
                "team_id": {"type": "string", "description": "Team ID (required with custom_task_ids)"},
            },
            "required": ["task_id", "field_id"],
        },
    ),
    # ----- Custom Task Types -----
    Tool(
        name="get_custom_task_types",
        description="Get custom task types in a workspace",
        inputSchema={
            "type": "object",
            "properties": {"team_id": {"type": "string", "description": "Workspace/Team ID"}},
            "required": ["team_id"],
        },
    ),
    # ----- Tags -----
    Tool(
        name="get_space_tags",
        description="Get all tags in a space",
        inputSchema={
            "type": "object",
            "properties": {"space_id": {"type": "string", "description": "Space ID"}},
            "required": ["space_id"],
        },
    ),
    Tool(
        name="create_space_tag",
        description="Create a tag in a space",
        inputSchema={
            "type": "object",
            "properties": {
                "space_id": {"type": "string", "description": "Space ID"},
                "name": {"type": "string", "description": "Tag name"},
                "tag_bg": {"type": "string", "description": "Background color hex"},
                "tag_fg": {"type": "string", "description": "Foreground color hex"},
            },
            "required": ["space_id", "name"],
        },
    ),
    Tool(
        name="update_space_tag",
        description="Update a tag in a space",
        inputSchema={
            "type": "object",
            "properties": {
                "space_id": {"type": "string", "description": "Space ID"},
                "tag_name": {"type": "string", "description": "Current tag name"},
                "new_name": {"type": "string", "description": "New tag name"},
                "tag_bg": {"type": "string", "description": "Background color hex"},
                "tag_fg": {"type": "string", "description": "Foreground color hex"},
            },
            "required": ["space_id", "tag_name", "new_name"],
        },
    ),
    Tool(
        name="delete_space_tag",
        description="Delete a tag from a space",
        inputSchema={
            "type": "object",
            "properties": {
                "space_id": {"type": "string", "description": "Space ID"},
                "tag_name": {"type": "string", "description": "Tag name"},
            },
            "required": ["space_id", "tag_name"],
        },
    ),
    Tool(
        name="add_tag_to_task",
        description="Add a tag to a task",
        inputSchema={
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task ID"},
                "tag_name": {"type": "string", "description": "Tag name"},
                "custom_task_ids": {"type": "boolean", "description": "task_id is a custom ID"},
                "team_id": {"type": "string", "description": "Team ID (required with custom_task_ids)"},
            },
            "required": ["task_id", "tag_name"],
        },
    ),
    Tool(
        name="remove_tag_from_task",
        description="Remove a tag from a task",
        inputSchema={
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task ID"},
                "tag_name": {"type": "string", "description": "Tag name"},
                "custom_task_ids": {"type": "boolean", "description": "task_id is a custom ID"},
                "team_id": {"type": "string", "description": "Team ID (required with custom_task_ids)"},
            },
            "required": ["task_id", "tag_name"],
        },
    ),
    # ----- Goals -----
    Tool(
        name="get_goals",
        description="Get goals in a workspace",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "include_completed": {"type": "boolean", "description": "Include completed goals", "default": False},
            },
            "required": ["team_id"],
        },
    ),
    Tool(
        name="create_goal",
        description="Create a goal",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "name": {"type": "string", "description": "Goal name"},
                "due_date": {"type": "integer", "description": "Due date timestamp (ms)"},
                "description": {"type": "string", "description": "Goal description"},
                "multiple_owners": {"type": "boolean", "description": "Allow multiple owners"},
                "owners": {"type": "array", "items": {"type": "string"}, "description": "Owner user IDs"},
                "color": {"type": "string", "description": "Goal color hex"},
            },
            "required": ["team_id", "name"],
        },
    ),
    Tool(
        name="get_goal",
        description="Get a specific goal",
        inputSchema={
            "type": "object",
            "properties": {"goal_id": {"type": "string", "description": "Goal ID"}},
            "required": ["goal_id"],
        },
    ),
    Tool(
        name="update_goal",
        description="Update a goal",
        inputSchema={
            "type": "object",
            "properties": {
                "goal_id": {"type": "string", "description": "Goal ID"},
                "name": {"type": "string", "description": "New name"},
                "due_date": {"type": "integer", "description": "New due date (ms)"},
                "description": {"type": "string", "description": "New description"},
                "color": {"type": "string", "description": "New color hex"},
                "rem_owners": {"type": "array", "items": {"type": "string"}, "description": "Owners to remove"},
                "add_owners": {"type": "array", "items": {"type": "string"}, "description": "Owners to add"},
            },
            "required": ["goal_id"],
        },
    ),
    Tool(
        name="delete_goal",
        description="Delete a goal",
        inputSchema={
            "type": "object",
            "properties": {"goal_id": {"type": "string", "description": "Goal ID"}},
            "required": ["goal_id"],
        },
    ),
    Tool(
        name="create_key_result",
        description="Create a key result (target) on a goal",
        inputSchema={
            "type": "object",
            "properties": {
                "goal_id": {"type": "string", "description": "Goal ID"},
                "name": {"type": "string", "description": "Key result name"},
                "type": {"type": "string", "description": "Type: number, currency, boolean, percentage, automatic"},
                "steps_start": {"type": "integer", "description": "Starting value", "default": 0},
                "steps_end": {"type": "integer", "description": "Target value", "default": 10},
                "unit": {"type": "string", "description": "Unit label"},
                "owners": {"type": "array", "items": {"type": "string"}, "description": "Owner user IDs"},
                "task_ids": {"type": "array", "items": {"type": "string"}, "description": "Linked task IDs"},
                "list_ids": {"type": "array", "items": {"type": "string"}, "description": "Linked list IDs"},
            },
            "required": ["goal_id", "name", "type"],
        },
    ),
    Tool(
        name="update_key_result",
        description="Update a key result",
        inputSchema={
            "type": "object",
            "properties": {
                "key_result_id": {"type": "string", "description": "Key result ID"},
                "name": {"type": "string", "description": "New name"},
                "steps_current": {"type": "integer", "description": "Current progress value"},
                "steps_start": {"type": "integer", "description": "New starting value"},
                "steps_end": {"type": "integer", "description": "New target value"},
                "unit": {"type": "string", "description": "New unit label"},
                "note": {"type": "string", "description": "Progress note"},
            },
            "required": ["key_result_id"],
        },
    ),
    Tool(
        name="delete_key_result",
        description="Delete a key result",
        inputSchema={
            "type": "object",
            "properties": {"key_result_id": {"type": "string", "description": "Key result ID"}},
            "required": ["key_result_id"],
        },
    ),
    # ----- Time Tracking -----
    Tool(
        name="get_time_entries",
        description="Get time entries within a date range",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "start_date": {"type": "integer", "description": "Start date (ms timestamp)"},
                "end_date": {"type": "integer", "description": "End date (ms timestamp)"},
                "assignee": {"type": "array", "items": {"type": "string"}, "description": "Filter by user IDs"},
                "include_task_tags": {"type": "boolean", "description": "Include task tags"},
                "include_location_names": {"type": "boolean", "description": "Include location names"},
                "space_id": {"type": "string", "description": "Filter by space"},
                "folder_id": {"type": "string", "description": "Filter by folder"},
                "list_id": {"type": "string", "description": "Filter by list"},
                "task_id": {"type": "string", "description": "Filter by task"},
                "custom_task_ids": {"type": "boolean", "description": "task_id is a custom ID"},
            },
            "required": ["team_id"],
        },
    ),
    Tool(
        name="create_time_entry",
        description="Create a time entry",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "start": {"type": "integer", "description": "Start time (ms timestamp)"},
                "duration": {"type": "integer", "description": "Duration in milliseconds"},
                "task_id": {"type": "string", "description": "Task ID to track time on"},
                "description": {"type": "string", "description": "Time entry description"},
                "billable": {"type": "boolean", "description": "Mark as billable", "default": False},
                "tags": {"type": "array", "items": {"type": "object"}, "description": "Tags to add"},
                "custom_task_ids": {"type": "boolean", "description": "task_id is a custom ID"},
            },
            "required": ["team_id", "start", "duration"],
        },
    ),
    Tool(
        name="get_time_entry",
        description="Get a specific time entry",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "timer_id": {"type": "string", "description": "Time entry ID"},
                "include_task": {"type": "boolean", "description": "Include task details"},
                "include_location_names": {"type": "boolean", "description": "Include location names"},
            },
            "required": ["team_id", "timer_id"],
        },
    ),
    Tool(
        name="update_time_entry",
        description="Update a time entry",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "timer_id": {"type": "string", "description": "Time entry ID"},
                "description": {"type": "string", "description": "New description"},
                "start": {"type": "integer", "description": "New start time (ms)"},
                "end": {"type": "integer", "description": "New end time (ms)"},
                "duration": {"type": "integer", "description": "New duration (ms)"},
                "billable": {"type": "boolean", "description": "Mark as billable"},
                "tag_action": {"type": "string", "description": "Tag action: add or remove"},
                "tags": {"type": "array", "items": {"type": "object"}, "description": "Tags to add/remove"},
            },
            "required": ["team_id", "timer_id"],
        },
    ),
    Tool(
        name="delete_time_entry",
        description="Delete a time entry",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "timer_id": {"type": "string", "description": "Time entry ID"},
            },
            "required": ["team_id", "timer_id"],
        },
    ),
    Tool(
        name="get_time_entry_history",
        description="Get history of changes to a time entry",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "timer_id": {"type": "string", "description": "Time entry ID"},
            },
            "required": ["team_id", "timer_id"],
        },
    ),
    Tool(
        name="get_running_time_entry",
        description="Get the currently running time entry",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "assignee": {"type": "string", "description": "Filter by user ID"},
            },
            "required": ["team_id"],
        },
    ),
    Tool(
        name="start_time_entry",
        description="Start a timer on a task",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "task_id": {"type": "string", "description": "Task ID"},
                "description": {"type": "string", "description": "Timer description"},
                "billable": {"type": "boolean", "description": "Mark as billable", "default": False},
                "tags": {"type": "array", "items": {"type": "object"}, "description": "Tags to add"},
                "custom_task_ids": {"type": "boolean", "description": "task_id is a custom ID"},
            },
            "required": ["team_id", "task_id"],
        },
    ),
    Tool(
        name="stop_time_entry",
        description="Stop the currently running timer",
        inputSchema={
            "type": "object",
            "properties": {"team_id": {"type": "string", "description": "Workspace/Team ID"}},
            "required": ["team_id"],
        },
    ),
    Tool(
        name="get_time_entry_tags",
        description="Get all time entry tags in a workspace",
        inputSchema={
            "type": "object",
            "properties": {"team_id": {"type": "string", "description": "Workspace/Team ID"}},
            "required": ["team_id"],
        },
    ),
    Tool(
        name="add_tags_to_time_entries",
        description="Add tags to time entries",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "time_entry_ids": {"type": "array", "items": {"type": "string"}, "description": "Time entry IDs"},
                "tags": {"type": "array", "items": {"type": "object"}, "description": "Tags to add"},
            },
            "required": ["team_id", "time_entry_ids", "tags"],
        },
    ),
    Tool(
        name="remove_tags_from_time_entries",
        description="Remove tags from time entries",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "time_entry_ids": {"type": "array", "items": {"type": "string"}, "description": "Time entry IDs"},
                "tags": {"type": "array", "items": {"type": "object"}, "description": "Tags to remove"},
            },
            "required": ["team_id", "time_entry_ids", "tags"],
        },
    ),
    Tool(
        name="update_time_entry_tags",
        description="Rename time entry tags",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "name": {"type": "string", "description": "Current tag name"},
                "new_name": {"type": "string", "description": "New tag name"},
                "tag_bg": {"type": "string", "description": "Background color hex"},
                "tag_fg": {"type": "string", "description": "Foreground color hex"},
            },
            "required": ["team_id", "name", "new_name", "tag_bg", "tag_fg"],
        },
    ),
    # ----- Members -----
    Tool(
        name="get_task_members",
        description="Get members with access to a task",
        inputSchema={
            "type": "object",
            "properties": {"task_id": {"type": "string", "description": "Task ID"}},
            "required": ["task_id"],
        },
    ),
    Tool(
        name="get_list_members",
        description="Get members with access to a list",
        inputSchema={
            "type": "object",
            "properties": {"list_id": {"type": "string", "description": "List ID"}},
            "required": ["list_id"],
        },
    ),
    # ----- Users -----
    Tool(
        name="invite_user_to_workspace",
        description="Invite a user to a workspace",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "email": {"type": "string", "description": "User's email address"},
                "admin": {"type": "boolean", "description": "Make user an admin", "default": False},
                "custom_role_id": {"type": "string", "description": "Custom role ID to assign"},
            },
            "required": ["team_id", "email"],
        },
    ),
    Tool(
        name="get_user",
        description="Get a user in a workspace",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "user_id": {"type": "string", "description": "User ID"},
            },
            "required": ["team_id", "user_id"],
        },
    ),
    Tool(
        name="update_user",
        description="Update a user in a workspace",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "user_id": {"type": "string", "description": "User ID"},
                "username": {"type": "string", "description": "New username"},
                "admin": {"type": "boolean", "description": "Admin status"},
                "custom_role_id": {"type": "string", "description": "New custom role ID"},
            },
            "required": ["team_id", "user_id"],
        },
    ),
    Tool(
        name="remove_user_from_workspace",
        description="Remove a user from a workspace",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "user_id": {"type": "string", "description": "User ID"},
            },
            "required": ["team_id", "user_id"],
        },
    ),
    # ----- Guests -----
    Tool(
        name="invite_guest_to_workspace",
        description="Invite a guest to a workspace",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "email": {"type": "string", "description": "Guest's email address"},
                "can_edit_tags": {"type": "boolean", "description": "Can edit tags", "default": False},
                "can_see_time_spent": {"type": "boolean", "description": "Can see time spent", "default": False},
                "can_see_time_estimated": {"type": "boolean", "description": "Can see time estimates", "default": False},
                "can_create_views": {"type": "boolean", "description": "Can create views", "default": False},
            },
            "required": ["team_id", "email"],
        },
    ),
    Tool(
        name="get_guest",
        description="Get a guest in a workspace",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "guest_id": {"type": "string", "description": "Guest ID"},
            },
            "required": ["team_id", "guest_id"],
        },
    ),
    Tool(
        name="update_guest",
        description="Update a guest's permissions",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "guest_id": {"type": "string", "description": "Guest ID"},
                "can_edit_tags": {"type": "boolean", "description": "Can edit tags"},
                "can_see_time_spent": {"type": "boolean", "description": "Can see time spent"},
                "can_see_time_estimated": {"type": "boolean", "description": "Can see time estimates"},
                "can_create_views": {"type": "boolean", "description": "Can create views"},
            },
            "required": ["team_id", "guest_id"],
        },
    ),
    Tool(
        name="remove_guest_from_workspace",
        description="Remove a guest from a workspace",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "guest_id": {"type": "string", "description": "Guest ID"},
            },
            "required": ["team_id", "guest_id"],
        },
    ),
    Tool(
        name="add_guest_to_task",
        description="Add a guest to a task",
        inputSchema={
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task ID"},
                "guest_id": {"type": "string", "description": "Guest ID"},
                "permission_level": {"type": "string", "description": "Permission: read, comment, edit, create"},
            },
            "required": ["task_id", "guest_id", "permission_level"],
        },
    ),
    Tool(
        name="remove_guest_from_task",
        description="Remove a guest from a task",
        inputSchema={
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task ID"},
                "guest_id": {"type": "string", "description": "Guest ID"},
            },
            "required": ["task_id", "guest_id"],
        },
    ),
    Tool(
        name="add_guest_to_list",
        description="Add a guest to a list",
        inputSchema={
            "type": "object",
            "properties": {
                "list_id": {"type": "string", "description": "List ID"},
                "guest_id": {"type": "string", "description": "Guest ID"},
                "permission_level": {"type": "string", "description": "Permission: read, comment, edit, create"},
            },
            "required": ["list_id", "guest_id", "permission_level"],
        },
    ),
    Tool(
        name="remove_guest_from_list",
        description="Remove a guest from a list",
        inputSchema={
            "type": "object",
            "properties": {
                "list_id": {"type": "string", "description": "List ID"},
                "guest_id": {"type": "string", "description": "Guest ID"},
            },
            "required": ["list_id", "guest_id"],
        },
    ),
    Tool(
        name="add_guest_to_folder",
        description="Add a guest to a folder",
        inputSchema={
            "type": "object",
            "properties": {
                "folder_id": {"type": "string", "description": "Folder ID"},
                "guest_id": {"type": "string", "description": "Guest ID"},
                "permission_level": {"type": "string", "description": "Permission: read, comment, edit, create"},
            },
            "required": ["folder_id", "guest_id", "permission_level"],
        },
    ),
    Tool(
        name="remove_guest_from_folder",
        description="Remove a guest from a folder",
        inputSchema={
            "type": "object",
            "properties": {
                "folder_id": {"type": "string", "description": "Folder ID"},
                "guest_id": {"type": "string", "description": "Guest ID"},
            },
            "required": ["folder_id", "guest_id"],
        },
    ),
    # ----- User Groups -----
    Tool(
        name="get_user_groups",
        description="Get user groups in a workspace",
        inputSchema={
            "type": "object",
            "properties": {"team_id": {"type": "string", "description": "Workspace/Team ID"}},
            "required": ["team_id"],
        },
    ),
    Tool(
        name="create_user_group",
        description="Create a user group",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "name": {"type": "string", "description": "Group name"},
                "member_ids": {"type": "array", "items": {"type": "string"}, "description": "Initial member user IDs"},
            },
            "required": ["team_id", "name"],
        },
    ),
    Tool(
        name="update_user_group",
        description="Update a user group",
        inputSchema={
            "type": "object",
            "properties": {
                "group_id": {"type": "string", "description": "Group ID"},
                "name": {"type": "string", "description": "New group name"},
                "member_ids_to_add": {"type": "array", "items": {"type": "string"}, "description": "Members to add"},
                "member_ids_to_remove": {"type": "array", "items": {"type": "string"}, "description": "Members to remove"},
            },
            "required": ["group_id"],
        },
    ),
    Tool(
        name="delete_user_group",
        description="Delete a user group",
        inputSchema={
            "type": "object",
            "properties": {"group_id": {"type": "string", "description": "Group ID"}},
            "required": ["group_id"],
        },
    ),
    # ----- Roles -----
    Tool(
        name="get_custom_roles",
        description="Get custom roles in a workspace",
        inputSchema={
            "type": "object",
            "properties": {"team_id": {"type": "string", "description": "Workspace/Team ID"}},
            "required": ["team_id"],
        },
    ),
    # ----- Views -----
    Tool(
        name="get_workspace_views",
        description="Get workspace-level views",
        inputSchema={
            "type": "object",
            "properties": {"team_id": {"type": "string", "description": "Workspace/Team ID"}},
            "required": ["team_id"],
        },
    ),
    Tool(
        name="create_workspace_view",
        description="Create a workspace-level view",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "name": {"type": "string", "description": "View name"},
                "type": {"type": "string", "description": "View type: list, board, calendar, gantt, table, map, etc."},
                "grouping": {"type": "object", "description": "Grouping configuration"},
                "divide": {"type": "object", "description": "Divide configuration"},
                "sorting": {"type": "object", "description": "Sorting configuration"},
                "filters": {"type": "object", "description": "Filter configuration"},
                "columns": {"type": "object", "description": "Column configuration"},
            },
            "required": ["team_id", "name", "type"],
        },
    ),
    Tool(
        name="get_space_views",
        description="Get space-level views",
        inputSchema={
            "type": "object",
            "properties": {"space_id": {"type": "string", "description": "Space ID"}},
            "required": ["space_id"],
        },
    ),
    Tool(
        name="create_space_view",
        description="Create a space-level view",
        inputSchema={
            "type": "object",
            "properties": {
                "space_id": {"type": "string", "description": "Space ID"},
                "name": {"type": "string", "description": "View name"},
                "type": {"type": "string", "description": "View type"},
                "grouping": {"type": "object", "description": "Grouping configuration"},
                "divide": {"type": "object", "description": "Divide configuration"},
                "sorting": {"type": "object", "description": "Sorting configuration"},
                "filters": {"type": "object", "description": "Filter configuration"},
                "columns": {"type": "object", "description": "Column configuration"},
            },
            "required": ["space_id", "name", "type"],
        },
    ),
    Tool(
        name="get_folder_views",
        description="Get folder-level views",
        inputSchema={
            "type": "object",
            "properties": {"folder_id": {"type": "string", "description": "Folder ID"}},
            "required": ["folder_id"],
        },
    ),
    Tool(
        name="create_folder_view",
        description="Create a folder-level view",
        inputSchema={
            "type": "object",
            "properties": {
                "folder_id": {"type": "string", "description": "Folder ID"},
                "name": {"type": "string", "description": "View name"},
                "type": {"type": "string", "description": "View type"},
                "grouping": {"type": "object", "description": "Grouping configuration"},
                "divide": {"type": "object", "description": "Divide configuration"},
                "sorting": {"type": "object", "description": "Sorting configuration"},
                "filters": {"type": "object", "description": "Filter configuration"},
                "columns": {"type": "object", "description": "Column configuration"},
            },
            "required": ["folder_id", "name", "type"],
        },
    ),
    Tool(
        name="get_list_views",
        description="Get list-level views",
        inputSchema={
            "type": "object",
            "properties": {"list_id": {"type": "string", "description": "List ID"}},
            "required": ["list_id"],
        },
    ),
    Tool(
        name="create_list_view",
        description="Create a list-level view",
        inputSchema={
            "type": "object",
            "properties": {
                "list_id": {"type": "string", "description": "List ID"},
                "name": {"type": "string", "description": "View name"},
                "type": {"type": "string", "description": "View type"},
                "grouping": {"type": "object", "description": "Grouping configuration"},
                "divide": {"type": "object", "description": "Divide configuration"},
                "sorting": {"type": "object", "description": "Sorting configuration"},
                "filters": {"type": "object", "description": "Filter configuration"},
                "columns": {"type": "object", "description": "Column configuration"},
            },
            "required": ["list_id", "name", "type"],
        },
    ),
    Tool(
        name="get_view",
        description="Get a specific view",
        inputSchema={
            "type": "object",
            "properties": {"view_id": {"type": "string", "description": "View ID"}},
            "required": ["view_id"],
        },
    ),
    Tool(
        name="update_view",
        description="Update a view",
        inputSchema={
            "type": "object",
            "properties": {
                "view_id": {"type": "string", "description": "View ID"},
                "name": {"type": "string", "description": "New name"},
                "grouping": {"type": "object", "description": "New grouping configuration"},
                "divide": {"type": "object", "description": "New divide configuration"},
                "sorting": {"type": "object", "description": "New sorting configuration"},
                "filters": {"type": "object", "description": "New filter configuration"},
                "columns": {"type": "object", "description": "New column configuration"},
            },
            "required": ["view_id"],
        },
    ),
    Tool(
        name="delete_view",
        description="Delete a view",
        inputSchema={
            "type": "object",
            "properties": {"view_id": {"type": "string", "description": "View ID"}},
            "required": ["view_id"],
        },
    ),
    Tool(
        name="get_view_tasks",
        description="Get tasks in a view",
        inputSchema={
            "type": "object",
            "properties": {
                "view_id": {"type": "string", "description": "View ID"},
                "page": {"type": "integer", "description": "Page number", "default": 0},
            },
            "required": ["view_id"],
        },
    ),
    # ----- Webhooks -----
    Tool(
        name="get_webhooks",
        description="Get webhooks in a workspace",
        inputSchema={
            "type": "object",
            "properties": {"team_id": {"type": "string", "description": "Workspace/Team ID"}},
            "required": ["team_id"],
        },
    ),
    Tool(
        name="create_webhook",
        description="Create a webhook",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "endpoint": {"type": "string", "description": "Webhook URL endpoint"},
                "events": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Events to subscribe to (taskCreated, taskUpdated, taskDeleted, etc. or '*' for all)",
                },
                "space_id": {"type": "string", "description": "Filter to space (optional)"},
                "folder_id": {"type": "string", "description": "Filter to folder (optional)"},
                "list_id": {"type": "string", "description": "Filter to list (optional)"},
                "task_id": {"type": "string", "description": "Filter to task (optional)"},
            },
            "required": ["team_id", "endpoint", "events"],
        },
    ),
    Tool(
        name="update_webhook",
        description="Update a webhook",
        inputSchema={
            "type": "object",
            "properties": {
                "webhook_id": {"type": "string", "description": "Webhook ID"},
                "endpoint": {"type": "string", "description": "New endpoint URL"},
                "events": {"type": "array", "items": {"type": "string"}, "description": "New events to subscribe to"},
                "status": {"type": "string", "description": "Webhook status: active or suspended"},
            },
            "required": ["webhook_id"],
        },
    ),
    Tool(
        name="delete_webhook",
        description="Delete a webhook",
        inputSchema={
            "type": "object",
            "properties": {"webhook_id": {"type": "string", "description": "Webhook ID"}},
            "required": ["webhook_id"],
        },
    ),
    # ----- Templates -----
    Tool(
        name="get_task_templates",
        description="Get task templates in a workspace",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "page": {"type": "integer", "description": "Page number", "default": 0},
            },
            "required": ["team_id"],
        },
    ),
    Tool(
        name="get_folder_templates",
        description="Get folder templates in a workspace (returned IDs keep their 't-' prefix)",
        inputSchema={
            "type": "object",
            "properties": {"team_id": {"type": "string", "description": "Workspace/Team ID"}},
            "required": ["team_id"],
        },
    ),
    Tool(
        name="get_list_templates",
        description="Get list templates in a workspace (returned IDs keep their 't-' prefix)",
        inputSchema={
            "type": "object",
            "properties": {"team_id": {"type": "string", "description": "Workspace/Team ID"}},
            "required": ["team_id"],
        },
    ),
    Tool(
        name="create_folder_from_template",
        description="Create a folder in a space from a folder template (use the full 't-' prefixed template ID)",
        inputSchema={
            "type": "object",
            "properties": {
                "space_id": {"type": "string", "description": "Space ID"},
                "template_id": {"type": "string", "description": "Folder template ID including the 't-' prefix"},
                "name": {"type": "string", "description": "Name for the new folder"},
                "options": {"type": "object", "description": "Import toggles (return_immediately, include_views, old_due_date, subtasks, ...)"},
            },
            "required": ["space_id", "template_id", "name"],
        },
    ),
    Tool(
        name="create_list_from_template_in_folder",
        description="Create a list in a folder from a list template (use the full 't-' prefixed template ID)",
        inputSchema={
            "type": "object",
            "properties": {
                "folder_id": {"type": "string", "description": "Folder ID"},
                "template_id": {"type": "string", "description": "List template ID including the 't-' prefix"},
                "name": {"type": "string", "description": "Name for the new list"},
                "options": {"type": "object", "description": "Import toggles (return_immediately, include_views, old_due_date, subtasks, ...)"},
            },
            "required": ["folder_id", "template_id", "name"],
        },
    ),
    Tool(
        name="create_list_from_template_in_space",
        description="Create a folderless list in a space from a list template (use the full 't-' prefixed template ID)",
        inputSchema={
            "type": "object",
            "properties": {
                "space_id": {"type": "string", "description": "Space ID"},
                "template_id": {"type": "string", "description": "List template ID including the 't-' prefix"},
                "name": {"type": "string", "description": "Name for the new list"},
                "options": {"type": "object", "description": "Import toggles (return_immediately, include_views, old_due_date, subtasks, ...)"},
            },
            "required": ["space_id", "template_id", "name"],
        },
    ),
    # ----- Shared Hierarchy -----
    Tool(
        name="get_shared_hierarchy",
        description="Get the shared hierarchy (shared spaces/folders/lists/tasks)",
        inputSchema={
            "type": "object",
            "properties": {"team_id": {"type": "string", "description": "Workspace/Team ID"}},
            "required": ["team_id"],
        },
    ),
    # ----- Docs (API v3) -----
    Tool(
        name="search_docs",
        description="Search docs in a workspace (API v3)",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "query": {"type": "string", "description": "Search text (optional)"},
                "cursor": {"type": "string", "description": "Pagination cursor (optional)"},
            },
            "required": ["team_id"],
        },
    ),
    Tool(
        name="create_doc",
        description="Create a doc in a workspace (API v3)",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "name": {"type": "string", "description": "Doc name"},
                "parent": {"type": "object", "description": "Optional parent: {id, type} (type: 4=space, 5=folder, 6=list, 7=everything, 12=workspace)"},
                "visibility": {"type": "string", "description": "PUBLIC or PRIVATE (optional)"},
                "create_page": {"type": "boolean", "description": "Create a blank starter page (API default: true; pass false to skip)"},
            },
            "required": ["team_id", "name"],
        },
    ),
    Tool(
        name="get_doc",
        description="Get a doc's metadata: dates, parent, archived state, page defaults (API v3). 404 returns an empty object.",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "doc_id": {"type": "string", "description": "Doc ID"},
            },
            "required": ["team_id", "doc_id"],
        },
    ),
    Tool(
        name="get_doc_page_listing",
        description="Get a doc's page tree (ids + names, no content) (API v3)",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "doc_id": {"type": "string", "description": "Doc ID"},
            },
            "required": ["team_id", "doc_id"],
        },
    ),
    Tool(
        name="get_doc_pages",
        description="Get all pages of a doc including content (API v3)",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "doc_id": {"type": "string", "description": "Doc ID"},
                "content_format": {"type": "string", "description": "text/md (default) or text/plain", "default": "text/md"},
            },
            "required": ["team_id", "doc_id"],
        },
    ),
    Tool(
        name="get_doc_page",
        description="Get one page of a doc (API v3)",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "doc_id": {"type": "string", "description": "Doc ID"},
                "page_id": {"type": "string", "description": "Page ID"},
                "content_format": {"type": "string", "description": "text/md (default) or text/plain", "default": "text/md"},
            },
            "required": ["team_id", "doc_id", "page_id"],
        },
    ),
    Tool(
        name="create_doc_page",
        description="Create a page or subpage in a doc (API v3). Preferred way to add doc content.",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "doc_id": {"type": "string", "description": "Doc ID"},
                "name": {"type": "string", "description": "Page name"},
                "content": {"type": "string", "description": "Page content (markdown)"},
                "parent_page_id": {"type": "string", "description": "Parent page ID to nest under (optional)"},
                "sub_title": {"type": "string", "description": "Page subtitle (optional)"},
                "content_format": {"type": "string", "description": "text/md (default) or text/plain", "default": "text/md"},
            },
            "required": ["team_id", "doc_id", "name", "content"],
        },
    ),
    Tool(
        name="update_doc_page",
        description=(
            "Update a doc page (API v3). content_edit_mode defaults to 'append' (safe). "
            "'replace' REWRITES the page and flattens live task chips — it requires the "
            "confirm token (RED tier)."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "doc_id": {"type": "string", "description": "Doc ID"},
                "page_id": {"type": "string", "description": "Page ID"},
                "content": {"type": "string", "description": "Content to write (markdown)"},
                "name": {"type": "string", "description": "New page name (optional)"},
                "sub_title": {"type": "string", "description": "New subtitle (optional)"},
                "content_edit_mode": {"type": "string", "description": "append (default) | prepend | replace (replace = RED tier, needs confirm)", "default": "append"},
                "content_format": {"type": "string", "description": "text/md (default) or text/plain", "default": "text/md"},
            },
            "required": ["team_id", "doc_id", "page_id"],
        },
    ),
    # ----- Chat (API v3) -----
    Tool(
        name="get_chat_channels",
        description="Get chat channels including DMs (API v3). DMs list member ids only, no names — use get_chat_channel_members to resolve.",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "cursor": {"type": "string", "description": "Pagination cursor (optional)"},
                "limit": {"type": "integer", "description": "Page size 1-100 (default 50)"},
                "is_follower": {"type": "boolean", "description": "Only channels the caller follows"},
                "include_closed": {"type": "boolean", "description": "Include closed DMs/group DMs"},
                "with_message_since": {"type": "integer", "description": "Only channels with a message since this ms timestamp"},
            },
            "required": ["team_id"],
        },
    ),
    Tool(
        name="get_chat_messages",
        description="Get messages in a chat channel, most recent first (API v3)",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "channel_id": {"type": "string", "description": "Channel ID"},
                "cursor": {"type": "string", "description": "Pagination cursor (optional)"},
                "limit": {"type": "integer", "description": "Page size 1-100 (default 50)"},
                "content_format": {"type": "string", "description": "text/md (default) or text/plain"},
            },
            "required": ["team_id", "channel_id"],
        },
    ),
    Tool(
        name="send_chat_message",
        description=(
            "Send a message to a chat channel or DM (API v3). RED tier: requires the "
            "confirm token, only after the human has approved the exact message text "
            "and the sending account."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "channel_id": {"type": "string", "description": "Channel ID"},
                "content": {"type": "string", "description": "Message text (max 40,000 chars)"},
                "msg_type": {"type": "string", "description": "message (default) or post", "default": "message"},
                "content_format": {"type": "string", "description": "text/md (default) or text/plain"},
                "assignee": {"type": "string", "description": "Assignee user ID for the message"},
                "group_assignee": {"type": "string", "description": "Group assignee for the message"},
                "triaged_action": {"type": "number", "description": "Triage action (1 or 2)"},
                "triaged_object_id": {"type": "string", "description": "Triage object ID"},
                "triaged_object_type": {"type": "number", "description": "Triage object type"},
                "reactions": {"type": "array", "items": {"type": "object"}, "description": "Reactions (max 10): [{date, reaction, user_id}]"},
                "followers": {"type": "array", "items": {"type": "string"}, "description": "Follower user IDs (max 10)"},
                "post_data": {"type": "object", "description": "Required when msg_type='post': {title, subtype: {id}}"},
            },
            "required": ["team_id", "channel_id", "content"],
        },
    ),
    Tool(
        name="get_chat_message_replies",
        description="Get replies to a chat message (API v3)",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "message_id": {"type": "string", "description": "Message ID"},
                "cursor": {"type": "string", "description": "Pagination cursor (optional)"},
                "limit": {"type": "integer", "description": "Page size 1-100 (default 50)"},
                "content_format": {"type": "string", "description": "text/md (default) or text/plain"},
            },
            "required": ["team_id", "message_id"],
        },
    ),
    Tool(
        name="get_chat_channel",
        description="Get a single chat channel by ID (API v3)",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "channel_id": {"type": "string", "description": "Channel ID"},
            },
            "required": ["team_id", "channel_id"],
        },
    ),
    Tool(
        name="create_chat_channel",
        description=(
            "Create a chat channel (API v3). RED tier: channels are shared, team-visible structures — "
            "requires the confirm token. If the name already exists the EXISTING channel is returned."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "name": {"type": "string", "description": "Channel name (acts as an upsert key)"},
                "description": {"type": "string", "description": "Channel description"},
                "topic": {"type": "string", "description": "Channel topic"},
                "visibility": {"type": "string", "description": "PUBLIC (default) or PRIVATE"},
                "user_ids": {"type": "array", "items": {"type": "string"}, "description": "Member user IDs (max 100)"},
            },
            "required": ["team_id", "name"],
        },
    ),
    Tool(
        name="update_chat_channel",
        description=(
            "Update a chat channel's name/description/topic/visibility/location (API v3). "
            "RED tier: shared standing config — requires the confirm token."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "channel_id": {"type": "string", "description": "Channel ID"},
                "name": {"type": "string", "description": "New name"},
                "description": {"type": "string", "description": "New description"},
                "topic": {"type": "string", "description": "New topic"},
                "visibility": {"type": "string", "description": "PUBLIC or PRIVATE"},
                "location": {"type": "object", "description": "New parent location: {id, type} (type: folder|list|space)"},
                "content_format": {"type": "string", "description": "text/md (default) or text/plain"},
            },
            "required": ["team_id", "channel_id"],
        },
    ),
    Tool(
        name="delete_chat_channel",
        description="Delete a chat channel (API v3). RED tier: requires the confirm token.",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "channel_id": {"type": "string", "description": "Channel ID"},
            },
            "required": ["team_id", "channel_id"],
        },
    ),
    Tool(
        name="create_chat_dm_channel",
        description=(
            "Create (or return the existing) direct-message channel with the given users (API v3). "
            "RED tier: opens a conversation others see — requires the confirm token. "
            "ALWAYS pass user_ids; an empty list creates a useless self-DM."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "user_ids": {"type": "array", "items": {"type": "string"}, "description": "Participant user IDs (max 15, excluding yourself)"},
            },
            "required": ["team_id", "user_ids"],
        },
    ),
    Tool(
        name="create_chat_location_channel",
        description=(
            "Create (or return the existing) chat channel attached to a space/folder/list (API v3). "
            "RED tier: shared standing config — requires the confirm token."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "location": {"type": "object", "description": "{id, type} — type: folder|list|space"},
                "description": {"type": "string", "description": "Channel description"},
                "topic": {"type": "string", "description": "Channel topic"},
                "visibility": {"type": "string", "description": "PUBLIC (default) or PRIVATE"},
                "user_ids": {"type": "array", "items": {"type": "string"}, "description": "Member user IDs (max 100)"},
            },
            "required": ["team_id", "location"],
        },
    ),
    Tool(
        name="get_chat_channel_members",
        description="Get members of a chat channel (API v3). THE way to identify who a DM is with.",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "channel_id": {"type": "string", "description": "Channel ID"},
                "cursor": {"type": "string", "description": "Pagination cursor (optional)"},
                "limit": {"type": "integer", "description": "Page size 1-100 (default 50)"},
            },
            "required": ["team_id", "channel_id"],
        },
    ),
    Tool(
        name="get_chat_channel_followers",
        description="Get followers of a chat channel (API v3)",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "channel_id": {"type": "string", "description": "Channel ID"},
                "cursor": {"type": "string", "description": "Pagination cursor (optional)"},
                "limit": {"type": "integer", "description": "Page size 1-100 (default 50)"},
            },
            "required": ["team_id", "channel_id"],
        },
    ),
    Tool(
        name="send_chat_reply",
        description=(
            "Reply to a chat message (API v3). RED tier: outbound message — requires the confirm "
            "token, only after the human approved the exact text and sending account."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "message_id": {"type": "string", "description": "Parent message ID"},
                "content": {"type": "string", "description": "Reply text (max 40,000 chars)"},
                "msg_type": {"type": "string", "description": "message (default) or post", "default": "message"},
                "content_format": {"type": "string", "description": "text/md (default) or text/plain"},
                "post_data": {"type": "object", "description": "Required when msg_type='post': {title, subtype: {id}}"},
            },
            "required": ["team_id", "message_id", "content"],
        },
    ),
    Tool(
        name="update_chat_message",
        description=(
            "Edit a sent chat message (API v3). RED tier: alters what others already saw — "
            "requires the confirm token."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "message_id": {"type": "string", "description": "Message ID"},
                "content": {"type": "string", "description": "New message text"},
                "content_format": {"type": "string", "description": "text/md (default) or text/plain"},
                "assignee": {"type": "string", "description": "Assignee user ID"},
                "resolved": {"type": "boolean", "description": "Resolved status"},
                "post_data": {"type": "object", "description": "Post metadata: {title, subtype: {id}}"},
            },
            "required": ["team_id", "message_id"],
        },
    ),
    Tool(
        name="delete_chat_message",
        description="Delete a chat message (API v3). RED tier: requires the confirm token.",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "message_id": {"type": "string", "description": "Message ID"},
            },
            "required": ["team_id", "message_id"],
        },
    ),
    Tool(
        name="get_chat_message_tagged_users",
        description="Get users tagged (mentioned) in a chat message (API v3)",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "message_id": {"type": "string", "description": "Message ID"},
                "cursor": {"type": "string", "description": "Pagination cursor (optional)"},
                "limit": {"type": "integer", "description": "Page size 1-100 (default 50)"},
            },
            "required": ["team_id", "message_id"],
        },
    ),
    Tool(
        name="create_chat_reaction",
        description=(
            "React to a chat message with an emoji (API v3). RED tier: visible social signal from "
            "Scott's account — requires the confirm token. reaction = lower-case emoji NAME "
            "(e.g. 'thumbsup'), not the emoji character. 400 if already present."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "message_id": {"type": "string", "description": "Message ID"},
                "reaction": {"type": "string", "description": "Lower-case emoji name"},
            },
            "required": ["team_id", "message_id", "reaction"],
        },
    ),
    Tool(
        name="delete_chat_reaction",
        description="Remove a reaction (by emoji name) from a chat message (API v3). RED tier: requires the confirm token.",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "message_id": {"type": "string", "description": "Message ID"},
                "reaction": {"type": "string", "description": "Lower-case emoji name to remove"},
            },
            "required": ["team_id", "message_id", "reaction"],
        },
    ),
    Tool(
        name="get_chat_message_reactions",
        description="Get reactions on a chat message (API v3)",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "message_id": {"type": "string", "description": "Message ID"},
                "cursor": {"type": "string", "description": "Pagination cursor (optional)"},
                "limit": {"type": "integer", "description": "Page size 1-100 (default 50)"},
            },
            "required": ["team_id", "message_id"],
        },
    ),
    Tool(
        name="get_chat_post_subtypes",
        description="Get post subtype IDs (Announcement/Discussion/Idea/Update) needed to send a chat 'post' (API v3)",
        inputSchema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Workspace/Team ID"},
                "comment_type": {"type": "string", "description": "post (default) | ai | syncup | ai_via_brain", "default": "post"},
            },
            "required": ["team_id"],
        },
    ),
]


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools."""
    return TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Execute a tool and return the result."""
    client = get_client()

    try:
        arguments = safety_check(name, arguments)
        result = await execute_tool(client, name, arguments)
        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
    except SafetyError as e:
        return [TextContent(type="text", text=json.dumps({"blocked": str(e)}))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def execute_tool(client: ClickUpClient, name: str, args: dict[str, Any]) -> Any:
    """Execute a specific tool."""
    # Authorization
    if name == "get_authorized_user":
        return await client.get_authorized_user()

    # Workspaces
    elif name == "get_workspaces":
        return await client.get_workspaces()
    elif name == "get_workspace_seats":
        return await client.get_workspace_seats(args["team_id"])
    elif name == "get_workspace_plan":
        return await client.get_workspace_plan(args["team_id"])

    # Spaces
    elif name == "get_spaces":
        return await client.get_spaces(args["team_id"], args.get("archived", False))
    elif name == "create_space":
        return await client.create_space(args["team_id"], args["name"], **{k: v for k, v in args.items() if k not in ["team_id", "name"]})
    elif name == "get_space":
        return await client.get_space(args["space_id"])
    elif name == "update_space":
        return await client.update_space(args["space_id"], **{k: v for k, v in args.items() if k != "space_id"})
    elif name == "delete_space":
        return await client.delete_space(args["space_id"])

    # Folders
    elif name == "get_folders":
        return await client.get_folders(args["space_id"], args.get("archived", False))
    elif name == "create_folder":
        return await client.create_folder(args["space_id"], args["name"])
    elif name == "get_folder":
        return await client.get_folder(args["folder_id"])
    elif name == "update_folder":
        return await client.update_folder(args["folder_id"], args["name"])
    elif name == "delete_folder":
        return await client.delete_folder(args["folder_id"])

    # Lists
    elif name == "get_lists":
        return await client.get_lists(args["folder_id"], args.get("archived", False))
    elif name == "create_list":
        return await client.create_list(args["folder_id"], args["name"], **{k: v for k, v in args.items() if k not in ["folder_id", "name"]})
    elif name == "get_folderless_lists":
        return await client.get_folderless_lists(args["space_id"], args.get("archived", False))
    elif name == "create_folderless_list":
        return await client.create_folderless_list(args["space_id"], args["name"], **{k: v for k, v in args.items() if k not in ["space_id", "name"]})
    elif name == "get_list":
        return await client.get_list(args["list_id"])
    elif name == "update_list":
        return await client.update_list(args["list_id"], **{k: v for k, v in args.items() if k != "list_id"})
    elif name == "delete_list":
        return await client.delete_list(args["list_id"])
    elif name == "add_task_to_list":
        return await client.add_task_to_list(args["list_id"], args["task_id"])
    elif name == "remove_task_from_list":
        return await client.remove_task_from_list(args["list_id"], args["task_id"])

    # Tasks
    elif name == "get_tasks":
        return await client.get_tasks(**args)
    elif name == "create_task":
        # Back-compat: the documented body param is markdown_content.
        if "markdown_description" in args and "markdown_content" not in args:
            args["markdown_content"] = args.pop("markdown_description")
        args.pop("markdown_description", None)
        return await client.create_task(args["list_id"], args["name"], **{k: v for k, v in args.items() if k not in ["list_id", "name"]})
    elif name == "get_task":
        return await client.get_task(**args)
    elif name == "update_task":
        if "markdown_description" in args and "markdown_content" not in args:
            args["markdown_content"] = args.pop("markdown_description")
        args.pop("markdown_description", None)
        task_id = args.pop("task_id")
        custom_task_ids = args.pop("custom_task_ids", False)
        team_id = args.pop("team_id", None)
        return await client.update_task(task_id, custom_task_ids, team_id, **args)
    elif name == "delete_task":
        return await client.delete_task(args["task_id"], args.get("custom_task_ids", False), args.get("team_id"))
    elif name == "get_filtered_team_tasks":
        return await client.get_filtered_team_tasks(**args)
    elif name == "get_task_time_in_status":
        return await client.get_task_time_in_status(args["task_id"], args.get("custom_task_ids", False), args.get("team_id"))
    elif name == "get_bulk_tasks_time_in_status":
        return await client.get_bulk_tasks_time_in_status(args["task_ids"], args.get("custom_task_ids", False), args.get("team_id"))
    elif name == "create_task_from_template":
        return await client.create_task_from_template(args["list_id"], args["template_id"], args["name"])
    elif name == "move_task":
        return await client.move_task(
            args["team_id"],
            args["task_id"],
            args["list_id"],
            args.get("move_custom_fields"),
            args.get("custom_fields_to_move"),
            args.get("status_mappings"),
        )
    elif name == "merge_tasks":
        return await client.merge_tasks(args["task_id"], args["source_task_ids"])
    elif name == "update_time_estimates_by_user":
        return await client.update_time_estimates_by_user(args["team_id"], args["task_id"], args["estimates"])
    elif name == "replace_time_estimates_by_user":
        return await client.replace_time_estimates_by_user(args["team_id"], args["task_id"], args["estimates"])

    # Checklists
    elif name == "create_checklist":
        return await client.create_checklist(args["task_id"], args["name"], args.get("custom_task_ids", False), args.get("team_id"))
    elif name == "update_checklist":
        return await client.update_checklist(args["checklist_id"], args["name"])
    elif name == "delete_checklist":
        return await client.delete_checklist(args["checklist_id"])
    elif name == "create_checklist_item":
        return await client.create_checklist_item(args["checklist_id"], args["name"], args.get("assignee"))
    elif name == "update_checklist_item":
        return await client.update_checklist_item(
            args["checklist_id"],
            args["checklist_item_id"],
            args.get("name"),
            args.get("resolved"),
            args.get("assignee"),
            args.get("parent"),
        )
    elif name == "delete_checklist_item":
        return await client.delete_checklist_item(args["checklist_id"], args["checklist_item_id"])

    # Task Relationships
    elif name == "add_dependency":
        return await client.add_dependency(
            args["task_id"],
            args.get("depends_on"),
            args.get("dependency_of"),
            args.get("custom_task_ids", False),
            args.get("team_id"),
        )
    elif name == "delete_dependency":
        return await client.delete_dependency(
            args["task_id"],
            args.get("depends_on"),
            args.get("dependency_of"),
            args.get("custom_task_ids", False),
            args.get("team_id"),
        )
    elif name == "add_task_link":
        return await client.add_task_link(args["task_id"], args["links_to"], args.get("custom_task_ids", False), args.get("team_id"))
    elif name == "delete_task_link":
        return await client.delete_task_link(args["task_id"], args["links_to"], args.get("custom_task_ids", False), args.get("team_id"))

    # Comments
    elif name == "get_task_comments":
        return await client.get_task_comments(
            args["task_id"],
            args.get("custom_task_ids", False),
            args.get("team_id"),
            args.get("start"),
            args.get("start_id"),
        )
    elif name == "create_task_comment":
        return await client.create_task_comment(
            args["task_id"],
            args["comment_text"],
            args.get("assignee"),
            args.get("notify_all", False),
            args.get("custom_task_ids", False),
            args.get("team_id"),
        )
    elif name == "get_list_comments":
        return await client.get_list_comments(args["list_id"], args.get("start"), args.get("start_id"))
    elif name == "create_list_comment":
        return await client.create_list_comment(args["list_id"], args["comment_text"], args.get("assignee"), args.get("notify_all", False))
    elif name == "get_chat_view_comments":
        return await client.get_chat_view_comments(args["view_id"], args.get("start"), args.get("start_id"))
    elif name == "create_chat_view_comment":
        return await client.create_chat_view_comment(args["view_id"], args["comment_text"], args.get("notify_all", False))
    elif name == "update_comment":
        return await client.update_comment(args["comment_id"], args["comment_text"], args.get("resolved"))
    elif name == "delete_comment":
        return await client.delete_comment(args["comment_id"])
    elif name == "get_threaded_comments":
        return await client.get_threaded_comments(args["comment_id"], args.get("start"), args.get("start_id"))
    elif name == "create_threaded_comment":
        return await client.create_threaded_comment(args["comment_id"], args["comment_text"], args.get("notify_all", False))

    # Attachments
    elif name == "create_task_attachment":
        return await client.create_task_attachment(
            args["task_id"],
            args["file_path"],
            args.get("filename"),
            args.get("custom_task_ids", False),
            args.get("team_id"),
        )
    elif name == "get_attachments":
        return await client.get_attachments(
            args["team_id"],
            args["entity_id"],
            args.get("entity_type", "tasks"),
            args.get("cursor"),
            args.get("limit"),
        )
    elif name == "create_attachment_v3":
        return await client.create_attachment_v3(
            args["team_id"],
            args["entity_id"],
            args["file_path"],
            args.get("entity_type", "tasks"),
            args.get("filename"),
        )

    # Custom Fields
    elif name == "get_list_custom_fields":
        return await client.get_accessible_custom_fields(args["list_id"])
    elif name == "get_folder_custom_fields":
        return await client.get_folder_custom_fields(args["folder_id"])
    elif name == "get_space_custom_fields":
        return await client.get_space_custom_fields(args["space_id"])
    elif name == "get_workspace_custom_fields":
        return await client.get_workspace_custom_fields(args["team_id"])
    elif name == "set_custom_field_value":
        value = args["value"]
        # Clients sometimes deliver the untyped `value` as a JSON string
        # (e.g. '["uuid"]' for a labels field). ClickUp then rejects it with
        # "Value must be an array". If the string parses as JSON structure,
        # unwrap it; plain strings (text fields, "3" for emoji) pass through.
        if isinstance(value, str):
            stripped = value.strip()
            if stripped[:1] in ("[", "{"):
                import json as _json

                try:
                    value = _json.loads(stripped)
                except ValueError:
                    pass
        return await client.set_custom_field_value(
            args["task_id"],
            args["field_id"],
            value,
            args.get("custom_task_ids", False),
            args.get("team_id"),
        )
    elif name == "remove_custom_field_value":
        return await client.remove_custom_field_value(
            args["task_id"],
            args["field_id"],
            args.get("custom_task_ids", False),
            args.get("team_id"),
        )

    # Custom Task Types
    elif name == "get_custom_task_types":
        return await client.get_custom_task_types(args["team_id"])

    # Tags
    elif name == "get_space_tags":
        return await client.get_space_tags(args["space_id"])
    elif name == "create_space_tag":
        return await client.create_space_tag(args["space_id"], args["name"], args.get("tag_bg"), args.get("tag_fg"))
    elif name == "update_space_tag":
        return await client.update_space_tag(args["space_id"], args["tag_name"], args["new_name"], args.get("tag_bg"), args.get("tag_fg"))
    elif name == "delete_space_tag":
        return await client.delete_space_tag(args["space_id"], args["tag_name"])
    elif name == "add_tag_to_task":
        return await client.add_tag_to_task(args["task_id"], args["tag_name"], args.get("custom_task_ids", False), args.get("team_id"))
    elif name == "remove_tag_from_task":
        return await client.remove_tag_from_task(args["task_id"], args["tag_name"], args.get("custom_task_ids", False), args.get("team_id"))

    # Goals
    elif name == "get_goals":
        return await client.get_goals(args["team_id"], args.get("include_completed", False))
    elif name == "create_goal":
        return await client.create_goal(
            args["team_id"],
            args["name"],
            args.get("due_date"),
            args.get("description"),
            args.get("multiple_owners", False),
            args.get("owners"),
            args.get("color"),
        )
    elif name == "get_goal":
        return await client.get_goal(args["goal_id"])
    elif name == "update_goal":
        goal_id = args.pop("goal_id")
        return await client.update_goal(goal_id, **args)
    elif name == "delete_goal":
        return await client.delete_goal(args["goal_id"])
    elif name == "create_key_result":
        return await client.create_key_result(
            args["goal_id"],
            args["name"],
            args["type"],
            args.get("steps_start", 0),
            args.get("steps_end", 10),
            args.get("unit"),
            args.get("owners"),
            args.get("task_ids"),
            args.get("list_ids"),
        )
    elif name == "update_key_result":
        key_result_id = args.pop("key_result_id")
        return await client.update_key_result(key_result_id, **args)
    elif name == "delete_key_result":
        return await client.delete_key_result(args["key_result_id"])

    # Time Tracking
    elif name == "get_time_entries":
        return await client.get_time_entries(**args)
    elif name == "create_time_entry":
        return await client.create_time_entry(
            args["team_id"],
            args["start"],
            args["duration"],
            args.get("task_id"),
            args.get("description"),
            args.get("billable", False),
            args.get("tags"),
            args.get("custom_task_ids", False),
        )
    elif name == "get_time_entry":
        return await client.get_time_entry(args["team_id"], args["timer_id"], args.get("include_task", False), args.get("include_location_names", False))
    elif name == "update_time_entry":
        team_id = args.pop("team_id")
        timer_id = args.pop("timer_id")
        return await client.update_time_entry(team_id, timer_id, **args)
    elif name == "delete_time_entry":
        return await client.delete_time_entry(args["team_id"], args["timer_id"])
    elif name == "get_time_entry_history":
        return await client.get_time_entry_history(args["team_id"], args["timer_id"])
    elif name == "get_running_time_entry":
        return await client.get_running_time_entry(args["team_id"], args.get("assignee"))
    elif name == "start_time_entry":
        return await client.start_time_entry(
            args["team_id"],
            args["task_id"],
            args.get("description"),
            args.get("billable", False),
            args.get("tags"),
            args.get("custom_task_ids", False),
        )
    elif name == "stop_time_entry":
        return await client.stop_time_entry(args["team_id"])
    elif name == "get_time_entry_tags":
        return await client.get_time_entry_tags(args["team_id"])
    elif name == "add_tags_to_time_entries":
        return await client.add_tags_to_time_entries(args["team_id"], args["time_entry_ids"], args["tags"])
    elif name == "remove_tags_from_time_entries":
        return await client.remove_tags_from_time_entries(args["team_id"], args["time_entry_ids"], args["tags"])
    elif name == "update_time_entry_tags":
        return await client.update_time_entry_tags(args["team_id"], args["name"], args["new_name"], args["tag_bg"], args["tag_fg"])

    # Members
    elif name == "get_task_members":
        return await client.get_task_members(args["task_id"])
    elif name == "get_list_members":
        return await client.get_list_members(args["list_id"])

    # Users
    elif name == "invite_user_to_workspace":
        return await client.invite_user_to_workspace(args["team_id"], args["email"], args.get("admin", False), args.get("custom_role_id"))
    elif name == "get_user":
        return await client.get_user(args["team_id"], args["user_id"])
    elif name == "update_user":
        team_id = args.pop("team_id")
        user_id = args.pop("user_id")
        return await client.update_user(team_id, user_id, **args)
    elif name == "remove_user_from_workspace":
        return await client.remove_user_from_workspace(args["team_id"], args["user_id"])

    # Guests
    elif name == "invite_guest_to_workspace":
        return await client.invite_guest_to_workspace(
            args["team_id"],
            args["email"],
            args.get("can_edit_tags", False),
            args.get("can_see_time_spent", False),
            args.get("can_see_time_estimated", False),
            args.get("can_create_views", False),
        )
    elif name == "get_guest":
        return await client.get_guest(args["team_id"], args["guest_id"])
    elif name == "update_guest":
        team_id = args.pop("team_id")
        guest_id = args.pop("guest_id")
        return await client.update_guest(team_id, guest_id, **args)
    elif name == "remove_guest_from_workspace":
        return await client.remove_guest_from_workspace(args["team_id"], args["guest_id"])
    elif name == "add_guest_to_task":
        return await client.add_guest_to_task(args["task_id"], args["guest_id"], args["permission_level"])
    elif name == "remove_guest_from_task":
        return await client.remove_guest_from_task(args["task_id"], args["guest_id"])
    elif name == "add_guest_to_list":
        return await client.add_guest_to_list(args["list_id"], args["guest_id"], args["permission_level"])
    elif name == "remove_guest_from_list":
        return await client.remove_guest_from_list(args["list_id"], args["guest_id"])
    elif name == "add_guest_to_folder":
        return await client.add_guest_to_folder(args["folder_id"], args["guest_id"], args["permission_level"])
    elif name == "remove_guest_from_folder":
        return await client.remove_guest_from_folder(args["folder_id"], args["guest_id"])

    # User Groups
    elif name == "get_user_groups":
        return await client.get_user_groups(args["team_id"])
    elif name == "create_user_group":
        return await client.create_user_group(args["team_id"], args["name"], args.get("member_ids"))
    elif name == "update_user_group":
        return await client.update_user_group(args["group_id"], args.get("name"), args.get("member_ids_to_add"), args.get("member_ids_to_remove"))
    elif name == "delete_user_group":
        return await client.delete_user_group(args["group_id"])

    # Roles
    elif name == "get_custom_roles":
        return await client.get_custom_roles(args["team_id"])

    # Views
    elif name == "get_workspace_views":
        return await client.get_workspace_views(args["team_id"])
    elif name == "create_workspace_view":
        team_id = args.pop("team_id")
        name = args.pop("name")
        type_ = args.pop("type")
        return await client.create_workspace_view(team_id, name, type_, **args)
    elif name == "get_space_views":
        return await client.get_space_views(args["space_id"])
    elif name == "create_space_view":
        space_id = args.pop("space_id")
        name = args.pop("name")
        type_ = args.pop("type")
        return await client.create_space_view(space_id, name, type_, **args)
    elif name == "get_folder_views":
        return await client.get_folder_views(args["folder_id"])
    elif name == "create_folder_view":
        folder_id = args.pop("folder_id")
        name = args.pop("name")
        type_ = args.pop("type")
        return await client.create_folder_view(folder_id, name, type_, **args)
    elif name == "get_list_views":
        return await client.get_list_views(args["list_id"])
    elif name == "create_list_view":
        list_id = args.pop("list_id")
        name = args.pop("name")
        type_ = args.pop("type")
        return await client.create_list_view(list_id, name, type_, **args)
    elif name == "get_view":
        return await client.get_view(args["view_id"])
    elif name == "update_view":
        view_id = args.pop("view_id")
        return await client.update_view(view_id, **args)
    elif name == "delete_view":
        return await client.delete_view(args["view_id"])
    elif name == "get_view_tasks":
        return await client.get_view_tasks(args["view_id"], args.get("page", 0))

    # Webhooks
    elif name == "get_webhooks":
        return await client.get_webhooks(args["team_id"])
    elif name == "create_webhook":
        return await client.create_webhook(
            args["team_id"],
            args["endpoint"],
            args["events"],
            args.get("space_id"),
            args.get("folder_id"),
            args.get("list_id"),
            args.get("task_id"),
        )
    elif name == "update_webhook":
        return await client.update_webhook(args["webhook_id"], args.get("endpoint"), args.get("events"), args.get("status"))
    elif name == "delete_webhook":
        return await client.delete_webhook(args["webhook_id"])

    # Templates
    elif name == "get_task_templates":
        return await client.get_task_templates(args["team_id"], args.get("page", 0))
    elif name == "get_folder_templates":
        return await client.get_folder_templates(args["team_id"])
    elif name == "get_list_templates":
        return await client.get_list_templates(args["team_id"])
    elif name == "create_folder_from_template":
        return await client.create_folder_from_template(args["space_id"], args["template_id"], args["name"], args.get("options"))
    elif name == "create_list_from_template_in_folder":
        return await client.create_list_from_template_in_folder(args["folder_id"], args["template_id"], args["name"], args.get("options"))
    elif name == "create_list_from_template_in_space":
        return await client.create_list_from_template_in_space(args["space_id"], args["template_id"], args["name"], args.get("options"))

    # Shared Hierarchy
    elif name == "get_shared_hierarchy":
        return await client.get_shared_hierarchy(args["team_id"])

    # Docs (API v3)
    elif name == "search_docs":
        return await client.search_docs(args["team_id"], args.get("query"), args.get("cursor"))
    elif name == "create_doc":
        return await client.create_doc(args["team_id"], args["name"], args.get("parent"), args.get("visibility"), args.get("create_page"))
    elif name == "get_doc":
        return await client.get_doc(args["team_id"], args["doc_id"])
    elif name == "get_doc_page_listing":
        return await client.get_doc_page_listing(args["team_id"], args["doc_id"])
    elif name == "get_doc_pages":
        return await client.get_doc_pages(args["team_id"], args["doc_id"], args.get("content_format", "text/md"))
    elif name == "get_doc_page":
        return await client.get_doc_page(args["team_id"], args["doc_id"], args["page_id"], args.get("content_format", "text/md"))
    elif name == "create_doc_page":
        return await client.create_doc_page(
            args["team_id"], args["doc_id"], args["name"], args["content"],
            args.get("parent_page_id"), args.get("sub_title"), args.get("content_format", "text/md"),
        )
    elif name == "update_doc_page":
        return await client.update_doc_page(
            args["team_id"], args["doc_id"], args["page_id"], args.get("content"),
            args.get("name"), args.get("sub_title"), args.get("content_edit_mode", "append"),
            args.get("content_format", "text/md"),
        )

    # Chat (API v3)
    elif name == "get_chat_channels":
        return await client.get_chat_channels(
            args["team_id"],
            args.get("cursor"),
            args.get("limit"),
            args.get("is_follower"),
            args.get("include_closed"),
            args.get("with_message_since"),
        )
    elif name == "get_chat_channel":
        return await client.get_chat_channel(args["team_id"], args["channel_id"])
    elif name == "create_chat_channel":
        team_id = args.pop("team_id")
        channel_name = args.pop("name")
        return await client.create_chat_channel(team_id, channel_name, **args)
    elif name == "update_chat_channel":
        team_id = args.pop("team_id")
        channel_id = args.pop("channel_id")
        return await client.update_chat_channel(team_id, channel_id, **args)
    elif name == "delete_chat_channel":
        return await client.delete_chat_channel(args["team_id"], args["channel_id"])
    elif name == "create_chat_dm_channel":
        return await client.create_chat_dm_channel(args["team_id"], args["user_ids"])
    elif name == "create_chat_location_channel":
        team_id = args.pop("team_id")
        location = args.pop("location")
        return await client.create_chat_location_channel(team_id, location, **args)
    elif name == "get_chat_channel_members":
        return await client.get_chat_channel_members(args["team_id"], args["channel_id"], args.get("cursor"), args.get("limit"))
    elif name == "get_chat_channel_followers":
        return await client.get_chat_channel_followers(args["team_id"], args["channel_id"], args.get("cursor"), args.get("limit"))
    elif name == "get_chat_messages":
        return await client.get_chat_messages(
            args["team_id"], args["channel_id"], args.get("cursor"), args.get("limit"), args.get("content_format")
        )
    elif name == "send_chat_message":
        team_id = args.pop("team_id")
        channel_id = args.pop("channel_id")
        content = args.pop("content")
        msg_type = args.pop("msg_type", "message")
        return await client.send_chat_message(team_id, channel_id, content, msg_type, **args)
    elif name == "send_chat_reply":
        team_id = args.pop("team_id")
        message_id = args.pop("message_id")
        content = args.pop("content")
        msg_type = args.pop("msg_type", "message")
        return await client.send_chat_reply(team_id, message_id, content, msg_type, **args)
    elif name == "update_chat_message":
        team_id = args.pop("team_id")
        message_id = args.pop("message_id")
        return await client.update_chat_message(team_id, message_id, **args)
    elif name == "delete_chat_message":
        return await client.delete_chat_message(args["team_id"], args["message_id"])
    elif name == "get_chat_message_replies":
        return await client.get_chat_message_replies(
            args["team_id"], args["message_id"], args.get("cursor"), args.get("limit"), args.get("content_format")
        )
    elif name == "get_chat_message_tagged_users":
        return await client.get_chat_message_tagged_users(args["team_id"], args["message_id"], args.get("cursor"), args.get("limit"))
    elif name == "create_chat_reaction":
        return await client.create_chat_reaction(args["team_id"], args["message_id"], args["reaction"])
    elif name == "delete_chat_reaction":
        return await client.delete_chat_reaction(args["team_id"], args["message_id"], args["reaction"])
    elif name == "get_chat_message_reactions":
        return await client.get_chat_message_reactions(args["team_id"], args["message_id"], args.get("cursor"), args.get("limit"))
    elif name == "get_chat_post_subtypes":
        return await client.get_chat_post_subtypes(args["team_id"], args.get("comment_type", "post"))

    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    """Run the MCP server."""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
