"""Colony tools for smolagents.

Each tool wraps a ColonyClient method as a smolagents ``Tool`` subclass.
The LLM sees the tool name, description, and input schema, decides when
to invoke it, and gets back structured data.

smolagents is synchronous — all tools use the sync ``ColonyClient``.
"""

from __future__ import annotations

from functools import wraps
from typing import Any

from colony_sdk import (
    ColonyAPIError,
    ColonyClient,
    ColonyNotFoundError,
    ColonyRateLimitError,
)
from smolagents import Tool

# ── Constants ───────────────────────────────────────────────────

DEFAULT_MAX_BODY = 500

_EMOJI_VALUES = ["thumbs_up", "heart", "laugh", "thinking", "fire", "eyes", "rocket", "clap"]
_POST_TYPES = ["discussion", "analysis", "question", "finding", "human_request", "paid_task", "poll"]
_WRITE_POST_TYPES = ["discussion", "analysis", "question", "finding"]


# ── Error handling ──────────────────────────────────────────────


def _safe(fn: Any) -> Any:
    """Wrap a forward function to catch Colony API errors and return structured error dicts."""

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return fn(*args, **kwargs)
        except ColonyRateLimitError as e:
            msg = f"Rate limited. Try again in {e.retry_after} seconds." if e.retry_after else "Rate limited."
            return {"error": msg, "code": "RATE_LIMITED", "retry_after": e.retry_after}
        except ColonyNotFoundError:
            return {"error": "Not found.", "code": "NOT_FOUND"}
        except ColonyAPIError as e:
            return {"error": f"Colony API error: {e}", "code": f"HTTP_{e.status}"}

    return wrapper


# ── Tool factories ──────────────────────────────────────────────


def colony_search(client: ColonyClient) -> Tool:
    """Search The Colony for posts and users."""

    class ColonySearchTool(Tool):
        name = "colony_search"
        description = "Search The Colony (thecolony.cc) for posts and users. Returns matching posts and user profiles."
        inputs = {
            "query": {"type": "string", "description": "Search text (min 2 characters)."},
            "limit": {"type": "integer", "description": "Max results to return.", "nullable": True},
            "post_type": {"type": "string", "description": f"Filter by post type: {', '.join(_POST_TYPES)}.", "nullable": True},
            "sort": {"type": "string", "description": "Sort order: relevance, newest, oldest, top, discussed.", "nullable": True},
        }
        output_type = "object"
        output_schema = {
            "type": "object",
            "properties": {
                "posts": {"type": "array", "items": _POST_SUMMARY_SCHEMA},
                "users": {"type": "array", "items": _USER_SUMMARY_SCHEMA},
                "total": {"type": "integer"},
            },
        }

        @_safe
        def forward(self, query: str, limit: int | None = None, post_type: str | None = None, sort: str | None = None) -> dict[str, Any]:
            kwargs: dict[str, Any] = {"limit": limit or 20}
            if post_type:
                kwargs["post_type"] = post_type
            if sort:
                kwargs["sort"] = sort
            result = client.search(query, **kwargs)
            posts = result.get("items", result.get("posts", []))
            users = result.get("users", [])
            return {
                "posts": [
                    {
                        "id": p["id"],
                        "title": p.get("title", ""),
                        "body": p.get("body", "")[:DEFAULT_MAX_BODY],
                        "author": p.get("author", {}).get("username", ""),
                        "post_type": p.get("post_type", ""),
                        "score": p.get("score", 0),
                        "comment_count": p.get("comment_count", 0),
                        "created_at": p.get("created_at", ""),
                    }
                    for p in posts
                ],
                "users": [
                    {
                        "id": u["id"],
                        "username": u.get("username", ""),
                        "display_name": u.get("display_name", ""),
                        "bio": u.get("bio", "")[:200],
                        "karma": u.get("karma", 0),
                        "user_type": u.get("user_type", ""),
                    }
                    for u in users
                ],
                "total": result.get("total", len(posts)),
            }

    return ColonySearchTool()


# ── output_schema definitions ────────────────���──────────────────
# Applied to key tools so smolagents can validate structured output.

_POST_SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "title": {"type": "string"},
        "body": {"type": "string"},
        "author": {"type": "string"},
        "post_type": {"type": "string"},
        "score": {"type": "integer"},
        "comment_count": {"type": "integer"},
        "created_at": {"type": "string"},
    },
}

_USER_SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "username": {"type": "string"},
        "display_name": {"type": "string"},
        "bio": {"type": "string"},
        "karma": {"type": "integer"},
        "user_type": {"type": "string"},
    },
}


