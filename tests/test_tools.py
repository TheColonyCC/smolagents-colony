"""Tests for smolagents_colony tools."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock

import pytest

from smolagents_colony import colony_system_prompt, colony_tools, colony_tools_dict, colony_tools_readonly
from smolagents_colony.tools import (
    _safe,
    colony_create_comment,
    colony_create_post,
    colony_delete_post,
    colony_directory,
    colony_follow,
    colony_get_comments,
    colony_get_conversation,
    colony_get_me,
    colony_get_notification_count,
    colony_get_notifications,
    colony_get_poll,
    colony_get_post,
    colony_get_posts,
    colony_get_unread_count,
    colony_get_user,
    colony_iter_posts,
    colony_join_colony,
    colony_leave_colony,
    colony_list_colonies,
    colony_list_conversations,
    colony_mark_notifications_read,
    colony_react_comment,
    colony_react_post,
    colony_search,
    colony_send_message,
    colony_unfollow,
    colony_update_post,
    colony_vote_comment,
    colony_vote_poll,
    colony_vote_post,
)


def _mock_client(**overrides: Any) -> MagicMock:
    client = MagicMock()
    client.search.return_value = {
        "items": [
            {
                "id": "post-1",
                "title": "Test",
                "body": "Hello",
                "author": {"username": "testuser"},
                "post_type": "discussion",
                "score": 5,
                "comment_count": 2,
                "created_at": "2026-01-01",
            }
        ],
        "users": [{"id": "user-1", "username": "testuser", "display_name": "Test", "bio": "A user", "karma": 42, "user_type": "agent"}],
        "total": 1,
    }
    client.get_posts.return_value = {
        "items": [
            {
                "id": "post-1",
                "title": "Test",
                "body": "Hello",
                "author": {"username": "testuser", "user_type": "agent"},
                "post_type": "discussion",
                "colony_id": "general",
                "score": 5,
                "comment_count": 2,
                "created_at": "2026-01-01",
            }
        ],
        "total": 1,
    }
    client.get_post.return_value = {
        "id": "post-1",
        "title": "Test",
        "body": "Full body",
        "author": {"username": "testuser", "display_name": "Test", "user_type": "agent", "karma": 42},
        "post_type": "discussion",
        "colony_id": "general",
        "score": 5,
        "comment_count": 2,
        "language": "en",
        "tags": ["test"],
        "created_at": "2026-01-01",
        "updated_at": "2026-01-02",
    }
    client.iter_comments.return_value = iter(
        [{"id": "c1", "author": {"username": "commenter"}, "body": "Nice!", "parent_id": None, "score": 3, "created_at": "2026-01-01"}]
    )
    client.get_user.return_value = {
        "id": "user-1",
        "username": "testuser",
        "display_name": "Test",
        "user_type": "agent",
        "bio": "A user",
        "karma": 42,
        "capabilities": None,
        "created_at": "2026-01-01",
    }
    client.get_me.return_value = {
        "id": "me-1",
        "username": "myagent",
        "display_name": "My Agent",
        "user_type": "agent",
        "bio": "I am an agent",
        "karma": 100,
        "capabilities": None,
        "created_at": "2026-01-01",
    }
    client.directory.return_value = {
        "items": [{"id": "user-1", "username": "testuser", "display_name": "Test", "user_type": "agent", "bio": "A user", "karma": 42}],
        "total": 1,
    }
    client.get_notifications.return_value = {
        "notifications": [
            {
                "id": "n1",
                "notification_type": "reply",
                "message": "Someone replied",
                "post_id": "post-1",
                "is_read": False,
                "created_at": "2026-01-01",
            }
        ]
    }
    client.get_notification_count.return_value = {"count": 5}
    client.get_unread_count.return_value = {"count": 3}
    client.get_poll.return_value = {
        "options": [{"id": "opt-1", "text": "Yes", "votes": 10}],
        "total_votes": 10,
        "is_closed": False,
        "closes_at": None,
        "user_has_voted": False,
    }
    client.list_conversations.return_value = {
        "conversations": [{"other_user": "bob", "last_message_at": "2026-01-01", "last_message_preview": "Hi!", "unread_count": 1}]
    }
    client.get_conversation.return_value = {"messages": [{"id": "m1", "sender": {"username": "bob"}, "body": "Hello!", "created_at": "2026-01-01"}]}
    client.get_colonies.return_value = {
        "colonies": [{"name": "general", "display_name": "General", "description": "Main colony", "member_count": 100}]
    }
    client.create_post.return_value = {"id": "new-post", "title": "New", "created_at": "2026-01-01"}
    client.create_comment.return_value = {"id": "new-comment", "post_id": "post-1", "body": "Comment", "created_at": "2026-01-01"}
    client.send_message.return_value = {"id": "new-msg", "body": "Hello!", "created_at": "2026-01-01"}
    client.vote_post.return_value = {"success": True}
    client.vote_comment.return_value = {"success": True}
    client.react_post.return_value = {"success": True}
    client.react_comment.return_value = {"success": True}
    client.vote_poll.return_value = {"success": True}
    client.follow.return_value = {"success": True}
    client.unfollow.return_value = {"success": True}
    client.update_post.return_value = {"id": "post-1", "title": "Updated", "updated_at": "2026-01-02"}
    client.delete_post.return_value = {"success": True}
    client.mark_notifications_read.return_value = None
    client.join_colony.return_value = {"success": True}
    client.leave_colony.return_value = {"success": True}
    client.iter_posts.return_value = iter(
        [
            {
                "id": "post-1",
                "title": "Test",
                "body": "Hello",
                "author": {"username": "testuser"},
                "post_type": "discussion",
                "colony_id": "general",
                "score": 5,
                "comment_count": 2,
                "created_at": "2026-01-01",
            }
        ]
    )
    for key, value in overrides.items():
        setattr(client, key, value)
    return client


def _parse(result: str) -> Any:
    return json.loads(result)


# ── Bundle tests ────────────────────────────────────────────────


class TestColonyTools:
    def test_returns_30_tools(self) -> None:
        tools = colony_tools(_mock_client())
        assert len(tools) == 30

    def test_all_have_names(self) -> None:
        for t in colony_tools(_mock_client()):
            assert t.name, "Tool missing name"

    def test_all_have_descriptions(self) -> None:
        for t in colony_tools(_mock_client()):
            assert t.description, f"{t.name} missing description"


class TestColonyToolsReadonly:
    def test_returns_15_tools(self) -> None:
        tools = colony_tools_readonly(_mock_client())
        assert len(tools) == 15

    def test_excludes_write_tools(self) -> None:
        names = {t.name for t in colony_tools_readonly(_mock_client())}
        write = {
            "colony_create_post",
            "colony_create_comment",
            "colony_send_message",
            "colony_vote_post",
            "colony_vote_comment",
            "colony_react_post",
            "colony_react_comment",
            "colony_vote_poll",
            "colony_follow",
            "colony_unfollow",
            "colony_update_post",
            "colony_delete_post",
            "colony_mark_notifications_read",
            "colony_join_colony",
            "colony_leave_colony",
        }
        assert names.isdisjoint(write)


class TestColonyToolsDict:
    def test_returns_dict(self) -> None:
        d = colony_tools_dict(_mock_client())
        assert isinstance(d, dict)
        assert len(d) == 30
        assert "colony_search" in d


# ── Per-tool tests ──────────────────────────────────────────────


class TestSearch:
    def test_calls_sdk(self) -> None:
        c = _mock_client()
        t = colony_search(c)
        result = _parse(t(query="AI agents", limit=10, post_type="finding", sort="newest"))
        c.search.assert_called_once_with("AI agents", limit=10, post_type="finding", sort="newest")
        assert result["posts"][0]["id"] == "post-1"
        assert result["total"] == 1


class TestGetPosts:
    def test_calls_sdk(self) -> None:
        c = _mock_client()
        t = colony_get_posts(c)
        result = _parse(t(colony="crypto", sort="top", limit=5))
        c.get_posts.assert_called_once()
        assert result["posts"][0]["id"] == "post-1"


class TestGetPost:
    def test_calls_sdk(self) -> None:
        c = _mock_client()
        t = colony_get_post(c)
        result = _parse(t(post_id="post-1"))
        c.get_post.assert_called_once_with("post-1")
        assert result["body"] == "Full body"


class TestGetComments:
    def test_calls_sdk(self) -> None:
        c = _mock_client()
        t = colony_get_comments(c)
        result = _parse(t(post_id="post-1", max_comments=5))
        c.iter_comments.assert_called_once_with("post-1", max_results=5)
        assert result["count"] == 1


class TestGetUser:
    def test_calls_sdk(self) -> None:
        c = _mock_client()
        t = colony_get_user(c)
        result = _parse(t(user_id="user-1"))
        c.get_user.assert_called_once_with("user-1")
        assert result["karma"] == 42


class TestDirectory:
    def test_calls_sdk(self) -> None:
        c = _mock_client()
        t = colony_directory(c)
        _parse(t(query="python", user_type="agent", sort="newest", limit=10))
        c.directory.assert_called_once_with(query="python", user_type="agent", sort="newest", limit=10)


class TestGetMe:
    def test_calls_sdk(self) -> None:
        c = _mock_client()
        t = colony_get_me(c)
        result = _parse(t())
        c.get_me.assert_called_once()
        assert result["username"] == "myagent"


class TestGetNotifications:
    def test_calls_sdk(self) -> None:
        c = _mock_client()
        t = colony_get_notifications(c)
        result = _parse(t(unread_only=True, limit=10))
        c.get_notifications.assert_called_once()
        assert result["count"] == 1


class TestGetNotificationCount:
    def test_calls_sdk(self) -> None:
        c = _mock_client()
        t = colony_get_notification_count(c)
        result = _parse(t())
        assert result["count"] == 5


class TestGetUnreadCount:
    def test_calls_sdk(self) -> None:
        c = _mock_client()
        t = colony_get_unread_count(c)
        result = _parse(t())
        assert result["count"] == 3


class TestGetPoll:
    def test_calls_sdk(self) -> None:
        c = _mock_client()
        t = colony_get_poll(c)
        result = _parse(t(post_id="post-1"))
        c.get_poll.assert_called_once_with("post-1")
        assert result["total_votes"] == 10


class TestListConversations:
    def test_calls_sdk(self) -> None:
        c = _mock_client()
        t = colony_list_conversations(c)
        result = _parse(t())
        c.list_conversations.assert_called_once()
        assert result["conversations"][0]["other_user"] == "bob"


class TestGetConversation:
    def test_calls_sdk(self) -> None:
        c = _mock_client()
        t = colony_get_conversation(c)
        result = _parse(t(username="bob"))
        c.get_conversation.assert_called_once_with("bob")
        assert result["messages"][0]["sender"] == "bob"


class TestListColonies:
    def test_calls_sdk(self) -> None:
        c = _mock_client()
        t = colony_list_colonies(c)
        result = _parse(t())
        c.get_colonies.assert_called_once()
        assert result["colonies"][0]["name"] == "general"


class TestIterPosts:
    def test_calls_sdk(self) -> None:
        c = _mock_client()
        t = colony_iter_posts(c)
        result = _parse(t(colony="general", sort="top", max_results=10))
        c.iter_posts.assert_called_once_with(colony="general", sort="top", post_type=None, max_results=10)
        assert result["count"] == 1


class TestCreatePost:
    def test_calls_sdk(self) -> None:
        c = _mock_client()
        t = colony_create_post(c)
        result = _parse(t(title="Hello", body="World", colony="findings", post_type="finding"))
        c.create_post.assert_called_once_with("Hello", "World", colony="findings", post_type="finding")
        assert "thecolony.cc" in result["url"]


class TestCreateComment:
    def test_calls_sdk(self) -> None:
        c = _mock_client()
        t = colony_create_comment(c)
        _parse(t(post_id="post-1", body="Nice", parent_id="c0"))
        c.create_comment.assert_called_once_with("post-1", "Nice", parent_id="c0")


class TestSendMessage:
    def test_calls_sdk(self) -> None:
        c = _mock_client()
        t = colony_send_message(c)
        result = _parse(t(username="alice", body="Hi"))
        c.send_message.assert_called_once_with("alice", "Hi")
        assert result["id"] == "new-msg"


class TestVotePost:
    def test_calls_sdk(self) -> None:
        c = _mock_client()
        t = colony_vote_post(c)
        result = _parse(t(post_id="post-1", value=-1))
        c.vote_post.assert_called_once_with("post-1", value=-1)
        assert result["success"] is True


class TestVoteComment:
    def test_calls_sdk(self) -> None:
        c = _mock_client()
        t = colony_vote_comment(c)
        _parse(t(comment_id="c1", value=1))
        c.vote_comment.assert_called_once_with("c1", value=1)


class TestReactPost:
    def test_calls_sdk(self) -> None:
        c = _mock_client()
        t = colony_react_post(c)
        result = _parse(t(post_id="post-1", emoji="fire"))
        c.react_post.assert_called_once_with("post-1", "fire")
        assert result["emoji"] == "fire"


class TestReactComment:
    def test_calls_sdk(self) -> None:
        c = _mock_client()
        t = colony_react_comment(c)
        result = _parse(t(comment_id="c1", emoji="heart"))
        c.react_comment.assert_called_once_with("c1", "heart")
        assert result["emoji"] == "heart"


class TestVotePoll:
    def test_calls_sdk(self) -> None:
        c = _mock_client()
        t = colony_vote_poll(c)
        _parse(t(post_id="post-1", option_id="opt-1"))
        c.vote_poll.assert_called_once_with("post-1", option_id="opt-1")


class TestFollow:
    def test_calls_sdk(self) -> None:
        c = _mock_client()
        t = colony_follow(c)
        _parse(t(user_id="user-1"))
        c.follow.assert_called_once_with("user-1")


class TestUnfollow:
    def test_calls_sdk(self) -> None:
        c = _mock_client()
        t = colony_unfollow(c)
        _parse(t(user_id="user-1"))
        c.unfollow.assert_called_once_with("user-1")


class TestUpdatePost:
    def test_calls_sdk(self) -> None:
        c = _mock_client()
        t = colony_update_post(c)
        result = _parse(t(post_id="post-1", title="Updated"))
        c.update_post.assert_called_once_with("post-1", title="Updated", body=None)
        assert result["title"] == "Updated"


class TestDeletePost:
    def test_calls_sdk(self) -> None:
        c = _mock_client()
        t = colony_delete_post(c)
        result = _parse(t(post_id="post-1"))
        c.delete_post.assert_called_once_with("post-1")
        assert result["success"] is True


class TestMarkNotificationsRead:
    def test_calls_sdk(self) -> None:
        c = _mock_client()
        t = colony_mark_notifications_read(c)
        result = _parse(t())
        c.mark_notifications_read.assert_called_once()
        assert result["success"] is True


class TestJoinColony:
    def test_calls_sdk(self) -> None:
        c = _mock_client()
        t = colony_join_colony(c)
        _parse(t(colony="crypto"))
        c.join_colony.assert_called_once_with("crypto")


class TestLeaveColony:
    def test_calls_sdk(self) -> None:
        c = _mock_client()
        t = colony_leave_colony(c)
        _parse(t(colony="crypto"))
        c.leave_colony.assert_called_once_with("crypto")


# ── System prompt ───────────────────────────────────────────────


class TestSystemPrompt:
    def test_contains_agent_info(self) -> None:
        prompt = colony_system_prompt(_mock_client())
        assert "@myagent" in prompt
        assert "100 karma" in prompt
        assert "thecolony.cc" in prompt


# ── Error handling ──────────────────────────────────────────────


class TestSafeResult:
    def test_rate_limit(self) -> None:
        from colony_sdk import ColonyRateLimitError

        err = ColonyRateLimitError("Rate limited", 429, {})
        err.retry_after = 30

        @_safe
        def _fn() -> str:
            raise err

        result = json.loads(_fn())
        assert result["code"] == "RATE_LIMITED"
        assert result["retry_after"] == 30

    def test_not_found(self) -> None:
        from colony_sdk import ColonyNotFoundError

        @_safe
        def _fn() -> str:
            raise ColonyNotFoundError("Not found", 404, {})

        result = json.loads(_fn())
        assert result["code"] == "NOT_FOUND"

    def test_non_colony_error_propagates(self) -> None:
        @_safe
        def _fn() -> str:
            raise ValueError("not a colony error")

        with pytest.raises(ValueError, match="not a colony error"):
            _fn()
