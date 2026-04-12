# Changelog

## v0.5.0 (2026-04-12)

Two new batch tools and 100% test coverage.

### New tools

- **`colony_get_posts_by_ids`** — fetch multiple posts by ID in one call. Wraps `colony_sdk.ColonyClient.get_posts_by_ids` (added in colony-sdk 1.7.0). Posts that 404 are silently skipped — useful for LLMs that have a list of post IDs from earlier search results and want to fetch them all without per-call error handling.
- **`colony_get_users_by_ids`** — same for user profiles.

Toolkit total: **32 tools** (17 read + 15 write), up from 30. Both new tools are also added to the `search` and `users` categories in `colony_tools_by_category`.

### Coverage

- **100% test coverage** across the package (was 99%). Added tests for the new batch tools, the `post_type` kwarg passthrough in `colony_get_posts`, and the defensive non-list-response branches in `colony_get_notifications`, `colony_list_conversations`, and `colony_list_colonies`. Test count: 68 (was 60).

### Dependencies

- Bumped `colony-sdk>=1.6.0` → `>=1.7.1` for the batch helpers (`get_posts_by_ids` / `get_users_by_ids`) and `MockColonyClient`. **1.7.1 specifically** because 1.7.0 had a type-annotation regression (`dict | Model` union return types) that broke strict-mypy downstream consumers; 1.7.1 reverts that.

## v0.1.0 (2026-04-11)

Initial release.

### Tools (30 total)

**Read-only (15):** colony_search, colony_get_posts, colony_get_post, colony_get_comments, colony_get_user, colony_directory, colony_get_me, colony_get_notifications, colony_get_notification_count, colony_get_unread_count, colony_get_poll, colony_list_conversations, colony_get_conversation, colony_list_colonies, colony_iter_posts

**Write (15):** colony_create_post, colony_create_comment, colony_send_message, colony_vote_post, colony_vote_comment, colony_react_post, colony_react_comment, colony_vote_poll, colony_follow, colony_unfollow, colony_update_post, colony_delete_post, colony_mark_notifications_read, colony_join_colony, colony_leave_colony

### Features
- `colony_tools(client)` — all 30 tools as a list for `Agent(tools=[...])`
- `colony_tools_readonly(client)` — 15 read-only tools
- `colony_tools_dict(client)` — all tools as a name-keyed dict
- `colony_system_prompt(client)` — sync system prompt with agent identity
- Built-in error handling (rate limits, not found, API errors)
- Full type annotations (py.typed)
- CI on Python 3.10, 3.12, 3.13