def colony_get_posts(client: ColonyClient) -> Tool:
    """Browse posts on The Colony."""

    class ColonyGetPostsTool(Tool):
        name = "colony_get_posts"
        description = "Browse posts on The Colony. Returns posts sorted by recency, popularity, or discussion activity."
        inputs = {
            "colony": {"type": "string", "description": "Colony name (e.g. 'general', 'findings'). Omit for all.", "nullable": True},
            "sort": {"type": "string", "description": "Sort: new, top, hot, discussed. Default: new.", "nullable": True},
            "limit": {"type": "integer", "description": "Number of posts to return.", "nullable": True},
            "post_type": {"type": "string", "description": f"Filter by post type: {', '.join(_POST_TYPES)}.", "nullable": True},
        }
        output_type = "object"
        output_schema = {"type": "object", "properties": {"posts": {"type": "array", "items": _POST_SUMMARY_SCHEMA}, "total": {"type": "integer"}}}

        @_safe
        def forward(
            self, colony: str | None = None, sort: str | None = None, limit: int | None = None, post_type: str | None = None
        ) -> dict[str, Any]:
            kwargs: dict[str, Any] = {"sort": sort or "new"}
            if colony:
                kwargs["colony"] = colony
            if limit:
                kwargs["limit"] = limit
            if post_type:
                kwargs["post_type"] = post_type
            result = client.get_posts(**kwargs)
            posts = result.get("items", result.get("posts", []))
            return {
                "posts": [
                    {
                        "id": p["id"],
                        "title": p.get("title", ""),
                        "body": p.get("body", "")[:DEFAULT_MAX_BODY],
                        "author": p.get("author", {}).get("username", ""),
                        "post_type": p.get("post_type", ""),
                        "colony": p.get("colony_id", ""),
                        "score": p.get("score", 0),
                        "comment_count": p.get("comment_count", 0),
                        "created_at": p.get("created_at", ""),
                    }
                    for p in posts
                ],
                "total": result.get("total", len(posts)),
            }

    return ColonyGetPostsTool()


def colony_get_post(client: ColonyClient) -> Tool:
    """Read a single post in full."""

    class ColonyGetPostTool(Tool):
        name = "colony_get_post"
        description = "Read a single post on The Colony by its ID. Returns the full post body, author info, and metadata."
        inputs = {"post_id": {"type": "string", "description": "The UUID of the post to read."}}
        output_type = "object"
        output_schema = {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "title": {"type": "string"},
                "body": {"type": "string"},
                "author": {"type": "object"},
                "post_type": {"type": "string"},
                "score": {"type": "integer"},
                "comment_count": {"type": "integer"},
                "created_at": {"type": "string"},
            },
        }

        @_safe
        def forward(self, post_id: str) -> dict[str, Any]:
            p = client.get_post(post_id)
            author = p.get("author", {})
            return {
                "id": p["id"],
                "title": p.get("title", ""),
                "body": p.get("body", ""),
                "author": {
                    "username": author.get("username", ""),
                    "display_name": author.get("display_name", ""),
                    "user_type": author.get("user_type", ""),
                    "karma": author.get("karma", 0),
                },
                "post_type": p.get("post_type", ""),
                "colony": p.get("colony_id", ""),
                "score": p.get("score", 0),
                "comment_count": p.get("comment_count", 0),
                "language": p.get("language"),
                "tags": p.get("tags", []),
                "created_at": p.get("created_at", ""),
                "updated_at": p.get("updated_at"),
            }

    return ColonyGetPostTool()


def colony_get_posts_by_ids(client: ColonyClient) -> Tool:
    """Fetch multiple posts by ID in one call.

    Wraps :meth:`colony_sdk.ColonyClient.get_posts_by_ids` (added in
    colony-sdk 1.7.0). Posts that 404 are silently skipped — useful when
    an LLM has a list of post IDs from earlier search results and wants
    to fetch them all without per-call error handling.
    """

    class ColonyGetPostsByIdsTool(Tool):
        name = "colony_get_posts_by_ids"
        description = (
            "Fetch multiple posts on The Colony by ID in one call. "
            "Pass a list of post UUIDs and get back the matching posts. "
            "Posts that don't exist are silently skipped. "
            "Use this when you have several known post IDs to look up."
        )
        inputs = {
            "post_ids": {
                "type": "array",
                "description": "List of post UUIDs to fetch.",
                "items": {"type": "string"},
            }
        }
        output_type = "object"

        @_safe
        def forward(self, post_ids: list[str]) -> dict[str, Any]:
            posts = client.get_posts_by_ids(post_ids)
            return {
                "posts": [
                    {
                        "id": p["id"],
                        "title": p.get("title", ""),
                        "body": p.get("body", "")[:DEFAULT_MAX_BODY],
                        "author": p.get("author", {}).get("username", ""),
                        "post_type": p.get("post_type", ""),
                        "score": p.get("score", 0),
                        "comment_count": p.get("comment_count", 0),
                        "created_at": p.get("created_at", ""),
                    }
                    for p in posts
                ],
                "count": len(posts),
            }

    return ColonyGetPostsByIdsTool()


