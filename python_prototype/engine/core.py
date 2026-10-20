"""Renderer-independent project, dialogue, and undo primitives."""
from __future__ import annotations

import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any


def default_project() -> dict[str, Any]:
    return {
        "format": "game-engen-python-scene", "version": 1, "name": "Untitled Scene",
        "variables": {}, "journal": [], "objects": [],
    }


def validate_project(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict) or not isinstance(data.get("objects"), list):
        raise ValueError("Scene must be an object containing an 'objects' list.")
    seen: set[str] = set()
    for obj in data["objects"]:
        if not isinstance(obj, dict) or not isinstance(obj.get("id"), str) or not obj["id"]:
            raise ValueError("Every scene object must have a non-empty string id.")
        if obj["id"] in seen:
            raise ValueError(f"Duplicate object id: {obj['id']}")
        seen.add(obj["id"])
        for field in ("position", "rotation", "scale", "color"):
            values = obj.get(field)
            if not isinstance(values, list) or len(values) != 3:
                raise ValueError(f"Object {obj['id']} has invalid {field}.")
            if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in values):
                raise ValueError(f"Object {obj['id']} has non-numeric {field}.")
        if any(abs(float(v)) < 0.0001 for v in obj["scale"]):
            raise ValueError(f"Object {obj['id']} has a zero scale.")
    data.setdefault("variables", {})
    data.setdefault("journal", [])
    data.setdefault("name", "Untitled Scene")
    data.setdefault("version", 1)
    data.setdefault("format", "game-engen-python-scene")
    return data


def atomic_save(path: str | Path, data: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(validate_project(json.loads(json.dumps(data))), indent=2, ensure_ascii=False)
    fd, tmp_name = tempfile.mkstemp(prefix=target.name, suffix=".tmp", dir=str(target.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp_name, target)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def load_project(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as stream:
        return validate_project(json.load(stream))


def apply_choice(project: dict[str, Any], node: dict[str, Any], choice: dict[str, Any]) -> str | None:
    """Apply dialogue effects and journal entry; return next node id if any."""
    project.setdefault("variables", {}).update(choice.get("effects", {}))
    return choice.get("next")


def aabb_intersects(a_min, a_max, b_min, b_max) -> bool:
    return all(a_min[i] <= b_max[i] and a_max[i] >= b_min[i] for i in range(3))


class UndoHistory:
    """Bounded undo/redo history for JSON-compatible project state."""
    def __init__(self, limit: int = 100):
        self.limit = max(1, int(limit))
        self.undo_stack: list[dict[str, Any]] = []
        self.redo_stack: list[dict[str, Any]] = []

    @staticmethod
    def clone(value):
        return json.loads(json.dumps(value))

    def record(self, state):
        self.undo_stack.append(self.clone(state))
        del self.undo_stack[:-self.limit]
        self.redo_stack.clear()

    def undo(self, current):
        if not self.undo_stack:
            return None
        self.redo_stack.append(self.clone(current))
        return self.undo_stack.pop()

    def redo(self, current):
        if not self.redo_stack:
            return None
        self.undo_stack.append(self.clone(current))
        return self.redo_stack.pop()
