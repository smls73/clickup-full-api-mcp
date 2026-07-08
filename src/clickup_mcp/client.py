"""ClickUp API client with full endpoint coverage."""

import os
from typing import Any, Optional
from urllib.parse import urlencode

import httpx


class ClickUpClient:
    """Async HTTP client for ClickUp API v2."""

    BASE_URL = "https://api.clickup.com/api/v2"

    def __init__(self, api_token: Optional[str] = None):
        """Initialize client with API token from param or environment."""
        self.api_token = api_token or os.environ.get("CLICKUP_API_TOKEN")
        if not self.api_token:
            raise ValueError(
                "ClickUp API token required. Set CLICKUP_API_TOKEN environment variable "
                "or pass api_token parameter."
            )
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers={
                    "Authorization": self.api_token,
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        json: Optional[dict] = None,
        data: Optional[Any] = None,
        files: Optional[dict] = None,
    ) -> dict:
        """Make an API request."""
        # Remove None values from params
        if params:
            params = {k: v for k, v in params.items() if v is not None}

        # Handle file uploads differently
        if files:
            headers = {"Authorization": self.api_token}
            upload_url = endpoint if endpoint.startswith("http") else f"{self.BASE_URL}{endpoint}"
            async with httpx.AsyncClient(timeout=60.0) as upload_client:
                response = await upload_client.request(
                    method=method,
                    url=upload_url,
                    headers=headers,
                    params=params,
                    files=files,
                )
        else:
            response = await self.client.request(
                method=method,
                url=endpoint,
                params=params,
                json=json,
            )

        if response.status_code >= 400:
            error_detail = response.text
            try:
                error_json = response.json()
                error_detail = error_json.get("err", error_json.get("error", error_detail))
            except Exception:
                pass
            raise httpx.HTTPStatusError(
                f"ClickUp API error: {error_detail}",
                request=response.request,
                response=response,
            )

        if response.status_code == 204:
            return {"success": True}

        return response.json()

    async def get(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """GET request."""
        return await self._request("GET", endpoint, params=params)

    async def post(
        self,
        endpoint: str,
        json: Optional[dict] = None,
        params: Optional[dict] = None,
        files: Optional[dict] = None,
    ) -> dict:
        """POST request."""
        return await self._request("POST", endpoint, params=params, json=json, files=files)

    async def put(self, endpoint: str, json: Optional[dict] = None, params: Optional[dict] = None) -> dict:
        """PUT request."""
        return await self._request("PUT", endpoint, params=params, json=json)

    async def delete(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """DELETE request."""
        return await self._request("DELETE", endpoint, params=params)

    # ===== Authorization =====

    async def get_authorized_user(self) -> dict:
        """Get the authorized user."""
        return await self.get("/user")

    # ===== Workspaces (Teams) =====

    async def get_workspaces(self) -> dict:
        """Get authorized workspaces (teams)."""
        return await self.get("/team")

    async def get_workspace_seats(self, team_id: str) -> dict:
        """Get workspace seats."""
        return await self.get(f"/team/{team_id}/seats")

    async def get_workspace_plan(self, team_id: str) -> dict:
        """Get workspace plan."""
        return await self.get(f"/team/{team_id}/plan")

    # ===== Spaces =====

    async def get_spaces(self, team_id: str, archived: bool = False) -> dict:
        """Get spaces in a workspace."""
        return await self.get(f"/team/{team_id}/space", params={"archived": str(archived).lower()})

    async def create_space(self, team_id: str, name: str, **kwargs) -> dict:
        """Create a space."""
        data = {"name": name, **kwargs}
        return await self.post(f"/team/{team_id}/space", json=data)

    async def get_space(self, space_id: str) -> dict:
        """Get a space."""
        return await self.get(f"/space/{space_id}")

    async def update_space(self, space_id: str, **kwargs) -> dict:
        """Update a space."""
        return await self.put(f"/space/{space_id}", json=kwargs)

    async def delete_space(self, space_id: str) -> dict:
        """Delete a space."""
        return await self.delete(f"/space/{space_id}")

    # ===== Folders =====

    async def get_folders(self, space_id: str, archived: bool = False) -> dict:
        """Get folders in a space."""
        return await self.get(f"/space/{space_id}/folder", params={"archived": str(archived).lower()})

    async def create_folder(self, space_id: str, name: str) -> dict:
        """Create a folder."""
        return await self.post(f"/space/{space_id}/folder", json={"name": name})

    async def get_folder(self, folder_id: str) -> dict:
        """Get a folder."""
        return await self.get(f"/folder/{folder_id}")

    async def update_folder(self, folder_id: str, name: str) -> dict:
        """Update a folder."""
        return await self.put(f"/folder/{folder_id}", json={"name": name})

    async def delete_folder(self, folder_id: str) -> dict:
        """Delete a folder."""
        return await self.delete(f"/folder/{folder_id}")

    # ===== Lists =====

    async def get_lists(self, folder_id: str, archived: bool = False) -> dict:
        """Get lists in a folder."""
        return await self.get(f"/folder/{folder_id}/list", params={"archived": str(archived).lower()})

    async def create_list(self, folder_id: str, name: str, **kwargs) -> dict:
        """Create a list in a folder."""
        data = {"name": name, **kwargs}
        return await self.post(f"/folder/{folder_id}/list", json=data)

    async def get_folderless_lists(self, space_id: str, archived: bool = False) -> dict:
        """Get folderless lists in a space."""
        return await self.get(f"/space/{space_id}/list", params={"archived": str(archived).lower()})

    async def create_folderless_list(self, space_id: str, name: str, **kwargs) -> dict:
        """Create a folderless list."""
        data = {"name": name, **kwargs}
        return await self.post(f"/space/{space_id}/list", json=data)

    async def get_list(self, list_id: str) -> dict:
        """Get a list."""
        return await self.get(f"/list/{list_id}")

    async def update_list(self, list_id: str, **kwargs) -> dict:
        """Update a list."""
        return await self.put(f"/list/{list_id}", json=kwargs)

    async def delete_list(self, list_id: str) -> dict:
        """Delete a list."""
        return await self.delete(f"/list/{list_id}")

    async def add_task_to_list(self, list_id: str, task_id: str) -> dict:
        """Add a task to a list."""
        return await self.post(f"/list/{list_id}/task/{task_id}")

    async def remove_task_from_list(self, list_id: str, task_id: str) -> dict:
        """Remove a task from a list."""
        return await self.delete(f"/list/{list_id}/task/{task_id}")

    # ===== Tasks =====

    async def get_tasks(
        self,
        list_id: str,
        archived: bool = False,
        include_closed: bool = False,
        page: int = 0,
        order_by: Optional[str] = None,
        reverse: bool = False,
        subtasks: bool = False,
        statuses: Optional[list[str]] = None,
        include_markdown_description: bool = False,
        assignees: Optional[list[str]] = None,
        tags: Optional[list[str]] = None,
        due_date_gt: Optional[int] = None,
        due_date_lt: Optional[int] = None,
        date_created_gt: Optional[int] = None,
        date_created_lt: Optional[int] = None,
        date_updated_gt: Optional[int] = None,
        date_updated_lt: Optional[int] = None,
        date_done_gt: Optional[int] = None,
        date_done_lt: Optional[int] = None,
        custom_fields: Optional[list[dict]] = None,
        custom_items: Optional[list[int]] = None,
        watchers: Optional[list[str]] = None,
        include_timl: bool = False,
    ) -> dict:
        """Get tasks in a list."""
        import json as _json

        params = {
            "archived": str(archived).lower(),
            "include_closed": str(include_closed).lower(),
            "page": page,
            "reverse": str(reverse).lower(),
            "subtasks": str(subtasks).lower(),
            "include_markdown_description": str(include_markdown_description).lower(),
        }
        if include_timl:
            params["include_timl"] = "true"
        if order_by:
            params["order_by"] = order_by
        if statuses:
            params["statuses[]"] = statuses
        if assignees:
            params["assignees[]"] = assignees
        if watchers:
            params["watchers[]"] = watchers
        if tags:
            params["tags[]"] = tags
        if due_date_gt:
            params["due_date_gt"] = due_date_gt
        if due_date_lt:
            params["due_date_lt"] = due_date_lt
        if date_created_gt:
            params["date_created_gt"] = date_created_gt
        if date_created_lt:
            params["date_created_lt"] = date_created_lt
        if date_updated_gt:
            params["date_updated_gt"] = date_updated_gt
        if date_updated_lt:
            params["date_updated_lt"] = date_updated_lt
        if date_done_gt:
            params["date_done_gt"] = date_done_gt
        if date_done_lt:
            params["date_done_lt"] = date_done_lt
        if custom_fields:
            # API expects a JSON-encoded array of {field_id, operator, value} in the query string
            params["custom_fields"] = _json.dumps(custom_fields)
        if custom_items:
            params["custom_items[]"] = custom_items

        return await self.get(f"/list/{list_id}/task", params=params)

    async def create_task(self, list_id: str, name: str, **kwargs) -> dict:
        """Create a task."""
        data = {"name": name, **kwargs}
        return await self.post(f"/list/{list_id}/task", json=data)

    async def get_task(
        self,
        task_id: str,
        custom_task_ids: bool = False,
        team_id: Optional[str] = None,
        include_subtasks: bool = False,
        include_markdown_description: bool = False,
    ) -> dict:
        """Get a task."""
        params = {
            "custom_task_ids": str(custom_task_ids).lower(),
            "include_subtasks": str(include_subtasks).lower(),
            "include_markdown_description": str(include_markdown_description).lower(),
        }
        if team_id:
            params["team_id"] = team_id
        return await self.get(f"/task/{task_id}", params=params)

    async def update_task(
        self,
        task_id: str,
        custom_task_ids: bool = False,
        team_id: Optional[str] = None,
        **kwargs,
    ) -> dict:
        """Update a task."""
        params = {"custom_task_ids": str(custom_task_ids).lower()}
        if team_id:
            params["team_id"] = team_id
        return await self.put(f"/task/{task_id}", json=kwargs, params=params)

    async def delete_task(
        self,
        task_id: str,
        custom_task_ids: bool = False,
        team_id: Optional[str] = None,
    ) -> dict:
        """Delete a task."""
        params = {"custom_task_ids": str(custom_task_ids).lower()}
        if team_id:
            params["team_id"] = team_id
        return await self.delete(f"/task/{task_id}", params=params)

    async def get_filtered_team_tasks(
        self,
        team_id: str,
        page: int = 0,
        order_by: Optional[str] = None,
        reverse: bool = False,
        subtasks: bool = False,
        space_ids: Optional[list[str]] = None,
        project_ids: Optional[list[str]] = None,
        list_ids: Optional[list[str]] = None,
        statuses: Optional[list[str]] = None,
        include_closed: bool = False,
        assignees: Optional[list[str]] = None,
        tags: Optional[list[str]] = None,
        due_date_gt: Optional[int] = None,
        due_date_lt: Optional[int] = None,
        date_created_gt: Optional[int] = None,
        date_created_lt: Optional[int] = None,
        date_updated_gt: Optional[int] = None,
        date_updated_lt: Optional[int] = None,
        date_done_gt: Optional[int] = None,
        date_done_lt: Optional[int] = None,
        parent: Optional[str] = None,
        include_markdown_description: bool = False,
        custom_fields: Optional[list[dict]] = None,
        custom_items: Optional[list[int]] = None,
        **kwargs,
    ) -> dict:
        """Get filtered tasks across a workspace."""
        import json as _json

        params = {
            "page": page,
            "reverse": str(reverse).lower(),
            "subtasks": str(subtasks).lower(),
            "include_closed": str(include_closed).lower(),
            **kwargs,
        }
        if include_markdown_description:
            params["include_markdown_description"] = "true"
        if order_by:
            params["order_by"] = order_by
        if space_ids:
            params["space_ids[]"] = space_ids
        if project_ids:
            params["project_ids[]"] = project_ids
        if list_ids:
            params["list_ids[]"] = list_ids
        if statuses:
            params["statuses[]"] = statuses
        if assignees:
            params["assignees[]"] = assignees
        if tags:
            params["tags[]"] = tags
        if due_date_gt:
            params["due_date_gt"] = due_date_gt
        if due_date_lt:
            params["due_date_lt"] = due_date_lt
        if date_created_gt:
            params["date_created_gt"] = date_created_gt
        if date_created_lt:
            params["date_created_lt"] = date_created_lt
        if date_updated_gt:
            params["date_updated_gt"] = date_updated_gt
        if date_updated_lt:
            params["date_updated_lt"] = date_updated_lt
        if date_done_gt:
            params["date_done_gt"] = date_done_gt
        if date_done_lt:
            params["date_done_lt"] = date_done_lt
        if parent:
            params["parent"] = parent
        if custom_fields:
            # API expects the SINGULAR key custom_fields holding a JSON-encoded array
            params["custom_fields"] = _json.dumps(custom_fields)
        if custom_items:
            params["custom_items[]"] = custom_items

        return await self.get(f"/team/{team_id}/task", params=params)

    async def get_task_time_in_status(
        self,
        task_id: str,
        custom_task_ids: bool = False,
        team_id: Optional[str] = None,
    ) -> dict:
        """Get time a task has spent in each status."""
        params = {"custom_task_ids": str(custom_task_ids).lower()}
        if team_id:
            params["team_id"] = team_id
        return await self.get(f"/task/{task_id}/time_in_status", params=params)

    async def get_bulk_tasks_time_in_status(
        self,
        task_ids: list[str],
        custom_task_ids: bool = False,
        team_id: Optional[str] = None,
    ) -> dict:
        """Get time multiple tasks have spent in each status."""
        params = {
            "task_ids": ",".join(task_ids),
            "custom_task_ids": str(custom_task_ids).lower(),
        }
        if team_id:
            params["team_id"] = team_id
        return await self.get("/task/bulk_time_in_status/task_ids", params=params)

    async def create_task_from_template(
        self,
        list_id: str,
        template_id: str,
        name: str,
    ) -> dict:
        """Create a task from a template."""
        return await self.post(
            f"/list/{list_id}/taskTemplate/{template_id}",
            json={"name": name},
        )

    async def move_task(
        self,
        team_id: str,
        task_id: str,
        list_id: str,
        move_custom_fields: Optional[bool] = None,
        custom_fields_to_move: Optional[list[str]] = None,
        status_mappings: Optional[list[dict]] = None,
    ) -> dict:
        """Move a task to a new home list (API v3)."""
        data: dict[str, Any] = {}
        if move_custom_fields is not None:
            data["move_custom_fields"] = move_custom_fields
        if custom_fields_to_move:
            data["custom_fields_to_move"] = custom_fields_to_move
        if status_mappings:
            data["status_mappings"] = status_mappings
        return await self.put(
            f"{self.V3_URL}/workspaces/{team_id}/tasks/{task_id}/home_list/{list_id}",
            json=data,
        )

    async def merge_tasks(self, task_id: str, source_task_ids: list[str]) -> dict:
        """Merge source tasks INTO the target task (target survives). Custom task IDs not supported."""
        return await self.post(f"/task/{task_id}/merge", json={"source_task_ids": source_task_ids})

    async def update_time_estimates_by_user(self, team_id: str, task_id: str, estimates: list[dict]) -> dict:
        """Set per-user time estimates for the named assignees only (API v3, Business plan+). Body is a bare array."""
        return await self._request(
            "PATCH",
            f"{self.V3_URL}/workspaces/{team_id}/tasks/{task_id}/time_estimates_by_user",
            json=estimates,
        )

    async def replace_time_estimates_by_user(self, team_id: str, task_id: str, estimates: list[dict]) -> dict:
        """REPLACE all per-user time estimates; any estimate not in the list is removed (API v3, Business plan+)."""
        return await self.put(
            f"{self.V3_URL}/workspaces/{team_id}/tasks/{task_id}/time_estimates_by_user",
            json=estimates,
        )

    # ===== Task Checklists =====

    async def create_checklist(
        self,
        task_id: str,
        name: str,
        custom_task_ids: bool = False,
        team_id: Optional[str] = None,
    ) -> dict:
        """Create a checklist on a task."""
        params = {"custom_task_ids": str(custom_task_ids).lower()}
        if team_id:
            params["team_id"] = team_id
        return await self.post(f"/task/{task_id}/checklist", json={"name": name}, params=params)

    async def update_checklist(self, checklist_id: str, name: str) -> dict:
        """Update a checklist."""
        return await self.put(f"/checklist/{checklist_id}", json={"name": name})

    async def delete_checklist(self, checklist_id: str) -> dict:
        """Delete a checklist."""
        return await self.delete(f"/checklist/{checklist_id}")

    async def create_checklist_item(
        self,
        checklist_id: str,
        name: str,
        assignee: Optional[str] = None,
    ) -> dict:
        """Create a checklist item."""
        data = {"name": name}
        if assignee:
            data["assignee"] = assignee
        return await self.post(f"/checklist/{checklist_id}/checklist_item", json=data)

    async def update_checklist_item(
        self,
        checklist_id: str,
        checklist_item_id: str,
        name: Optional[str] = None,
        resolved: Optional[bool] = None,
        assignee: Optional[str] = None,
        parent: Optional[str] = None,
    ) -> dict:
        """Update a checklist item."""
        data = {}
        if name is not None:
            data["name"] = name
        if resolved is not None:
            data["resolved"] = resolved
        if assignee is not None:
            data["assignee"] = assignee
        if parent is not None:
            data["parent"] = parent
        return await self.put(f"/checklist/{checklist_id}/checklist_item/{checklist_item_id}", json=data)

    async def delete_checklist_item(self, checklist_id: str, checklist_item_id: str) -> dict:
        """Delete a checklist item."""
        return await self.delete(f"/checklist/{checklist_id}/checklist_item/{checklist_item_id}")

    # ===== Task Relationships =====

    async def add_dependency(
        self,
        task_id: str,
        depends_on: Optional[str] = None,
        dependency_of: Optional[str] = None,
        custom_task_ids: bool = False,
        team_id: Optional[str] = None,
    ) -> dict:
        """Add a dependency to a task."""
        params = {"custom_task_ids": str(custom_task_ids).lower()}
        if team_id:
            params["team_id"] = team_id
        data = {}
        if depends_on:
            data["depends_on"] = depends_on
        if dependency_of:
            data["dependency_of"] = dependency_of
        return await self.post(f"/task/{task_id}/dependency", json=data, params=params)

    async def delete_dependency(
        self,
        task_id: str,
        depends_on: Optional[str] = None,
        dependency_of: Optional[str] = None,
        custom_task_ids: bool = False,
        team_id: Optional[str] = None,
    ) -> dict:
        """Remove a dependency from a task."""
        params = {"custom_task_ids": str(custom_task_ids).lower()}
        if team_id:
            params["team_id"] = team_id
        if depends_on:
            params["depends_on"] = depends_on
        if dependency_of:
            params["dependency_of"] = dependency_of
        return await self.delete(f"/task/{task_id}/dependency", params=params)

    async def add_task_link(
        self,
        task_id: str,
        links_to: str,
        custom_task_ids: bool = False,
        team_id: Optional[str] = None,
    ) -> dict:
        """Link two tasks."""
        params = {"custom_task_ids": str(custom_task_ids).lower()}
        if team_id:
            params["team_id"] = team_id
        return await self.post(f"/task/{task_id}/link/{links_to}", params=params)

    async def delete_task_link(
        self,
        task_id: str,
        links_to: str,
        custom_task_ids: bool = False,
        team_id: Optional[str] = None,
    ) -> dict:
        """Unlink two tasks."""
        params = {"custom_task_ids": str(custom_task_ids).lower()}
        if team_id:
            params["team_id"] = team_id
        return await self.delete(f"/task/{task_id}/link/{links_to}", params=params)

    # ===== Comments =====

    async def get_task_comments(
        self,
        task_id: str,
        custom_task_ids: bool = False,
        team_id: Optional[str] = None,
        start: Optional[int] = None,
        start_id: Optional[str] = None,
    ) -> dict:
        """Get comments on a task."""
        params = {"custom_task_ids": str(custom_task_ids).lower()}
        if team_id:
            params["team_id"] = team_id
        if start:
            params["start"] = start
        if start_id:
            params["start_id"] = start_id
        return await self.get(f"/task/{task_id}/comment", params=params)

    async def create_task_comment(
        self,
        task_id: str,
        comment_text: str,
        assignee: Optional[str] = None,
        notify_all: bool = False,
        custom_task_ids: bool = False,
        team_id: Optional[str] = None,
    ) -> dict:
        """Create a comment on a task."""
        params = {"custom_task_ids": str(custom_task_ids).lower()}
        if team_id:
            params["team_id"] = team_id
        data = {"comment_text": comment_text, "notify_all": notify_all}
        if assignee:
            data["assignee"] = assignee
        return await self.post(f"/task/{task_id}/comment", json=data, params=params)

    async def get_list_comments(self, list_id: str, start: Optional[int] = None, start_id: Optional[str] = None) -> dict:
        """Get comments on a list."""
        params = {}
        if start:
            params["start"] = start
        if start_id:
            params["start_id"] = start_id
        return await self.get(f"/list/{list_id}/comment", params=params)

    async def create_list_comment(
        self,
        list_id: str,
        comment_text: str,
        assignee: Optional[str] = None,
        notify_all: bool = False,
    ) -> dict:
        """Create a comment on a list."""
        data = {"comment_text": comment_text, "notify_all": notify_all}
        if assignee:
            data["assignee"] = assignee
        return await self.post(f"/list/{list_id}/comment", json=data)

    async def get_chat_view_comments(
        self,
        view_id: str,
        start: Optional[int] = None,
        start_id: Optional[str] = None,
    ) -> dict:
        """Get comments in a chat view."""
        params = {}
        if start:
            params["start"] = start
        if start_id:
            params["start_id"] = start_id
        return await self.get(f"/view/{view_id}/comment", params=params)

    async def create_chat_view_comment(
        self,
        view_id: str,
        comment_text: str,
        notify_all: bool = False,
    ) -> dict:
        """Create a comment in a chat view."""
        data = {"comment_text": comment_text, "notify_all": notify_all}
        return await self.post(f"/view/{view_id}/comment", json=data)

    async def update_comment(self, comment_id: str, comment_text: str, resolved: Optional[bool] = None) -> dict:
        """Update a comment."""
        data = {"comment_text": comment_text}
        if resolved is not None:
            data["resolved"] = resolved
        return await self.put(f"/comment/{comment_id}", json=data)

    async def delete_comment(self, comment_id: str) -> dict:
        """Delete a comment."""
        return await self.delete(f"/comment/{comment_id}")

    async def get_threaded_comments(
        self,
        comment_id: str,
        start: Optional[int] = None,
        start_id: Optional[str] = None,
    ) -> dict:
        """Get threaded comments (replies)."""
        params = {}
        if start:
            params["start"] = start
        if start_id:
            params["start_id"] = start_id
        return await self.get(f"/comment/{comment_id}/reply", params=params)

    async def create_threaded_comment(
        self,
        comment_id: str,
        comment_text: str,
        notify_all: bool = False,
    ) -> dict:
        """Create a threaded comment (reply)."""
        data = {"comment_text": comment_text, "notify_all": notify_all}
        return await self.post(f"/comment/{comment_id}/reply", json=data)

    # ===== Attachments =====

    async def create_task_attachment(
        self,
        task_id: str,
        file_path: str,
        filename: Optional[str] = None,
        custom_task_ids: bool = False,
        team_id: Optional[str] = None,
    ) -> dict:
        """Upload an attachment to a task."""
        import os

        params = {"custom_task_ids": str(custom_task_ids).lower()}
        if team_id:
            params["team_id"] = team_id

        if not filename:
            filename = os.path.basename(file_path)

        with open(file_path, "rb") as f:
            files = {"attachment": (filename, f)}
            return await self.post(f"/task/{task_id}/attachment", files=files, params=params)

    async def get_attachments(
        self,
        team_id: str,
        entity_id: str,
        entity_type: str = "tasks",
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> dict:
        """Get attachments on a task or Files custom field (API v3).

        entity_type='tasks' + entity_id=<task_id> for a task;
        entity_type='custom_fields' + entity_id=<field_id> for a Files custom field.
        NOTE: ClickUp's reference doc claims 'attachments' as the task entity type —
        live-tested 2026-07-08: 'attachments' 404s, 'tasks' works."""
        params: dict[str, Any] = {}
        if cursor:
            params["cursor"] = cursor
        if limit:
            params["limit"] = limit
        return await self.get(
            f"{self.V3_URL}/workspaces/{team_id}/{entity_type}/{entity_id}/attachments",
            params=params,
        )

    async def create_attachment_v3(
        self,
        team_id: str,
        entity_id: str,
        file_path: str,
        entity_type: str = "tasks",
        filename: Optional[str] = None,
    ) -> dict:
        """Upload an attachment to a task or Files custom field (API v3, multipart).

        Live-tested 2026-07-08: entity_type must be 'tasks' (docs wrongly say
        'attachments') and the multipart field name must be 'attachment'."""
        import os

        if not filename:
            filename = os.path.basename(file_path)
        with open(file_path, "rb") as f:
            files = {"attachment": (filename, f)}
            return await self.post(
                f"{self.V3_URL}/workspaces/{team_id}/{entity_type}/{entity_id}/attachments",
                files=files,
            )

    # ===== Custom Fields =====

    async def get_accessible_custom_fields(self, list_id: str) -> dict:
        """Get custom fields available on a list."""
        return await self.get(f"/list/{list_id}/field")

    async def get_folder_custom_fields(self, folder_id: str) -> dict:
        """Get custom fields available on a folder."""
        return await self.get(f"/folder/{folder_id}/field")

    async def get_space_custom_fields(self, space_id: str) -> dict:
        """Get custom fields available on a space."""
        return await self.get(f"/space/{space_id}/field")

    async def get_workspace_custom_fields(self, team_id: str) -> dict:
        """Get all custom fields in a workspace."""
        return await self.get(f"/team/{team_id}/field")

    async def set_custom_field_value(
        self,
        task_id: str,
        field_id: str,
        value: Any,
        custom_task_ids: bool = False,
        team_id: Optional[str] = None,
    ) -> dict:
        """Set a custom field value on a task."""
        params = {"custom_task_ids": str(custom_task_ids).lower()}
        if team_id:
            params["team_id"] = team_id
        return await self.post(f"/task/{task_id}/field/{field_id}", json={"value": value}, params=params)

    async def remove_custom_field_value(
        self,
        task_id: str,
        field_id: str,
        custom_task_ids: bool = False,
        team_id: Optional[str] = None,
    ) -> dict:
        """Remove a custom field value from a task."""
        params = {"custom_task_ids": str(custom_task_ids).lower()}
        if team_id:
            params["team_id"] = team_id
        return await self.delete(f"/task/{task_id}/field/{field_id}", params=params)

    # ===== Custom Task Types =====

    async def get_custom_task_types(self, team_id: str) -> dict:
        """Get custom task types in a workspace."""
        return await self.get(f"/team/{team_id}/custom_item")

    # ===== Tags =====

    async def get_space_tags(self, space_id: str) -> dict:
        """Get tags in a space."""
        return await self.get(f"/space/{space_id}/tag")

    async def create_space_tag(self, space_id: str, name: str, tag_bg: Optional[str] = None, tag_fg: Optional[str] = None) -> dict:
        """Create a tag in a space."""
        data = {"tag": {"name": name}}
        if tag_bg:
            data["tag"]["tag_bg"] = tag_bg
        if tag_fg:
            data["tag"]["tag_fg"] = tag_fg
        return await self.post(f"/space/{space_id}/tag", json=data)

    async def update_space_tag(
        self,
        space_id: str,
        tag_name: str,
        new_name: str,
        tag_bg: Optional[str] = None,
        tag_fg: Optional[str] = None,
    ) -> dict:
        """Update a tag in a space."""
        data = {"tag": {"name": tag_name, "new_name": new_name}}
        if tag_bg:
            data["tag"]["tag_bg"] = tag_bg
        if tag_fg:
            data["tag"]["tag_fg"] = tag_fg
        return await self.put(f"/space/{space_id}/tag/{tag_name}", json=data)

    async def delete_space_tag(self, space_id: str, tag_name: str) -> dict:
        """Delete a tag from a space."""
        return await self.delete(f"/space/{space_id}/tag/{tag_name}")

    async def add_tag_to_task(
        self,
        task_id: str,
        tag_name: str,
        custom_task_ids: bool = False,
        team_id: Optional[str] = None,
    ) -> dict:
        """Add a tag to a task."""
        params = {"custom_task_ids": str(custom_task_ids).lower()}
        if team_id:
            params["team_id"] = team_id
        return await self.post(f"/task/{task_id}/tag/{tag_name}", params=params)

    async def remove_tag_from_task(
        self,
        task_id: str,
        tag_name: str,
        custom_task_ids: bool = False,
        team_id: Optional[str] = None,
    ) -> dict:
        """Remove a tag from a task."""
        params = {"custom_task_ids": str(custom_task_ids).lower()}
        if team_id:
            params["team_id"] = team_id
        return await self.delete(f"/task/{task_id}/tag/{tag_name}", params=params)

    # ===== Goals =====

    async def get_goals(self, team_id: str, include_completed: bool = False) -> dict:
        """Get goals in a workspace."""
        return await self.get(f"/team/{team_id}/goal", params={"include_completed": str(include_completed).lower()})

    async def create_goal(
        self,
        team_id: str,
        name: str,
        due_date: Optional[int] = None,
        description: Optional[str] = None,
        multiple_owners: bool = False,
        owners: Optional[list[str]] = None,
        color: Optional[str] = None,
    ) -> dict:
        """Create a goal."""
        data = {"name": name, "multiple_owners": multiple_owners}
        if due_date:
            data["due_date"] = due_date
        if description:
            data["description"] = description
        if owners:
            data["owners"] = owners
        if color:
            data["color"] = color
        return await self.post(f"/team/{team_id}/goal", json=data)

    async def get_goal(self, goal_id: str) -> dict:
        """Get a goal."""
        return await self.get(f"/goal/{goal_id}")

    async def update_goal(self, goal_id: str, **kwargs) -> dict:
        """Update a goal."""
        return await self.put(f"/goal/{goal_id}", json=kwargs)

    async def delete_goal(self, goal_id: str) -> dict:
        """Delete a goal."""
        return await self.delete(f"/goal/{goal_id}")

    async def create_key_result(
        self,
        goal_id: str,
        name: str,
        type: str,
        steps_start: int = 0,
        steps_end: int = 10,
        unit: Optional[str] = None,
        owners: Optional[list[str]] = None,
        task_ids: Optional[list[str]] = None,
        list_ids: Optional[list[str]] = None,
    ) -> dict:
        """Create a key result (target) on a goal."""
        data = {
            "name": name,
            "type": type,
            "steps_start": steps_start,
            "steps_end": steps_end,
        }
        if unit:
            data["unit"] = unit
        if owners:
            data["owners"] = owners
        if task_ids:
            data["task_ids"] = task_ids
        if list_ids:
            data["list_ids"] = list_ids
        return await self.post(f"/goal/{goal_id}/key_result", json=data)

    async def update_key_result(self, key_result_id: str, **kwargs) -> dict:
        """Update a key result."""
        return await self.put(f"/key_result/{key_result_id}", json=kwargs)

    async def delete_key_result(self, key_result_id: str) -> dict:
        """Delete a key result."""
        return await self.delete(f"/key_result/{key_result_id}")

    # ===== Time Tracking =====

    async def get_time_entries(
        self,
        team_id: str,
        start_date: Optional[int] = None,
        end_date: Optional[int] = None,
        assignee: Optional[list[str]] = None,
        include_task_tags: bool = False,
        include_location_names: bool = False,
        space_id: Optional[str] = None,
        folder_id: Optional[str] = None,
        list_id: Optional[str] = None,
        task_id: Optional[str] = None,
        custom_task_ids: bool = False,
    ) -> dict:
        """Get time entries within a date range."""
        params = {
            "include_task_tags": str(include_task_tags).lower(),
            "include_location_names": str(include_location_names).lower(),
            "custom_task_ids": str(custom_task_ids).lower(),
        }
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if assignee:
            params["assignee"] = ",".join(assignee)
        if space_id:
            params["space_id"] = space_id
        if folder_id:
            params["folder_id"] = folder_id
        if list_id:
            params["list_id"] = list_id
        if task_id:
            params["task_id"] = task_id
        return await self.get(f"/team/{team_id}/time_entries", params=params)

    async def create_time_entry(
        self,
        team_id: str,
        start: int,
        duration: int,
        task_id: Optional[str] = None,
        description: Optional[str] = None,
        billable: bool = False,
        tags: Optional[list[dict]] = None,
        custom_task_ids: bool = False,
    ) -> dict:
        """Create a time entry."""
        params = {"custom_task_ids": str(custom_task_ids).lower()}
        data = {"start": start, "duration": duration, "billable": billable}
        if task_id:
            data["tid"] = task_id
        if description:
            data["description"] = description
        if tags:
            data["tags"] = tags
        return await self.post(f"/team/{team_id}/time_entries", json=data, params=params)

    async def get_time_entry(
        self,
        team_id: str,
        timer_id: str,
        include_task: bool = False,
        include_location_names: bool = False,
    ) -> dict:
        """Get a single time entry."""
        params = {
            "include_task": str(include_task).lower(),
            "include_location_names": str(include_location_names).lower(),
        }
        return await self.get(f"/team/{team_id}/time_entries/{timer_id}", params=params)

    async def update_time_entry(
        self,
        team_id: str,
        timer_id: str,
        **kwargs,
    ) -> dict:
        """Update a time entry."""
        return await self.put(f"/team/{team_id}/time_entries/{timer_id}", json=kwargs)

    async def delete_time_entry(self, team_id: str, timer_id: str) -> dict:
        """Delete a time entry."""
        return await self.delete(f"/team/{team_id}/time_entries/{timer_id}")

    async def get_time_entry_history(self, team_id: str, timer_id: str) -> dict:
        """Get history of changes to a time entry."""
        return await self.get(f"/team/{team_id}/time_entries/{timer_id}/history")

    async def get_running_time_entry(self, team_id: str, assignee: Optional[str] = None) -> dict:
        """Get currently running time entry."""
        params = {}
        if assignee:
            params["assignee"] = assignee
        return await self.get(f"/team/{team_id}/time_entries/current", params=params)

    async def start_time_entry(
        self,
        team_id: str,
        task_id: str,
        description: Optional[str] = None,
        billable: bool = False,
        tags: Optional[list[dict]] = None,
        custom_task_ids: bool = False,
    ) -> dict:
        """Start a timer on a task."""
        params = {"custom_task_ids": str(custom_task_ids).lower()}
        data = {"tid": task_id, "billable": billable}
        if description:
            data["description"] = description
        if tags:
            data["tags"] = tags
        return await self.post(f"/team/{team_id}/time_entries/start", json=data, params=params)

    async def stop_time_entry(self, team_id: str) -> dict:
        """Stop the currently running timer."""
        return await self.post(f"/team/{team_id}/time_entries/stop")

    async def get_time_entry_tags(self, team_id: str) -> dict:
        """Get all time entry tags."""
        return await self.get(f"/team/{team_id}/time_entries/tags")

    async def add_tags_to_time_entries(self, team_id: str, time_entry_ids: list[str], tags: list[dict]) -> dict:
        """Add tags to time entries."""
        return await self.post(
            f"/team/{team_id}/time_entries/tags",
            json={"time_entry_ids": time_entry_ids, "tags": tags},
        )

    async def remove_tags_from_time_entries(self, team_id: str, time_entry_ids: list[str], tags: list[dict]) -> dict:
        """Remove tags from time entries."""
        return await self.delete(
            f"/team/{team_id}/time_entries/tags",
            params={"time_entry_ids": time_entry_ids, "tags": tags},
        )

    async def update_time_entry_tags(self, team_id: str, name: str, new_name: str, tag_bg: str, tag_fg: str) -> dict:
        """Change tag names for time entries."""
        return await self.put(
            f"/team/{team_id}/time_entries/tags",
            json={"name": name, "new_name": new_name, "tag_bg": tag_bg, "tag_fg": tag_fg},
        )

    # ===== Members =====

    async def get_task_members(self, task_id: str) -> dict:
        """Get members with access to a task."""
        return await self.get(f"/task/{task_id}/member")

    async def get_list_members(self, list_id: str) -> dict:
        """Get members with access to a list."""
        return await self.get(f"/list/{list_id}/member")

    # ===== Users =====

    async def invite_user_to_workspace(
        self,
        team_id: str,
        email: str,
        admin: bool = False,
        custom_role_id: Optional[str] = None,
    ) -> dict:
        """Invite a user to a workspace."""
        data = {"email": email, "admin": admin}
        if custom_role_id:
            data["custom_role_id"] = custom_role_id
        return await self.post(f"/team/{team_id}/user", json=data)

    async def get_user(self, team_id: str, user_id: str) -> dict:
        """Get a user."""
        return await self.get(f"/team/{team_id}/user/{user_id}")

    async def update_user(self, team_id: str, user_id: str, **kwargs) -> dict:
        """Update a user."""
        return await self.put(f"/team/{team_id}/user/{user_id}", json=kwargs)

    async def remove_user_from_workspace(self, team_id: str, user_id: str) -> dict:
        """Remove a user from a workspace."""
        return await self.delete(f"/team/{team_id}/user/{user_id}")

    # ===== Guests =====

    async def invite_guest_to_workspace(
        self,
        team_id: str,
        email: str,
        can_edit_tags: bool = False,
        can_see_time_spent: bool = False,
        can_see_time_estimated: bool = False,
        can_create_views: bool = False,
    ) -> dict:
        """Invite a guest to a workspace."""
        data = {
            "email": email,
            "can_edit_tags": can_edit_tags,
            "can_see_time_spent": can_see_time_spent,
            "can_see_time_estimated": can_see_time_estimated,
            "can_create_views": can_create_views,
        }
        return await self.post(f"/team/{team_id}/guest", json=data)

    async def get_guest(self, team_id: str, guest_id: str) -> dict:
        """Get a guest."""
        return await self.get(f"/team/{team_id}/guest/{guest_id}")

    async def update_guest(self, team_id: str, guest_id: str, **kwargs) -> dict:
        """Update a guest."""
        return await self.put(f"/team/{team_id}/guest/{guest_id}", json=kwargs)

    async def remove_guest_from_workspace(self, team_id: str, guest_id: str) -> dict:
        """Remove a guest from a workspace."""
        return await self.delete(f"/team/{team_id}/guest/{guest_id}")

    async def add_guest_to_task(self, task_id: str, guest_id: str, permission_level: str) -> dict:
        """Add a guest to a task."""
        return await self.post(f"/task/{task_id}/guest/{guest_id}", json={"permission_level": permission_level})

    async def remove_guest_from_task(self, task_id: str, guest_id: str) -> dict:
        """Remove a guest from a task."""
        return await self.delete(f"/task/{task_id}/guest/{guest_id}")

    async def add_guest_to_list(self, list_id: str, guest_id: str, permission_level: str) -> dict:
        """Add a guest to a list."""
        return await self.post(f"/list/{list_id}/guest/{guest_id}", json={"permission_level": permission_level})

    async def remove_guest_from_list(self, list_id: str, guest_id: str) -> dict:
        """Remove a guest from a list."""
        return await self.delete(f"/list/{list_id}/guest/{guest_id}")

    async def add_guest_to_folder(self, folder_id: str, guest_id: str, permission_level: str) -> dict:
        """Add a guest to a folder."""
        return await self.post(f"/folder/{folder_id}/guest/{guest_id}", json={"permission_level": permission_level})

    async def remove_guest_from_folder(self, folder_id: str, guest_id: str) -> dict:
        """Remove a guest from a folder."""
        return await self.delete(f"/folder/{folder_id}/guest/{guest_id}")

    # ===== User Groups =====

    async def get_user_groups(self, team_id: str) -> dict:
        """Get user groups in a workspace."""
        return await self.get(f"/group", params={"team_id": team_id})

    async def create_user_group(self, team_id: str, name: str, member_ids: Optional[list[str]] = None) -> dict:
        """Create a user group."""
        data = {"name": name, "team_id": team_id}
        if member_ids:
            data["member_ids"] = member_ids
        return await self.post("/group", json=data)

    async def update_user_group(
        self,
        group_id: str,
        name: Optional[str] = None,
        member_ids_to_add: Optional[list[str]] = None,
        member_ids_to_remove: Optional[list[str]] = None,
    ) -> dict:
        """Update a user group."""
        data = {}
        if name:
            data["name"] = name
        if member_ids_to_add:
            data["members"] = {"add": member_ids_to_add}
        if member_ids_to_remove:
            if "members" not in data:
                data["members"] = {}
            data["members"]["rem"] = member_ids_to_remove
        return await self.put(f"/group/{group_id}", json=data)

    async def delete_user_group(self, group_id: str) -> dict:
        """Delete a user group."""
        return await self.delete(f"/group/{group_id}")

    # ===== Roles =====

    async def get_custom_roles(self, team_id: str) -> dict:
        """Get custom roles in a workspace."""
        return await self.get(f"/team/{team_id}/customroles")

    # ===== Views =====

    async def get_workspace_views(self, team_id: str) -> dict:
        """Get workspace-level views."""
        return await self.get(f"/team/{team_id}/view")

    async def create_workspace_view(self, team_id: str, name: str, type: str, **kwargs) -> dict:
        """Create a workspace-level view."""
        data = {"name": name, "type": type, **kwargs}
        return await self.post(f"/team/{team_id}/view", json=data)

    async def get_space_views(self, space_id: str) -> dict:
        """Get space-level views."""
        return await self.get(f"/space/{space_id}/view")

    async def create_space_view(self, space_id: str, name: str, type: str, **kwargs) -> dict:
        """Create a space-level view."""
        data = {"name": name, "type": type, **kwargs}
        return await self.post(f"/space/{space_id}/view", json=data)

    async def get_folder_views(self, folder_id: str) -> dict:
        """Get folder-level views."""
        return await self.get(f"/folder/{folder_id}/view")

    async def create_folder_view(self, folder_id: str, name: str, type: str, **kwargs) -> dict:
        """Create a folder-level view."""
        data = {"name": name, "type": type, **kwargs}
        return await self.post(f"/folder/{folder_id}/view", json=data)

    async def get_list_views(self, list_id: str) -> dict:
        """Get list-level views."""
        return await self.get(f"/list/{list_id}/view")

    async def create_list_view(self, list_id: str, name: str, type: str, **kwargs) -> dict:
        """Create a list-level view."""
        data = {"name": name, "type": type, **kwargs}
        return await self.post(f"/list/{list_id}/view", json=data)

    async def get_view(self, view_id: str) -> dict:
        """Get a view."""
        return await self.get(f"/view/{view_id}")

    async def update_view(self, view_id: str, **kwargs) -> dict:
        """Update a view."""
        return await self.put(f"/view/{view_id}", json=kwargs)

    async def delete_view(self, view_id: str) -> dict:
        """Delete a view."""
        return await self.delete(f"/view/{view_id}")

    async def get_view_tasks(self, view_id: str, page: int = 0) -> dict:
        """Get tasks in a view."""
        return await self.get(f"/view/{view_id}/task", params={"page": page})

    # ===== Webhooks =====

    async def get_webhooks(self, team_id: str) -> dict:
        """Get webhooks in a workspace."""
        return await self.get(f"/team/{team_id}/webhook")

    async def create_webhook(
        self,
        team_id: str,
        endpoint: str,
        events: list[str],
        space_id: Optional[str] = None,
        folder_id: Optional[str] = None,
        list_id: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> dict:
        """Create a webhook."""
        data = {"endpoint": endpoint, "events": events}
        if space_id:
            data["space_id"] = space_id
        if folder_id:
            data["folder_id"] = folder_id
        if list_id:
            data["list_id"] = list_id
        if task_id:
            data["task_id"] = task_id
        return await self.post(f"/team/{team_id}/webhook", json=data)

    async def update_webhook(
        self,
        webhook_id: str,
        endpoint: Optional[str] = None,
        events: Optional[list[str]] = None,
        status: Optional[str] = None,
    ) -> dict:
        """Update a webhook."""
        data = {}
        if endpoint:
            data["endpoint"] = endpoint
        if events:
            data["events"] = events
        if status:
            data["status"] = status
        return await self.put(f"/webhook/{webhook_id}", json=data)

    async def delete_webhook(self, webhook_id: str) -> dict:
        """Delete a webhook."""
        return await self.delete(f"/webhook/{webhook_id}")

    # ===== Templates =====

    async def get_task_templates(self, team_id: str, page: int = 0) -> dict:
        """Get task templates in a workspace."""
        return await self.get(f"/team/{team_id}/taskTemplate", params={"page": page})

    async def get_folder_templates(self, team_id: str) -> dict:
        """Get folder templates in a workspace (IDs come back with a 't-' prefix — keep it)."""
        return await self.get(f"/team/{team_id}/folder_template")

    async def get_list_templates(self, team_id: str) -> dict:
        """Get list templates in a workspace (IDs come back with a 't-' prefix — keep it)."""
        return await self.get(f"/team/{team_id}/list_template")

    async def create_folder_from_template(
        self,
        space_id: str,
        template_id: str,
        name: str,
        options: Optional[dict] = None,
    ) -> dict:
        """Create a folder in a space from a folder template (template_id keeps its 't-' prefix)."""
        data: dict[str, Any] = {"name": name}
        if options:
            data["options"] = options
        return await self.post(f"/space/{space_id}/folder_template/{template_id}", json=data)

    async def create_list_from_template_in_folder(
        self,
        folder_id: str,
        template_id: str,
        name: str,
        options: Optional[dict] = None,
    ) -> dict:
        """Create a list in a folder from a list template (template_id keeps its 't-' prefix)."""
        data: dict[str, Any] = {"name": name}
        if options:
            data["options"] = options
        return await self.post(f"/folder/{folder_id}/list_template/{template_id}", json=data)

    async def create_list_from_template_in_space(
        self,
        space_id: str,
        template_id: str,
        name: str,
        options: Optional[dict] = None,
    ) -> dict:
        """Create a folderless list in a space from a list template (template_id keeps its 't-' prefix)."""
        data: dict[str, Any] = {"name": name}
        if options:
            data["options"] = options
        return await self.post(f"/space/{space_id}/list_template/{template_id}", json=data)

    # ===== Shared Hierarchy =====

    async def get_shared_hierarchy(self, team_id: str) -> dict:
        """Get shared hierarchy."""
        return await self.get(f"/team/{team_id}/shared")

    # ===== Docs (API v3) =====

    V3_URL = "https://api.clickup.com/api/v3"

    async def search_docs(self, team_id: str, query: Optional[str] = None, cursor: Optional[str] = None) -> dict:
        """Search docs in a workspace."""
        return await self.get(f"{self.V3_URL}/workspaces/{team_id}/docs", params={"search": query, "next_cursor": cursor})

    async def create_doc(
        self,
        team_id: str,
        name: str,
        parent: Optional[dict] = None,
        visibility: Optional[str] = None,
        create_page: Optional[bool] = None,
    ) -> dict:
        """Create a doc. create_page defaults to true API-side (blank starter page); pass False to suppress it."""
        data: dict[str, Any] = {"name": name}
        if parent:
            data["parent"] = parent
        if visibility:
            data["visibility"] = visibility
        if create_page is not None:
            data["create_page"] = create_page
        return await self.post(f"{self.V3_URL}/workspaces/{team_id}/docs", json=data)

    async def get_doc(self, team_id: str, doc_id: str) -> dict:
        """Get a doc's metadata (creation dates, parent, archived state, page defaults)."""
        return await self.get(f"{self.V3_URL}/workspaces/{team_id}/docs/{doc_id}")

    async def get_doc_page_listing(self, team_id: str, doc_id: str) -> dict:
        """Get the page tree (ids + names, no content) of a doc."""
        return await self.get(f"{self.V3_URL}/workspaces/{team_id}/docs/{doc_id}/pageListing")

    async def get_doc_pages(self, team_id: str, doc_id: str, content_format: str = "text/md") -> dict:
        """Get all pages of a doc including content."""
        return await self.get(f"{self.V3_URL}/workspaces/{team_id}/docs/{doc_id}/pages", params={"content_format": content_format})

    async def get_doc_page(self, team_id: str, doc_id: str, page_id: str, content_format: str = "text/md") -> dict:
        """Get one page of a doc."""
        return await self.get(f"{self.V3_URL}/workspaces/{team_id}/docs/{doc_id}/pages/{page_id}", params={"content_format": content_format})

    async def create_doc_page(
        self,
        team_id: str,
        doc_id: str,
        name: str,
        content: str,
        parent_page_id: Optional[str] = None,
        sub_title: Optional[str] = None,
        content_format: str = "text/md",
    ) -> dict:
        """Create a page (or subpage) in a doc."""
        data: dict[str, Any] = {"name": name, "content": content, "content_format": content_format}
        if parent_page_id:
            data["parent_page_id"] = parent_page_id
        if sub_title:
            data["sub_title"] = sub_title
        return await self.post(f"{self.V3_URL}/workspaces/{team_id}/docs/{doc_id}/pages", json=data)

    async def update_doc_page(
        self,
        team_id: str,
        doc_id: str,
        page_id: str,
        content: Optional[str] = None,
        name: Optional[str] = None,
        sub_title: Optional[str] = None,
        content_edit_mode: str = "append",
        content_format: str = "text/md",
    ) -> dict:
        """Update a doc page. Default edit mode is APPEND (replace flattens task chips)."""
        data: dict[str, Any] = {"content_edit_mode": content_edit_mode, "content_format": content_format}
        if content is not None:
            data["content"] = content
        if name is not None:
            data["name"] = name
        if sub_title is not None:
            data["sub_title"] = sub_title
        return await self.put(f"{self.V3_URL}/workspaces/{team_id}/docs/{doc_id}/pages/{page_id}", json=data)

    # ===== Chat (API v3) =====

    async def get_chat_channels(
        self,
        team_id: str,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        is_follower: Optional[bool] = None,
        include_closed: Optional[bool] = None,
        with_message_since: Optional[int] = None,
    ) -> dict:
        """Get chat channels (incl. DMs) in a workspace."""
        params: dict[str, Any] = {"cursor": cursor}
        if limit:
            params["limit"] = limit
        if is_follower is not None:
            params["is_follower"] = str(is_follower).lower()
        if include_closed is not None:
            params["include_closed"] = str(include_closed).lower()
        if with_message_since:
            params["with_message_since"] = with_message_since
        return await self.get(f"{self.V3_URL}/workspaces/{team_id}/chat/channels", params=params)

    async def get_chat_channel(self, team_id: str, channel_id: str) -> dict:
        """Get a single chat channel."""
        return await self.get(f"{self.V3_URL}/workspaces/{team_id}/chat/channels/{channel_id}")

    async def create_chat_channel(self, team_id: str, name: str, **kwargs) -> dict:
        """Create a chat channel (returns the EXISTING channel if the name is taken)."""
        return await self.post(f"{self.V3_URL}/workspaces/{team_id}/chat/channels", json={"name": name, **kwargs})

    async def update_chat_channel(self, team_id: str, channel_id: str, **kwargs) -> dict:
        """Update a chat channel (PATCH: send only fields to change)."""
        return await self._request(
            "PATCH", f"{self.V3_URL}/workspaces/{team_id}/chat/channels/{channel_id}", json=kwargs
        )

    async def delete_chat_channel(self, team_id: str, channel_id: str) -> dict:
        """Delete a chat channel."""
        return await self.delete(f"{self.V3_URL}/workspaces/{team_id}/chat/channels/{channel_id}")

    async def create_chat_dm_channel(self, team_id: str, user_ids: list[str]) -> dict:
        """Create (or return the existing) DM channel with the given users (max 15)."""
        return await self.post(
            f"{self.V3_URL}/workspaces/{team_id}/chat/channels/direct_message",
            json={"user_ids": user_ids},
        )

    async def create_chat_location_channel(self, team_id: str, location: dict, **kwargs) -> dict:
        """Create (or return the existing) channel on a space/folder/list. location={id, type}."""
        return await self.post(
            f"{self.V3_URL}/workspaces/{team_id}/chat/channels/location",
            json={"location": location, **kwargs},
        )

    async def get_chat_channel_members(
        self, team_id: str, channel_id: str, cursor: Optional[str] = None, limit: Optional[int] = None
    ) -> dict:
        """Get members of a chat channel."""
        params: dict[str, Any] = {"cursor": cursor}
        if limit:
            params["limit"] = limit
        return await self.get(
            f"{self.V3_URL}/workspaces/{team_id}/chat/channels/{channel_id}/members", params=params
        )

    async def get_chat_channel_followers(
        self, team_id: str, channel_id: str, cursor: Optional[str] = None, limit: Optional[int] = None
    ) -> dict:
        """Get followers of a chat channel."""
        params: dict[str, Any] = {"cursor": cursor}
        if limit:
            params["limit"] = limit
        return await self.get(
            f"{self.V3_URL}/workspaces/{team_id}/chat/channels/{channel_id}/followers", params=params
        )

    async def get_chat_messages(
        self,
        team_id: str,
        channel_id: str,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        content_format: Optional[str] = None,
    ) -> dict:
        """Get messages in a chat channel (most recent first)."""
        params: dict[str, Any] = {"cursor": cursor}
        if limit:
            params["limit"] = limit
        if content_format:
            params["content_format"] = content_format
        return await self.get(
            f"{self.V3_URL}/workspaces/{team_id}/chat/channels/{channel_id}/messages", params=params
        )

    async def send_chat_message(self, team_id: str, channel_id: str, content: str, msg_type: str = "message", **kwargs) -> dict:
        """Send a message to a chat channel. Extra kwargs pass through to the documented body
        (content_format, assignee, group_assignee, triaged_*, reactions, followers, post_data)."""
        return await self.post(
            f"{self.V3_URL}/workspaces/{team_id}/chat/channels/{channel_id}/messages",
            json={"type": msg_type, "content": content, **kwargs},
        )

    async def send_chat_reply(self, team_id: str, message_id: str, content: str, msg_type: str = "message", **kwargs) -> dict:
        """Reply to a chat message."""
        return await self.post(
            f"{self.V3_URL}/workspaces/{team_id}/chat/messages/{message_id}/replies",
            json={"type": msg_type, "content": content, **kwargs},
        )

    async def update_chat_message(self, team_id: str, message_id: str, **kwargs) -> dict:
        """Edit a chat message (PATCH: content, content_format, assignee, resolved, post_data)."""
        return await self._request(
            "PATCH", f"{self.V3_URL}/workspaces/{team_id}/chat/messages/{message_id}", json=kwargs
        )

    async def delete_chat_message(self, team_id: str, message_id: str) -> dict:
        """Delete a chat message."""
        return await self.delete(f"{self.V3_URL}/workspaces/{team_id}/chat/messages/{message_id}")

    async def get_chat_message_replies(
        self,
        team_id: str,
        message_id: str,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        content_format: Optional[str] = None,
    ) -> dict:
        """Get replies to a chat message."""
        params: dict[str, Any] = {"cursor": cursor}
        if limit:
            params["limit"] = limit
        if content_format:
            params["content_format"] = content_format
        return await self.get(
            f"{self.V3_URL}/workspaces/{team_id}/chat/messages/{message_id}/replies", params=params
        )

    async def get_chat_message_tagged_users(
        self, team_id: str, message_id: str, cursor: Optional[str] = None, limit: Optional[int] = None
    ) -> dict:
        """Get users tagged (mentioned) in a chat message."""
        params: dict[str, Any] = {"cursor": cursor}
        if limit:
            params["limit"] = limit
        return await self.get(
            f"{self.V3_URL}/workspaces/{team_id}/chat/messages/{message_id}/tagged_users", params=params
        )

    async def create_chat_reaction(self, team_id: str, message_id: str, reaction: str) -> dict:
        """React to a chat message (reaction = lower-case emoji name; 400 if duplicate)."""
        return await self.post(
            f"{self.V3_URL}/workspaces/{team_id}/chat/messages/{message_id}/reactions",
            json={"reaction": reaction},
        )

    async def delete_chat_reaction(self, team_id: str, message_id: str, reaction: str) -> dict:
        """Remove a reaction (by emoji name) from a chat message."""
        return await self.delete(
            f"{self.V3_URL}/workspaces/{team_id}/chat/messages/{message_id}/reactions/{reaction}"
        )

    async def get_chat_message_reactions(
        self, team_id: str, message_id: str, cursor: Optional[str] = None, limit: Optional[int] = None
    ) -> dict:
        """Get reactions on a chat message."""
        params: dict[str, Any] = {"cursor": cursor}
        if limit:
            params["limit"] = limit
        return await self.get(
            f"{self.V3_URL}/workspaces/{team_id}/chat/messages/{message_id}/reactions", params=params
        )

    async def get_chat_post_subtypes(self, team_id: str, comment_type: str = "post") -> dict:
        """Get post subtype IDs (Announcement/Discussion/Idea/Update) for chat 'post' messages."""
        return await self.get(f"{self.V3_URL}/workspaces/{team_id}/comments/types/{comment_type}/subtypes")