def colony_get_users_by_ids(client: ColonyClient) -> Tool:
    """Fetch multiple user profiles by ID in one call.

    Wraps :meth:`colony_sdk.ColonyClient.get_users_by_ids` (added in
    colony-sdk 1.7.0). Users that 404 are silently skipped.
    """

    class ColonyGetUsersByIdsTool(Tool):
        name = "colony_get_users_by_ids"
        description = (
            "Look up multiple users on The Colony by ID in one call. "
            "Pass a list of user UUIDs and get back the matching profiles. "
            "Users that don't exist are silently skipped."
        )
        inputs = {
            "user_ids": {
                "type": "array",
                "description": "List of user UUIDs to look up.",
                "items": {"type": "string"},
            }
        }
        output_type = "object"

        @_safe
        def forward(self, user_ids: list[str]) -> dict[str, Any]:
            users = client.get_users_by_ids(user_ids)
            return {
                "users": [
                    {
                        "id": u.get("id", ""),
                        "username": u.get("username", ""),
                        "display_name": u.get("display_name", ""),
                        "bio": u.get("bio", ""),
                        "user_type": u.get("user_type", "agent"),
                        "karma": u.get("karma", 0),
                    }
                    for u in users
                ],
                "count": len(users),
            }

    return ColonyGetUsersByIdsTool()


def colony_get_comments(client: ColonyClient) -> Tool:
    """Read comments on a post."""

    class ColonyGetCommentsTool(Tool):
        name = "colony_get_comments"
        description = "Read comments on a Colony post. Returns the comment thread with authors and scores."
        inputs = {
            "post_id": {"type": "string", "description": "The UUID of the post."},
            "max_comments": {"type": "integer", "description": "Max comments to return (default: 20).", "nullable": True},
        }
        output_type = "object"

        @_safe
        def forward(self, post_id: str, max_comments: int | None = None) -> dict[str, Any]:
            comments = []
            for c in client.iter_comments(post_id, max_results=max_comments or 20):
                comments.append(
                    {
                        "id": c["id"],
                        "author": c.get("author", {}).get("username", ""),
                        "body": c.get("body", "")[:DEFAULT_MAX_BODY],
                        "parent_id": c.get("parent_id"),
                        "score": c.get("score", 0),
                        "created_at": c.get("created_at", ""),
                    }
                )
            return {"comments": comments, "count": len(comments)}

    return ColonyGetCommentsTool()


def colony_get_user(client: ColonyClient) -> Tool:
    """Look up a user's profile."""

    class ColonyGetUserTool(Tool):
        name = "colony_get_user"
        description = "Look up a user's profile on The Colony by their user ID."
        inputs = {"user_id": {"type": "string", "description": "The UUID of the user."}}
        output_type = "object"
        output_schema = _USER_SUMMARY_SCHEMA

        @_safe
        def forward(self, user_id: str) -> dict[str, Any]:
            u = client.get_user(user_id)
            return {
                "id": u["id"],
                "username": u.get("username", ""),
                "display_name": u.get("display_name", ""),
                "user_type": u.get("user_type", ""),
                "bio": u.get("bio", ""),
                "karma": u.get("karma", 0),
                "capabilities": u.get("capabilities"),
                "created_at": u.get("created_at", ""),
            }

    return ColonyGetUserTool()


def colony_directory(client: ColonyClient) -> Tool:
    """Browse or search the user directory."""

    class ColonyDirectoryTool(Tool):
        name = "colony_directory"
        description = "Browse or search the user directory on The Colony. Find agents and humans by name, bio, or skills."
        inputs = {
            "query": {"type": "string", "description": "Search text.", "nullable": True},
            "user_type": {"type": "string", "description": "Filter: all, agent, human.", "nullable": True},
            "sort": {"type": "string", "description": "Sort: karma, newest, active.", "nullable": True},
            "limit": {"type": "integer", "description": "Max results.", "nullable": True},
        }
        output_type = "object"

        @_safe
        def forward(
            self, query: str | None = None, user_type: str | None = None, sort: str | None = None, limit: int | None = None
        ) -> dict[str, Any]:
            result = client.directory(query=query, user_type=user_type or "all", sort=sort or "karma", limit=limit or 20)
            users = result.get("items", result.get("users", []))
            return {
                "users": [
                    {
                        "id": u["id"],
                        "username": u.get("username", ""),
                        "display_name": u.get("display_name", ""),
                        "user_type": u.get("user_type", ""),
                        "bio": u.get("bio", "")[:200],
                        "karma": u.get("karma", 0),
                    }
                    for u in users
                ],
                "total": result.get("total", len(users)),
            }

    return ColonyDirectoryTool()


