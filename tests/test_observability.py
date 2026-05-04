"""Tests for the FinishReasonStepCallback observability helper."""

from __future__ import annotations

from types import SimpleNamespace

from smolagents_colony import FinishReasonStepCallback
from smolagents_colony.observability import _extract_finish_reason


def _step_with_raw(raw) -> SimpleNamespace:
    """Build a minimal ActionStep-shaped object with a model_output_message
    whose raw field carries (some shape of) finish_reason metadata.
    """
    msg = SimpleNamespace(raw=raw)
    return SimpleNamespace(model_output_message=msg)


def _empty_step() -> SimpleNamespace:
    """Step with no model_output_message."""
    return SimpleNamespace(model_output_message=None)


# ── _extract_finish_reason ─────────────────────────────────────────


class TestExtractFinishReason:
    def test_openai_choices_dict(self):
        step = _step_with_raw({"choices": [{"finish_reason": "stop"}]})
        assert _extract_finish_reason(step) == "stop"

    def test_top_level_in_dict(self):
        step = _step_with_raw({"finish_reason": "length"})
        assert _extract_finish_reason(step) == "length"

    def test_top_level_attr_on_object(self):
        step = _step_with_raw(SimpleNamespace(finish_reason="length"))
        assert _extract_finish_reason(step) == "length"

    def test_choices_attr_on_object(self):
        choice = SimpleNamespace(finish_reason="stop")
        step = _step_with_raw(SimpleNamespace(choices=[choice]))
        assert _extract_finish_reason(step) == "stop"

    def test_stop_reason_alias_in_choice(self):
        step = _step_with_raw({"choices": [{"stop_reason": "length"}]})
        assert _extract_finish_reason(step) == "length"

    def test_no_model_output_message(self):
        assert _extract_finish_reason(_empty_step()) is None

    def test_no_raw(self):
        msg = SimpleNamespace(raw=None)
        step = SimpleNamespace(model_output_message=msg)
        assert _extract_finish_reason(step) is None

    def test_empty_raw_dict(self):
        step = _step_with_raw({})
        assert _extract_finish_reason(step) is None

    def test_empty_choices_list(self):
        step = _step_with_raw({"choices": []})
        assert _extract_finish_reason(step) is None

    def test_choices_with_no_finish_reason(self):
        step = _step_with_raw({"choices": [{"message": {"content": "hi"}}]})
        assert _extract_finish_reason(step) is None

    def test_step_without_model_output_message_attr(self):
        # MemoryStep shape that isn't an ActionStep — e.g. PlanningStep.
        step = SimpleNamespace()
        assert _extract_finish_reason(step) is None


# ── FinishReasonStepCallback ───────────────────────────────────────


class TestFinishReasonStepCallback:
    def test_initial_state(self):
        cb = FinishReasonStepCallback()
        assert cb.last_finish_reason is None
        assert cb.length_count == 0
        assert cb.total_count == 0

    def test_stop_increments_total_only(self):
        cb = FinishReasonStepCallback(log_level=None)
        cb(_step_with_raw({"choices": [{"finish_reason": "stop"}]}))
        assert cb.last_finish_reason == "stop"
        assert cb.length_count == 0
        assert cb.total_count == 1

    def test_length_increments_both_counters(self):
        cb = FinishReasonStepCallback(log_level=None)
        cb(_step_with_raw({"choices": [{"finish_reason": "length"}]}))
        assert cb.last_finish_reason == "length"
        assert cb.length_count == 1
        assert cb.total_count == 1

    def test_no_op_when_no_finish_reason(self):
        cb = FinishReasonStepCallback(log_level=None)
        cb(_empty_step())
        assert cb.total_count == 0
        assert cb.last_finish_reason is None

    def test_warning_emitted_on_length(self, caplog):
        cb = FinishReasonStepCallback()
        with caplog.at_level("WARNING", logger="smolagents_colony"):
            cb(_step_with_raw({"choices": [{"finish_reason": "length"}]}))
        assert any("finish_reason=length" in record.message for record in caplog.records)

    def test_no_warning_on_stop(self, caplog):
        cb = FinishReasonStepCallback()
        with caplog.at_level("WARNING", logger="smolagents_colony"):
            cb(_step_with_raw({"choices": [{"finish_reason": "stop"}]}))
        assert not any("finish_reason=length" in record.message for record in caplog.records)

    def test_log_level_none_silences_warning(self, caplog):
        cb = FinishReasonStepCallback(log_level=None)
        with caplog.at_level("WARNING", logger="smolagents_colony"):
            cb(_step_with_raw({"choices": [{"finish_reason": "length"}]}))
        assert cb.length_count == 1
        assert not any("finish_reason=length" in record.message for record in caplog.records)

    def test_kwargs_accepted(self):
        # smolagents' callback registry passes agent= as a kwarg when
        # the callable signature allows it. Ours should accept it without
        # blowing up.
        cb = FinishReasonStepCallback(log_level=None)
        cb(
            _step_with_raw({"choices": [{"finish_reason": "length"}]}),
            agent="agent-stub",
        )
        assert cb.length_count == 1

    def test_multiple_steps_track_last(self):
        cb = FinishReasonStepCallback(log_level=None)
        cb(_step_with_raw({"choices": [{"finish_reason": "stop"}]}))
        cb(_step_with_raw({"choices": [{"finish_reason": "length"}]}))
        cb(_step_with_raw({"choices": [{"finish_reason": "stop"}]}))
        assert cb.last_finish_reason == "stop"
        assert cb.length_count == 1
        assert cb.total_count == 3

    def test_reset_clears_state(self):
        cb = FinishReasonStepCallback(log_level=None)
        cb(_step_with_raw({"choices": [{"finish_reason": "length"}]}))
        cb(_step_with_raw({"choices": [{"finish_reason": "stop"}]}))
        cb.reset()
        assert cb.last_finish_reason is None
        assert cb.length_count == 0
        assert cb.total_count == 0
