import json
import os
import re
import sys

from openai import OpenAI

DEFAULT_MODEL = "nvidia/nemotron-3.5-super-vl:free"
PROMPT = (
    "Review the complete project plan. Return a JSON object matching the supplied "
    "schema. Extract every task, with a unique short id, exact task name, owner "
    "(or null), positive integer duration_days, and depends_on containing only "
    "other task ids. Include a quote copied verbatim from the plan for every task. "
    "Use integer deadline_day or null if unclear. Findings must each have a title, "
    "detail, and a verbatim quote from the plan, or null if no supporting quote "
    "exists. Do not invent quotes."
)


REVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "deadline_day": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
        "tasks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "owner": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "duration_days": {"type": "integer", "minimum": 1},
                    "depends_on": {"type": "array", "items": {"type": "string"}},
                    "quote": {"type": "string"},
                },
                "required": [
                    "id",
                    "name",
                    "owner",
                    "duration_days",
                    "depends_on",
                    "quote",
                ],
                "additionalProperties": False,
            },
        },
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "detail": {"type": "string"},
                    "quote": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                },
                "required": ["title", "detail", "quote"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["deadline_day", "tasks", "findings"],
    "additionalProperties": False,
}


def _get_content(reply):
    if hasattr(reply, "choices"):
        content = reply.choices[0].message.content
    else:
        content = reply["choices"][0]["message"]["content"]
    if not isinstance(content, str):
        raise ValueError("The model returned no text content.")
    return content


def _parse_json(content):
    content = content.strip()
    if content.startswith("```"):
        content = content.split("```", 2)[1]
        if content.startswith("json"):
            content = content[4:]
    content = content.strip()
    return json.loads(content)


def _normalized(text):
    return re.sub(r"\s+", " ", text).strip()


def _validate_review(review, plan_text):
    errors = []
    if not isinstance(review, dict):
        raise ValueError("The model response must be a JSON object.")

    deadline = review.get("deadline_day")
    if "deadline_day" not in review or (
        deadline is not None and type(deadline) is not int
    ):
        errors.append("deadline_day must be an integer or null")

    tasks = review.get("tasks")
    if not isinstance(tasks, list):
        errors.append("tasks must be a list")
        tasks = []
    findings = review.get("findings")
    if not isinstance(findings, list):
        errors.append("findings must be a list")
        findings = []

    task_ids = set()
    for index, task in enumerate(tasks):
        prefix = f"tasks[{index}]"
        if not isinstance(task, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in ("id", "name", "quote"):
            if not isinstance(task.get(field), str):
                errors.append(f"{prefix}.{field} must be a string")
        task_id = task.get("id")
        if isinstance(task_id, str):
            if task_id in task_ids:
                errors.append(f"{prefix}.id must be unique")
            task_ids.add(task_id)
        if "owner" not in task:
            errors.append(f"{prefix}.owner is required")
        owner = task.get("owner")
        if owner is not None and not isinstance(owner, str):
            errors.append(f"{prefix}.owner must be a string or null")
        duration = task.get("duration_days")
        if type(duration) is not int or duration < 1:
            errors.append(f"{prefix}.duration_days must be a positive integer")
        dependencies = task.get("depends_on")
        if not isinstance(dependencies, list) or any(
            not isinstance(dependency, str) for dependency in dependencies
        ):
            errors.append(f"{prefix}.depends_on must be a list of ids")

    for index, task in enumerate(tasks):
        if not isinstance(task, dict):
            continue
        dependencies = task.get("depends_on")
        if isinstance(dependencies, list):
            for dependency in dependencies:
                if isinstance(dependency, str) and dependency not in task_ids:
                    errors.append(f"tasks[{index}] has unknown dependency {dependency}")

    normalized_plan = _normalized(plan_text)
    for index, finding in enumerate(findings):
        prefix = f"findings[{index}]"
        if not isinstance(finding, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in ("title", "detail"):
            if not isinstance(finding.get(field), str):
                errors.append(f"{prefix}.{field} must be a string")
        if "quote" not in finding:
            errors.append(f"{prefix}.quote is required")
            continue
        quote = finding["quote"]
        if quote is not None and not isinstance(quote, str):
            errors.append(f"{prefix}.quote must be a string or null")

    for collection_name, collection in (("tasks", tasks), ("findings", findings)):
        for index, item in enumerate(collection):
            if not isinstance(item, dict):
                continue
            quote = item.get("quote")
            if isinstance(quote, str) and _normalized(quote) not in normalized_plan:
                errors.append(f"{collection_name}[{index}].quote is not in the plan")

    if errors:
        raise ValueError("Invalid review response: " + "; ".join(errors))
    return review


def review_plan(text, client=None):
    client = client or OpenAI(
        api_key=os.environ["OPENROUTER_API_KEY"],
        base_url=os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
    )
    reply = client.chat.completions.create(
        model=os.environ.get("REVIEW_MODEL", DEFAULT_MODEL),
        max_tokens=16000,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "plan_review",
                "strict": True,
                "schema": REVIEW_SCHEMA,
            },
        },
        messages=[
            {
                "role": "system",
                "content": "Follow the JSON schema exactly. Do not use Markdown fences.",
            },
            {"role": "user", "content": PROMPT + "\n\n" + text},
        ],
    )
    return _validate_review(_parse_json(_get_content(reply)), text)


if __name__ == "__main__":
    plan_path, out_path = sys.argv[1], sys.argv[2]
    with open(plan_path, encoding="utf-8") as f:
        review = review_plan(f.read())
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(review, f, indent=2)