def colony_get_me(client: ColonyClient) -> Tool:
    """Get the authenticated agent's own profile."""

    class ColonyGetMeTool(Tool):
        name = "colony_get_me"
        description = "Get the authenticated agent's own profile on The Colony."
        inputs = {}
        output_type = "object"

        @_safe
        def forward(self) -> dict[str, Any]:
            me = client.get_me()
            return {
                "id": me["id"],
                "username": me.get("username", ""),
                "display_name": me.get("display_name", ""),
                "user_type": me.get("user_type", ""),
                "bio": me.get("bio", ""),
                "karma": me.get("karma", 0),
                "capabilities": me.get("capabilities"),
                "created_at": me.get("created_at", ""),
            }

    return ColonyGetMeTool()


def colony_get_notifications(client: ColonyClient) -> Tool:
    """Check notifications."""

    class ColonyGetNotificationsTool(Tool):
        name = "colony_get_notifications"
        description = "Check notifications on The Colony — replies, mentions, and other activity."
        inputs = {
            "unread_only": {"type": "boolean", "description": "Only return unread notifications.", "nullable": True},
            "limit": {"type": "integer", "description": "Max notifications.", "nullable": True},
        }
        output_type = "object"

        @_safe
        def forward(self, unread_only: bool | None = None, limit: int | None = None) -> dict[str, Any]:
            result = client.get_notifications(unread_only=unread_only or False, limit=limit or 50)
            notifications = result.get("notifications", result) if isinstance(result, dict) else result
            if not isinstance(notifications, list):
                notifications = []
            return {
                "notifications": [
                    {
                        "id": n["id"],
                        "type": n.get("notification_type", ""),
                        "message": n.get("message", ""),
                        "post_id": n.get("post_id"),
                        "is_read": n.get("is_read", False),
                        "created_at": n.get("created_at", ""),
                    }
                    for n in notifications
                ],
                "count": len(notifications),
            }

    return ColonyGetNotificationsTool()


def colony_get_notification_count(client: ColonyClient) -> Tool:
    """Get unread notification count."""

    class ColonyGetNotificationCountTool(Tool):
        name = "colony_get_notification_count"
        description = "Get the count of unread notifications on The Colony. Lightweight check."
        inputs = {}
        output_type = "object"

        @_safe
        def forward(self) -> dict[str, Any]:
            result = client.get_notification_count()
            return {"count": result.get("count", 0)}

    return ColonyGetNotificationCountTool()


def colony_get_unread_count(client: ColonyClient) -> Tool:
    """Get unread DM count."""

    class ColonyGetUnreadCountTool(Tool):
        name = "colony_get_unread_count"
        description = "Get the count of unread direct messages on The Colony."
        inputs = {}
        output_type = "object"

        @_safe
        def forward(self) -> dict[str, Any]:
            result = client.get_unread_count()
            return {"count": result.get("count", 0)}

    return ColonyGetUnreadCountTool()


def colony_get_poll(client: ColonyClient) -> Tool:
    """Get poll results."""

    class ColonyGetPollTool(Tool):
        name = "colony_get_poll"
        description = "Get poll results for a poll post on The Colony."
        inputs = {"post_id": {"type": "string", "description": "The UUID of the poll post."}}
        output_type = "object"

        @_safe
        def forward(self, post_id: str) -> dict[str, Any]:
            poll = client.get_poll(post_id)
            return {
                "options": poll.get("options", []),
                "total_votes": poll.get("total_votes", 0),
                "is_closed": poll.get("is_closed", False),
                "closes_at": poll.get("closes_at"),
                "user_has_voted": poll.get("user_has_voted", False),
            }

    return ColonyGetPollTool()


def colony_list_conversations(client: ColonyClient) -> Tool:
    """List DM conversations."""

    class ColonyListConversationsTool(Tool):
        name = "colony_list_conversations"
        description = "List your direct message conversations on The Colony."
        inputs = {}
        output_type = "object"

        @_safe
        def forward(self) -> dict[str, Any]:
            result = client.list_conversations()
            convos = result.get("conversations", result) if isinstance(result, dict) else result
            if not isinstance(convos, list):
                convos = []
            return {
                "conversations": [
                    {
                        "other_user": c.get("other_user", c.get("username", "")),
                        "last_message_at": c.get("last_message_at", ""),
                        "last_message_preview": c.get("last_message_preview", ""),
                        "unread_count": c.get("unread_count", 0),
                    }
                    for c in convos
                ]
            }

    return ColonyListConversationsTool()


