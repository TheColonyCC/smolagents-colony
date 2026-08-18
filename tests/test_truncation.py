"""Our own cuts have to announce themselves.

A bare ``text[:limit]`` hands a model a fragment it cannot tell apart from a
whole post. On 2026-08-18 that produced a false public claim: a sibling package
cut a 1,699 character post to 1,500, and the agent reading it correctly saw the
text stop mid-sentence and reported that the *author* had posted it that way.
It was truthful about the bytes it received.

Every arm here is paired with a control. A marker present on everything carries
no more information than one present on nothing.
"""

from __future__ import annotations

from smolagents_colony.tools import _bio_fields, _body_fields, _comment_body_fields, _excerpt

LONG = "x" * 1699
SHORT = "a complete short body."


class TestExcerpt:
    def test_long_text_is_cut_and_says_so(self) -> None:
        out, cut = _excerpt(LONG, 1500)
        assert cut is True
        assert "cut by smolagents-colony" in out
        assert "at 1500 of 1699 chars" in out

    def test_short_text_is_byte_identical(self) -> None:
        """The control."""
        out, cut = _excerpt(SHORT, 1500)
        assert out == SHORT and cut is False and "cut by" not in out

    def test_exactly_at_the_limit_is_untouched(self) -> None:
        exact = "y" * 1500
        assert _excerpt(exact, 1500) == (exact, False)

    def test_one_over_is_cut(self) -> None:
        out, cut = _excerpt("y" * 1501, 1500)
        assert cut is True and "at 1500 of 1501 chars" in out

    def test_empty_is_not_cut(self) -> None:
        assert _excerpt("", 1500) == ("", False)

    def test_the_marker_blames_us_not_the_author(self) -> None:
        out, _ = _excerpt(LONG, 1500)
        assert "OUR cut, not the author's" in out
        assert "the source is not malformed" in out

    def test_hint_only_when_a_tool_really_helps(self) -> None:
        with_hint, _ = _excerpt(LONG, 1500, full_text="colony_get_post(post_id)")
        assert "Call colony_get_post(post_id) for the full text." in with_hint
        without, _ = _excerpt(LONG, 1500)
        assert "Call " not in without


class TestFieldHelpers:
    def test_post_body_is_flagged_and_marked(self) -> None:
        f = _body_fields({"body": LONG}, 500)
        assert f["body_is_truncated"] is True
        assert "cut by smolagents-colony" in f["body"]
        assert f["body"] != LONG[:500]  # mutation arm: a bare slice fails here

    def test_short_post_body_is_untouched(self) -> None:
        f = _body_fields({"body": SHORT}, 500)
        assert f["body"] == SHORT and f["body_is_truncated"] is False

    def test_missing_body_is_not_flagged(self) -> None:
        assert _body_fields({}, 500) == {"body": "", "body_is_truncated": False}

    def test_bio_is_flagged_and_points_at_get_user(self) -> None:
        f = _bio_fields({"bio": LONG}, 200)
        assert f["bio_is_truncated"] is True
        assert "colony_get_user(user_id)" in f["bio"]

    def test_comment_body_is_flagged_with_no_hint(self) -> None:
        """No tool returns an untruncated comment body; do not invent advice."""
        f = _comment_body_fields({"body": LONG}, 500)
        assert f["body_is_truncated"] is True
        assert "Call " not in f["body"]
