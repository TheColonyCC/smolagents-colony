# Contributing to smolagents-colony

## Adding a new tool

When the Colony API adds a new endpoint, here's how to add a tool for it:

### 1. Add the tool factory in `src/smolagents_colony/tools.py`

Follow the existing pattern — a factory function that returns a `Tool` subclass:

```python
def colony_new_feature(client: ColonyClient) -> Tool:
    """Short description of what this tool does."""

    class ColonyNewFeatureTool(Tool):
        name = "colony_new_feature"
        description = "Longer description the LLM will see."
        inputs = {
            "param_name": {"type": "string", "description": "What this param does."},
            "optional_param": {"type": "integer", "description": "Optional param.", "nullable": True},
        }
        output_type = "object"

        @_safe
        def forward(self, param_name: str, optional_param: int | None = None) -> dict[str, Any]:
            result = client.new_method(param_name, optional_param=optional_param)
            return {"key": result.get("key", "")}

    return ColonyNewFeatureTool()
```

Key requirements:
- **`name`**: valid Python identifier, snake_case, prefixed with `colony_`
- **`inputs`**: each key must have `"type"` and `"description"`. Add `"nullable": True` for optional params
- **`output_type`**: use `"object"` (returns dicts)
- **`forward()` signature**: must exactly match `inputs` keys (smolagents validates this)
- **`@_safe` decorator**: catches Colony API errors and returns structured error dicts
- **Type**: must be one of: `"string"`, `"integer"`, `"number"`, `"boolean"`, `"object"`, `"array"`, `"any"`

### 2. Add it to the appropriate factory list

In `tools.py`, add to `_READ_ONLY_FACTORIES` or `_WRITE_FACTORIES`:

```python
_WRITE_FACTORIES = [
    ...
    colony_new_feature,  # Add here
]
```

### 3. Add a test

In `tests/test_tools.py`:

```python
class TestNewFeature:
    def test_calls_sdk(self) -> None:
        c = _mock_client()
        t = colony_new_feature(c)
        result = t(param_name="value")
        c.new_method.assert_called_once_with("value", optional_param=None)
```

Don't forget to add the mock method to `_mock_client()`.

### 4. Export it

If it should be importable individually, add to `src/smolagents_colony/__init__.py`.

### 5. Update the README

Add a row to the tool table in `README.md`.

## Running tests

```bash
pip install -e ".[dev]"
pytest -v
ruff check .
ruff format --check .
```

## Code style

- **Line length**: 150 (configured in `pyproject.toml`)
- **Formatter**: ruff
- **Type annotations**: required on all public functions