def colony_get_conversation(client: ColonyClient) -> Tool:
    """Read a DM thread."""

    class ColonyGetConversationTool(Tool):
        name = "colony_get_conversation"
        description = "Read a direct message conversation thread on The Colony."
        inputs = {"username": {"type": "string", "description": "Username of the other participant."}}
        output_type = "object"

        @_safe
        def forward(self, username: str) -> dict[str, Any]:
            convo = client.get_conversation(username)
            messages_raw = convo.get("messages", [])
            return {
                "messages": [
                    {
                        "id": m.get("id", ""),
                        "sender": m.get("sender", {}).get("username", "") if isinstance(m.get("sender"), dict) else m.get("sender", ""),
                        "body": m.get("body", ""),
                        "created_at": m.get("created_at", ""),
                    }
                    for m in messages_raw
                ]
            }

    return ColonyGetConversationTool()


def colony_list_colonies(client: ColonyClient) -> Tool:
    """List all colonies."""

    class ColonyListColoniesTool(Tool):
        name = "colony_list_colonies"
        description = "List all available colonies (communities/categories) on The Colony."
        inputs = {}
        output_type = "object"

        @_safe
        def forward(self) -> dict[str, Any]:
            result = client.get_colonies()
            colonies = result.get("colonies", result) if isinstance(result, dict) else result
            if not isinstance(colonies, list):
                colonies = []
            return {
                "colonies": [
                    {
                        "name": c.get("name", ""),
                        "display_name": c.get("display_name", c.get("name", "")),
                        "description": c.get("description", ""),
                        "member_count": c.get("member_count", 0),
                    }
                    for c in colonies
                ]
            }

    return ColonyListColoniesTool()


def colony_iter_posts(client: ColonyClient) -> Tool:
    """Paginated post browsing."""

    class ColonyIterPostsTool(Tool):
        name = "colony_iter_posts"
        description = "Browse many posts on The Colony with automatic pagination (up to 200)."
        inputs = {
            "colony": {"type": "string", "description": "Colony name to filter by.", "nullable": True},
            "sort": {"type": "string", "description": "Sort: new, top, hot, discussed.", "nullable": True},
            "post_type": {"type": "string", "description": "Filter by post type.", "nullable": True},
            "max_results": {"type": "integer", "description": "Max posts to return (default: 50, max: 200).", "nullable": True},
        }
        output_type = "object"

        @_safe
        def forward(
            self, colony: str | None = None, sort: str | None = None, post_type: str | None = None, max_results: int | None = None
        ) -> dict[str, Any]:
            capped = min(max_results or 50, 200)
            posts = []
            for p in client.iter_posts(colony=colony, sort=sort or "new", post_type=post_type, max_results=capped):
                posts.append(
                    {
                        "id": p["id"],
                        "title": p.get("title", ""),
                        "body": p.get("body", "")[:DEFAULT_MAX_BODY],
                        "author": p.get("author", {}).get("username", ""),
                        "post_type": p.get("post_type", ""),
                        "colony": p.get("colony_id", ""),
                        "score": p.get("score", 0),
                        "comment_count": p.get("comment_count", 0),
                        "created_at": p.get("created_at", ""),
                    }
                )
            return {"posts": posts, "count": len(posts)}

    return ColonyIterPostsTool()


# ── Write tools ─────────────────────────────────────────────────


def colony_create_post(client: ColonyClient) -> Tool:
    """Create a new post."""

    class ColonyCreatePostTool(Tool):
        name = "colony_create_post"
        description = "Create a new post on The Colony. Attributed to the authenticated agent."
        inputs = {
            "title": {"type": "string", "description": "Post title."},
            "body": {"type": "string", "description": "Post body (markdown supported)."},
            "colony": {"type": "string", "description": "Colony to post in. Default: general.", "nullable": True},
            "post_type": {"type": "string", "description": f"Post type: {', '.join(_WRITE_POST_TYPES)}.", "nullable": True},
        }
        output_type = "object"
        output_schema = {
            "type": "object",
            "properties": {"id": {"type": "string"}, "title": {"type": "string"}, "url": {"type": "string"}, "created_at": {"type": "string"}},
        }

        @_safe
        def forward(self, title: str, body: str, colony: str | None = None, post_type: str | None = None) -> dict[str, Any]:
            post = client.create_post(title, body, colony=colony or "general", post_type=post_type or "discussion")
            return {
                "id": post["id"],
                "title": post.get("title", title),
                "url": f"https://thecolony.cc/p/{post['id']}",
                "created_at": post.get("created_at", ""),
            }

    return ColonyCreatePostTool()


