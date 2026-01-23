# ClickUp MCP Server

A comprehensive Model Context Protocol (MCP) server for the ClickUp API v2, providing full coverage of all available endpoints.

## Features

- **Complete API Coverage**: 120+ tools covering all ClickUp API v2 endpoints
- **Type-Safe**: Full type hints and Pydantic validation
- **Async**: Built on async/await for efficient operation
- **No Hardcoded Secrets**: API token via environment variable

## Installation

```bash
# Using pip
pip install clickup-mcp

# From source
git clone https://github.com/Yes-Gaming/clickup-mcp.git
cd clickup-mcp
pip install -e .
```

## Configuration

Set your ClickUp API token as an environment variable:

```bash
export CLICKUP_API_TOKEN="pk_your_token_here"
```

You can get your personal API token from ClickUp Settings > Apps > API Token.

### Claude Desktop Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "clickup": {
      "command": "clickup-mcp",
      "env": {
        "CLICKUP_API_TOKEN": "pk_your_token_here"
      }
    }
  }
}
```

Or using uvx:

```json
{
  "mcpServers": {
    "clickup": {
      "command": "uvx",
      "args": ["clickup-mcp"],
      "env": {
        "CLICKUP_API_TOKEN": "pk_your_token_here"
      }
    }
  }
}
```

## Available Tools (120+)

### Authorization (1)
| Tool | Description |
|------|-------------|
| `get_authorized_user` | Get authenticated user info |

### Workspaces (3)
| Tool | Description |
|------|-------------|
| `get_workspaces` | Get all workspaces |
| `get_workspace_seats` | Get workspace seat info |
| `get_workspace_plan` | Get workspace plan info |

### Spaces (5)
| Tool | Description |
|------|-------------|
| `get_spaces` | List spaces in workspace |
| `create_space` | Create a space |
| `get_space` | Get space details |
| `update_space` | Update a space |
| `delete_space` | Delete a space |

### Folders (5)
| Tool | Description |
|------|-------------|
| `get_folders` | List folders in space |
| `create_folder` | Create a folder |
| `get_folder` | Get folder details |
| `update_folder` | Update a folder |
| `delete_folder` | Delete a folder |

### Lists (10)
| Tool | Description |
|------|-------------|
| `get_lists` | List lists in folder |
| `create_list` | Create list in folder |
| `get_folderless_lists` | Get lists not in folders |
| `create_folderless_list` | Create list in space |
| `get_list` | Get list details |
| `update_list` | Update a list |
| `delete_list` | Delete a list |
| `add_task_to_list` | Add task to list |
| `remove_task_from_list` | Remove task from list |

### Tasks (11)
| Tool | Description |
|------|-------------|
| `get_tasks` | Get tasks in list |
| `create_task` | Create a task |
| `get_task` | Get task details |
| `update_task` | Update a task |
| `delete_task` | Delete a task |
| `get_filtered_team_tasks` | Filter tasks across workspace |
| `get_task_time_in_status` | Get time in each status |
| `get_bulk_tasks_time_in_status` | Bulk time in status |
| `create_task_from_template` | Create from template |

### Task Checklists (6)
| Tool | Description |
|------|-------------|
| `create_checklist` | Create checklist on task |
| `update_checklist` | Update checklist |
| `delete_checklist` | Delete checklist |
| `create_checklist_item` | Add checklist item |
| `update_checklist_item` | Update item (mark done, etc) |
| `delete_checklist_item` | Delete item |

### Task Relationships (4)
| Tool | Description |
|------|-------------|
| `add_dependency` | Add task dependency |
| `delete_dependency` | Remove dependency |
| `add_task_link` | Link two tasks |
| `delete_task_link` | Unlink tasks |

### Comments (10)
| Tool | Description |
|------|-------------|
| `get_task_comments` | Get task comments |
| `create_task_comment` | Add task comment |
| `get_list_comments` | Get list comments |
| `create_list_comment` | Add list comment |
| `get_chat_view_comments` | Get chat view comments |
| `create_chat_view_comment` | Add chat view comment |
| `update_comment` | Update comment |
| `delete_comment` | Delete comment |
| `get_threaded_comments` | Get comment replies |
| `create_threaded_comment` | Reply to comment |

### Attachments (1)
| Tool | Description |
|------|-------------|
| `create_task_attachment` | Upload file to task |

### Custom Fields (7)
| Tool | Description |
|------|-------------|
| `get_list_custom_fields` | Get list fields |
| `get_folder_custom_fields` | Get folder fields |
| `get_space_custom_fields` | Get space fields |
| `get_workspace_custom_fields` | Get all workspace fields |
| `set_custom_field_value` | Set field on task |
| `remove_custom_field_value` | Remove field from task |
| `get_custom_task_types` | Get custom task types |

### Tags (6)
| Tool | Description |
|------|-------------|
| `get_space_tags` | Get tags in space |
| `create_space_tag` | Create a tag |
| `update_space_tag` | Update tag |
| `delete_space_tag` | Delete tag |
| `add_tag_to_task` | Tag a task |
| `remove_tag_from_task` | Untag a task |

### Goals & Key Results (8)
| Tool | Description |
|------|-------------|
| `get_goals` | Get workspace goals |
| `create_goal` | Create a goal |
| `get_goal` | Get goal details |
| `update_goal` | Update a goal |
| `delete_goal` | Delete a goal |
| `create_key_result` | Create key result |
| `update_key_result` | Update key result |
| `delete_key_result` | Delete key result |

### Time Tracking (14)
| Tool | Description |
|------|-------------|
| `get_time_entries` | Get time entries |
| `create_time_entry` | Log time entry |
| `get_time_entry` | Get single entry |
| `update_time_entry` | Update entry |
| `delete_time_entry` | Delete entry |
| `get_time_entry_history` | Get entry history |
| `get_running_time_entry` | Get running timer |
| `start_time_entry` | Start timer |
| `stop_time_entry` | Stop timer |
| `get_time_entry_tags` | Get time tags |
| `add_tags_to_time_entries` | Add tags to entries |
| `remove_tags_from_time_entries` | Remove tags |
| `update_time_entry_tags` | Rename tags |

### Members (2)
| Tool | Description |
|------|-------------|
| `get_task_members` | Get task members |
| `get_list_members` | Get list members |

### Users (4)
| Tool | Description |
|------|-------------|
| `invite_user_to_workspace` | Invite user |
| `get_user` | Get user info |
| `update_user` | Update user |
| `remove_user_from_workspace` | Remove user |

### Guests (10)
| Tool | Description |
|------|-------------|
| `invite_guest_to_workspace` | Invite guest |
| `get_guest` | Get guest info |
| `update_guest` | Update guest |
| `remove_guest_from_workspace` | Remove guest |
| `add_guest_to_task` | Add guest to task |
| `remove_guest_from_task` | Remove from task |
| `add_guest_to_list` | Add guest to list |
| `remove_guest_from_list` | Remove from list |
| `add_guest_to_folder` | Add guest to folder |
| `remove_guest_from_folder` | Remove from folder |

### User Groups (4)
| Tool | Description |
|------|-------------|
| `get_user_groups` | Get groups |
| `create_user_group` | Create group |
| `update_user_group` | Update group |
| `delete_user_group` | Delete group |

### Roles (1)
| Tool | Description |
|------|-------------|
| `get_custom_roles` | Get custom roles |

### Views (12)
| Tool | Description |
|------|-------------|
| `get_workspace_views` | Get workspace views |
| `create_workspace_view` | Create workspace view |
| `get_space_views` | Get space views |
| `create_space_view` | Create space view |
| `get_folder_views` | Get folder views |
| `create_folder_view` | Create folder view |
| `get_list_views` | Get list views |
| `create_list_view` | Create list view |
| `get_view` | Get view details |
| `update_view` | Update view |
| `delete_view` | Delete view |
| `get_view_tasks` | Get tasks in view |

### Webhooks (4)
| Tool | Description |
|------|-------------|
| `get_webhooks` | Get webhooks |
| `create_webhook` | Create webhook |
| `update_webhook` | Update webhook |
| `delete_webhook` | Delete webhook |

### Templates (1)
| Tool | Description |
|------|-------------|
| `get_task_templates` | Get task templates |

### Shared Hierarchy (1)
| Tool | Description |
|------|-------------|
| `get_shared_hierarchy` | Get shared items |

## Usage Examples

### Get all workspaces
```python
# The tool will return all workspaces you have access to
result = await get_workspaces()
```

### Create a task
```python
result = await create_task(
    list_id="12345",
    name="My new task",
    description="Task description",
    priority=2,  # High priority
    assignees=[12345678],
    due_date=1735689600000  # Unix timestamp in ms
)
```

### Start time tracking
```python
result = await start_time_entry(
    team_id="123456",
    task_id="abc123",
    description="Working on feature",
    billable=True
)
```

### Create a webhook
```python
result = await create_webhook(
    team_id="123456",
    endpoint="https://your-server.com/webhook",
    events=["taskCreated", "taskUpdated"],
    space_id="789"  # Optional: limit to specific space
)
```

## Webhook Events

Available webhook events:
- Task: `taskCreated`, `taskUpdated`, `taskDeleted`, `taskPriorityUpdated`, `taskStatusUpdated`, `taskAssigneeUpdated`, `taskDueDateUpdated`, `taskTagUpdated`, `taskMoved`, `taskCommentPosted`, `taskCommentUpdated`, `taskTimeEstimateUpdated`, `taskTimeTrackedUpdated`
- List: `listCreated`, `listUpdated`, `listDeleted`
- Folder: `folderCreated`, `folderUpdated`, `folderDeleted`
- Space: `spaceCreated`, `spaceUpdated`, `spaceDeleted`
- Goal: `goalCreated`, `goalUpdated`, `goalDeleted`
- Key Result: `keyResultCreated`, `keyResultUpdated`, `keyResultDeleted`

Use `*` to subscribe to all events.

## API Reference

This MCP server implements the [ClickUp API v2](https://developer.clickup.com/). For detailed parameter documentation, refer to the official API docs.

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check .
```

## License

MIT License - see LICENSE file.

## Contributing

Contributions welcome! Please open an issue or PR on GitHub.
