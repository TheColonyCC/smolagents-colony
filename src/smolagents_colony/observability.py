"""Observability helpers for smolagents-colony agents.

Currently exposes one helper: :class:`FinishReasonStepCallback`, which
detects silent token-budget truncations on local-Ollama (and other)
inference backends. See
https://thecolony.cc/post/488740e9-c8e5-4ccd-abe7-6156a53e9359 for the
failure-mode writeup.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("smolagents_colony")


def _extract_finish_reason(memory_step: Any) -> str | None:
    """Pull a single ``finish_reason`` from a smolagents memory step.

    The model output for an :class:`smolagents.memory.ActionStep` lives
    on ``step.model_output_message`` (a :class:`smolagents.models.ChatMessage`).
    For OpenAI-compatible providers, the full provider response is
    stashed on ``ChatMessage.raw`` — typically a dict shaped like
    ``{"choices": [{"finish_reason": "stop", ...}]}``. Some providers
    promote ``finish_reason`` to a top-level attribute on the raw object;
    we check both.

    Returns the value as a string, or ``None`` when the metadata isn't
    surfaced. Duck-typed throughout so this keeps working across
    smolagents versions.
    """
    msg = getattr(memory_step, "model_output_message", None)
    if msg is None:
        return None
    raw = getattr(msg, "raw", None)
    if raw is None:
        return None
    # Top-level attribute first (some providers / wrappers).
    direct = getattr(raw, "finish_reason", None)
    if direct:
        return str(direct)
    # Dict shapes.
    if isinstance(raw, dict):
        if raw.get("finish_reason"):
            return str(raw["finish_reason"])
        choices = raw.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                value = first.get("finish_reason") or first.get("stop_reason")
                if value:
                    return str(value)
    # Object-with-choices fallback (e.g. an OpenAI SDK response object
    # that wasn't dict-coerced before being stored).
    choices_attr = getattr(raw, "choices", None)
    if isinstance(choices_attr, list) and choices_attr:
        first = choices_attr[0]
        value = getattr(first, "finish_reason", None) or getattr(first, "stop_reason", None)
        if value:
            return str(value)
    return None


class FinishReasonStepCallback:
    """smolagents step callback that surfaces LLM ``finish_reason``.

    The OpenAI-compatible response shape includes a ``finish_reason``
    field — ``stop`` when the model finished naturally, ``length`` when
    it hit the token cap mid-thought. smolagents stores the raw
    provider response on ``ChatMessage.raw`` but the agent loop never
    reads it, so a length-truncated step is treated as a low-quality
    but valid step. With qwen3 / other reasoning-mode models on a
    tight ``num_predict``, that's the silent-fail pattern documented at
    https://thecolony.cc/post/488740e9-c8e5-4ccd-abe7-6156a53e9359.

    Register the callback when constructing your agent::

        from smolagents import CodeAgent
        from smolagents_colony import colony_tools, FinishReasonStepCallback

        cb = FinishReasonStepCallback()
        agent = CodeAgent(
            tools=colony_tools(client),
            model=...,
            step_callbacks=[cb],
        )

        agent.run("...")

        if cb.length_count:
            print(f"hit num_predict {cb.length_count} time(s)")

    Works with both ``CodeAgent`` and ``ToolCallingAgent`` since both
    fire step callbacks against ``ActionStep`` instances by default.

    Args:
        log_level: Logging level for the warning emitted on ``length``.
            Set to ``None`` to disable logging and only collect counters.
            Defaults to ``logging.WARNING``.
    """

    #: The most recently observed finish_reason, or ``None`` if no step
    #: with surfaced finish_reason has fired.
    last_finish_reason: str | None

    #: Count of steps where ``finish_reason == "length"``.
    length_count: int

    #: Count of all steps observed (with surfaced finish_reason).
    total_count: int

    def __init__(self, log_level: int | None = logging.WARNING) -> None:
        self.log_level = log_level
        self.last_finish_reason = None
        self.length_count = 0
        self.total_count = 0

    def __call__(self, memory_step: Any, **kwargs: Any) -> None:  # noqa: ARG002
        """Inspect the step's model output for ``finish_reason``.

        Conforms to smolagents' step-callback signature (single-arg or
        multi-arg-with-``agent`` both accepted by the registry).
        """
        reason = _extract_finish_reason(memory_step)
        if reason is None:
            return
        self.total_count += 1
        self.last_finish_reason = reason
        if reason == "length":
            self.length_count += 1
            if self.log_level is not None:
                logger.log(
                    self.log_level,
                    "LLM finish_reason=length — likely truncated step, consider raising max_tokens / num_predict",
                )

    def reset(self) -> None:
        """Reset counters and the last-seen reason."""
        self.last_finish_reason = None
        self.length_count = 0
        self.total_count = 0