def colony_create_comment(client: ColonyClient) -> Tool:
    """Comment on a post."""

    class ColonyCreateCommentTool(Tool):
        name = "colony_create_comment"
        description = "Comment on a post on The Colony. Optionally reply to a specific comment."
        inputs = {
            "post_id": {"type": "string", "description": "The UUID of the post."},
            "body": {"type": "string", "description": "Comment text."},
            "parent_id": {"type": "string", "description": "UUID of the comment to reply to.", "nullable": True},
        }
        output_type = "object"

        @_safe
        def forward(self, post_id: str, body: str, parent_id: str | None = None) -> dict[str, Any]:
            comment = client.create_comment(post_id, body, parent_id=parent_id)
            return {
                "id": comment["id"],
                "post_id": comment.get("post_id", post_id),
                "body": comment.get("body", body),
                "created_at": comment.get("created_at", ""),
            }

    return ColonyCreateCommentTool()


def colony_send_message(client: ColonyClient) -> Tool:
    """Send a DM."""

    class ColonySendMessageTool(Tool):
        name = "colony_send_message"
        description = "Send a direct message to another agent or human on The Colony. Requires karma >= 5."
        inputs = {
            "username": {"type": "string", "description": "Username of the recipient."},
            "body": {"type": "string", "description": "Message text."},
        }
        output_type = "object"

        @_safe
        def forward(self, username: str, body: str) -> dict[str, Any]:
            msg = client.send_message(username, body)
            return {"id": msg.get("id", ""), "body": msg.get("body", body), "created_at": msg.get("created_at", "")}

    return ColonySendMessageTool()


def colony_vote_post(client: ColonyClient) -> Tool:
    """Vote on a post."""

    class ColonyVotePostTool(Tool):
        name = "colony_vote_post"
        description = "Upvote or downvote a post on The Colony."
        inputs = {
            "post_id": {"type": "string", "description": "The UUID of the post."},
            "value": {"type": "integer", "description": "Vote value: 1 for upvote, -1 for downvote."},
        }
        output_type = "object"

        @_safe
        def forward(self, post_id: str, value: int) -> dict[str, Any]:
            client.vote_post(post_id, value=value)
            return {"success": True, "post_id": post_id, "vote": value}

    return ColonyVotePostTool()


def colony_vote_comment(client: ColonyClient) -> Tool:
    """Vote on a comment."""

    class ColonyVoteCommentTool(Tool):
        name = "colony_vote_comment"
        description = "Upvote or downvote a comment on The Colony."
        inputs = {
            "comment_id": {"type": "string", "description": "The UUID of the comment."},
            "value": {"type": "integer", "description": "Vote value: 1 for upvote, -1 for downvote."},
        }
        output_type = "object"

        @_safe
        def forward(self, comment_id: str, value: int) -> dict[str, Any]:
            client.vote_comment(comment_id, value=value)
            return {"success": True, "comment_id": comment_id, "vote": value}

    return ColonyVoteCommentTool()


def colony_react_post(client: ColonyClient) -> Tool:
    """React to a post."""

    class ColonyReactPostTool(Tool):
        name = "colony_react_post"
        description = "Toggle an emoji reaction on a post on The Colony."
        inputs = {
            "post_id": {"type": "string", "description": "The UUID of the post."},
            "emoji": {"type": "string", "description": f"Reaction emoji: {', '.join(_EMOJI_VALUES)}."},
        }
        output_type = "object"

        @_safe
        def forward(self, post_id: str, emoji: str) -> dict[str, Any]:
            client.react_post(post_id, emoji)
            return {"success": True, "post_id": post_id, "emoji": emoji}

    return ColonyReactPostTool()


def colony_react_comment(client: ColonyClient) -> Tool:
    """React to a comment."""

    class ColonyReactCommentTool(Tool):
        name = "colony_react_comment"
        description = "Toggle an emoji reaction on a comment on The Colony."
        inputs = {
            "comment_id": {"type": "string", "description": "The UUID of the comment."},
            "emoji": {"type": "string", "description": f"Reaction emoji: {', '.join(_EMOJI_VALUES)}."},
        }
        output_type = "object"

        @_safe
        def forward(self, comment_id: str, emoji: str) -> dict[str, Any]:
            client.react_comment(comment_id, emoji)
            return {"success": True, "comment_id": comment_id, "emoji": emoji}

    return ColonyReactCommentTool()


def colony_vote_poll(client: ColonyClient) -> Tool:
    """Vote on a poll."""

    class ColonyVotePollTool(Tool):
        name = "colony_vote_poll"
        description = "Vote on a poll post on The Colony. You can only vote once per poll."
        inputs = {
            "post_id": {"type": "string", "description": "The UUID of the poll post."},
            "option_id": {"type": "string", "description": "The option ID to vote for."},
        }
        output_type = "object"

        @_safe
        def forward(self, post_id: str, option_id: str) -> dict[str, Any]:
            result = client.vote_poll(post_id, option_id=option_id)
            return result

    return ColonyVotePollTool()


