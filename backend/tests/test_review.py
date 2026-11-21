import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.review import DEFAULT_MODEL, _validate_review, review_plan  # noqa: E402


class MockCompletions:
    def create(self, **kwargs):
        assert kwargs["model"] == DEFAULT_MODEL
        assert kwargs["response_format"]["type"] == "json_schema"
        assert kwargs["response_format"]["json_schema"]["strict"] is True
        content = '{"deadline_day": 10, "tasks": [], "findings": []}'
        message = SimpleNamespace(content=content)
        choice = SimpleNamespace(message=message)
        return SimpleNamespace(choices=[choice])


class MockClient:
    chat = SimpleNamespace(completions=MockCompletions())


def test_review_plan_uses_openrouter_compatible_response(monkeypatch):
    monkeypatch.delenv("REVIEW_MODEL", raising=False)
    review = review_plan("Test plan", client=MockClient())
    assert review == {"deadline_day": 10, "tasks": [], "findings": []}


def test_review_rejects_non_contract_fields():
    review = {
        "deadline_day": 10,
        "tasks": [{"name": "Task", "who": "Ann"}],
        "findings": ["Not an object"],
    }
    try:
        _validate_review(review, "Task")
    except ValueError as error:
        assert "tasks[0].id must be a string" in str(error)
        assert "tasks[0].owner is required" in str(error)
        assert "findings[0] must be an object" in str(error)
    else:
        raise AssertionError("Invalid review should be rejected")


def test_review_rejects_quotes_not_found_in_plan():
    review = {
        "deadline_day": None,
        "tasks": [
            {
                "id": "T1",
                "name": "Task",
                "owner": None,
                "duration_days": 1,
                "depends_on": [],
                "quote": "Invented task quote",
            }
        ],
        "findings": [],
    }
    try:
        _validate_review(review, "Task")
    except ValueError as error:
        assert "tasks[0].quote is not in the plan" in str(error)
    else:
        raise AssertionError("Invalid quote should be rejected")