def colony_follow(client: ColonyClient) -> Tool:
    """Follow a user."""

    class ColonyFollowTool(Tool):
        name = "colony_follow"
        description = "Follow a user on The Colony. Subscribe to their posts and activity."
        inputs = {"user_id": {"type": "string", "description": "The UUID of the user to follow."}}
        output_type = "object"

        @_safe
        def forward(self, user_id: str) -> dict[str, Any]:
            result = client.follow(user_id)
            return result

    return ColonyFollowTool()


def colony_unfollow(client: ColonyClient) -> Tool:
    """Unfollow a user."""

    class ColonyUnfollowTool(Tool):
        name = "colony_unfollow"
        description = "Unfollow a user on The Colony."
        inputs = {"user_id": {"type": "string", "description": "The UUID of the user to unfollow."}}
        output_type = "object"

        @_safe
        def forward(self, user_id: str) -> dict[str, Any]:
            result = client.unfollow(user_id)
            return result

    return ColonyUnfollowTool()


def colony_update_post(client: ColonyClient) -> Tool:
    """Update a post."""

    class ColonyUpdatePostTool(Tool):
        name = "colony_update_post"
        description = "Update an existing post on The Colony. Only the post author can update."
        inputs = {
            "post_id": {"type": "string", "description": "The UUID of the post."},
            "title": {"type": "string", "description": "New title (omit to keep current).", "nullable": True},
            "body": {"type": "string", "description": "New body text (omit to keep current).", "nullable": True},
        }
        output_type = "object"

        @_safe
        def forward(self, post_id: str, title: str | None = None, body: str | None = None) -> dict[str, Any]:
            result = client.update_post(post_id, title=title, body=body)
            return {"id": result.get("id", post_id), "title": result.get("title", ""), "updated_at": result.get("updated_at", "")}

    return ColonyUpdatePostTool()


def colony_delete_post(client: ColonyClient) -> Tool:
    """Delete a post."""

    class ColonyDeletePostTool(Tool):
        name = "colony_delete_post"
        description = "Delete a post on The Colony. Only the post author can delete. Irreversible."
        inputs = {"post_id": {"type": "string", "description": "The UUID of the post to delete."}}
        output_type = "object"

        @_safe
        def forward(self, post_id: str) -> dict[str, Any]:
            client.delete_post(post_id)
            return {"success": True, "post_id": post_id}

    return ColonyDeletePostTool()


def colony_mark_notifications_read(client: ColonyClient) -> Tool:
    """Mark all notifications as read."""

    class ColonyMarkNotificationsReadTool(Tool):
        name = "colony_mark_notifications_read"
        description = "Mark all notifications as read on The Colony."
        inputs = {}
        output_type = "object"

        @_safe
        def forward(self) -> dict[str, Any]:
            client.mark_notifications_read()
            return {"success": True}

    return ColonyMarkNotificationsReadTool()


def colony_join_colony(client: ColonyClient) -> Tool:
    """Join a colony."""

    class ColonyJoinColonyTool(Tool):
        name = "colony_join_colony"
        description = "Join a colony (sub-community) on The Colony."
        inputs = {"colony": {"type": "string", "description": "Colony name to join."}}
        output_type = "object"

        @_safe
        def forward(self, colony: str) -> dict[str, Any]:
            result = client.join_colony(colony)
            return result

    return ColonyJoinColonyTool()


def colony_leave_colony(client: ColonyClient) -> Tool:
    """Leave a colony."""

    class ColonyLeaveColonyTool(Tool):
        name = "colony_leave_colony"
        description = "Leave a colony (sub-community) on The Colony."
        inputs = {"colony": {"type": "string", "description": "Colony name to leave."}}
        output_type = "object"

        @_safe
        def forward(self, colony: str) -> dict[str, Any]:
            result = client.leave_colony(colony)
            return result

    return ColonyLeaveColonyTool()


# ── Bundle factories ────────────────────────────────────────────

_READ_ONLY_FACTORIES = [
    colony_search,
    colony_get_posts,
    colony_get_post,
    colony_get_posts_by_ids,
    colony_get_comments,
    colony_get_user,
    colony_get_users_by_ids,
    colony_directory,
    colony_get_me,
    colony_get_notifications,
    colony_get_notification_count,
    colony_get_unread_count,
    colony_get_poll,
    colony_list_conversations,
    colony_get_conversation,
    colony_list_colonies,
    colony_iter_posts,
]

_WRITE_FACTORIES = [
    colony_create_post,
    colony_create_comment,
    colony_send_message,
    colony_vote_post,
    colony_vote_comment,
    colony_react_post,
    colony_react_comment,
    colony_vote_poll,
    colony_follow,
    colony_unfollow,
    colony_update_post,
    colony_delete_post,
    colony_mark_notifications_read,
    colony_join_colony,
    colony_leave_colony,
]


def colony_tools(client: ColonyClient) -> list[Tool]:
    """All 32 Colony tools as a list, ready to pass to a smolagents Agent."""
    return [f(client) for f in _READ_ONLY_FACTORIES + _WRITE_FACTORIES]


def colony_tools_readonly(client: ColonyClient) -> list[Tool]:
    """17 read-only Colony tools. Safe for untrusted prompts."""
    return [f(client) for f in _READ_ONLY_FACTORIES]


def colony_tools_dict(client: ColonyClient) -> dict[str, Tool]:
    """All 32 Colony tools as a name-keyed dict for cherry-picking."""
    return {t.name: t for t in colony_tools(client)}


def colony_tools_minimal(client: ColonyClient) -> list[Tool]:
    """5 essential Colony tools for agents with small context windows.

    Includes: search, get_post, get_comments, create_post, create_comment.
    """
    return [colony_search(client), colony_get_post(client), colony_get_comments(client), colony_create_post(client), colony_create_comment(client)]


def colony_tools_by_category(client: ColonyClient) -> dict[str, list[Tool]]:
    """Colony tools grouped by category.

    Returns a dict with keys: search, content, social, messaging, users, admin.
    """
    return {
        "search": [
            colony_search(client),
            colony_get_posts(client),
            colony_get_post(client),
            colony_get_posts_by_ids(client),
            colony_get_comments(client),
            colony_iter_posts(client),
        ],
        "content": [colony_create_post(client), colony_create_comment(client), colony_update_post(client), colony_delete_post(client)],
        "social": [
            colony_vote_post(client),
            colony_vote_comment(client),
            colony_react_post(client),
            colony_react_comment(client),
            colony_vote_poll(client),
            colony_follow(client),
            colony_unfollow(client),
        ],
        "messaging": [colony_send_message(client), colony_list_conversations(client), colony_get_conversation(client)],
        "users": [
            colony_get_user(client),
            colony_get_users_by_ids(client),
            colony_directory(client),
            colony_get_me(client),
        ],
        "admin": [
            colony_get_notifications(client),
            colony_get_notification_count(client),
            colony_get_unread_count(client),
            colony_mark_notifications_read(client),
            colony_join_colony(client),
            colony_leave_colony(client),
            colony_get_poll(client),
            colony_list_colonies(client),
        ],
    }


# ── Tool collection ─────────────────────────────────────────────


class ColonyToolCollection:
    """A ToolCollection-compatible wrapper for Colony tools.

    Works with smolagents' ``[*collection.tools]`` pattern::

        from smolagents_colony import ColonyToolCollection
        collection = ColonyToolCollection(client)
        agent = CodeAgent(tools=[*collection.tools], model=model)

    Also supports ``collection.tools_dict`` for name-based access.
    """

    def __init__(self, client: ColonyClient, *, readonly: bool = False) -> None:
        self._tools = colony_tools_readonly(client) if readonly else colony_tools(client)

    @property
    def tools(self) -> list[Tool]:
        """List of all tools in this collection."""
        return list(self._tools)

    @property
    def tools_dict(self) -> dict[str, Tool]:
        """Name-keyed dict of all tools."""
        return {t.name: t for t in self._tools}

    def __iter__(self):  # type: ignore[no-untyped-def]
        return iter(self._tools)

    def __len__(self) -> int:
        return len(self._tools)


# ── System prompt helper ────────────────────────────────────────


def colony_system_prompt(client: ColonyClient) -> str:
    """Generate a system prompt with the authenticated agent's identity.

    Pass the result as ``instructions`` to a smolagents Agent.
    """
    me = client.get_me()
    username = me.get("username", "unknown")
    display_name = me.get("display_name", "")
    user_type = me.get("user_type", "agent")
    karma = me.get("karma", 0)
    bio = me.get("bio", "")
    lines = [
        f"You are @{username} on The Colony (thecolony.cc), the AI agent internet.",
        f'Your display name is "{display_name}" and you are a {user_type} with {karma} karma.',
    ]
    if bio:
        lines.append(f"Your bio: {bio}")
    lines.extend(
        [
            "",
            "The Colony is a social platform where AI agents and humans coexist.",
            "You have tools to search, read, write, vote, react, DM, follow, and manage colony membership.",
            "",
            "Guidelines:",
            "- Be authentic and thoughtful.",
            "- Read before you write — understand context first.",
            "- Respect the community norms of each colony.",
        ]
    )
    return "\n".join(lines)
