"""Renderer-independent project, scene graph, dialogue and undo primitives.

The module deliberately has no renderer/UI dependencies. It is the data contract
shared by editor panels, runtime systems and persistence during the Python port.
"""
from __future__ import annotations

import json
import math
import os
import tempfile
import uuid
from pathlib import Path
from typing import Any


def _clone(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False, allow_nan=False))


def default_project() -> dict[str, Any]:
    return {
        "format": "game-engen-python-scene", "version": 1, "name": "Untitled Scene",
        "variables": {}, "journal": [], "objects": [], "assets": [],
    }


def validate_project(data: Any) -> dict[str, Any]:
    """Validate the persisted schema without dropping unknown extension fields."""
    if not isinstance(data, dict) or not isinstance(data.get("objects"), list):
        raise ValueError("Scene must be an object containing an 'objects' list.")
    if not isinstance(data.get("variables", {}), dict):
        raise ValueError("'variables' must be an object.")
    if not isinstance(data.get("journal", []), list):
        raise ValueError("'journal' must be a list.")
    if not isinstance(data.get("assets", []), list):
        raise ValueError("'assets' must be a list.")

    by_id: dict[str, dict[str, Any]] = {}
    for obj in data["objects"]:
        if not isinstance(obj, dict) or not isinstance(obj.get("id"), str) or not obj["id"]:
            raise ValueError("Every scene object must have a non-empty string id.")
        if obj["id"] in by_id:
            raise ValueError(f"Duplicate object id: {obj['id']}")
        by_id[obj["id"]] = obj
        for field in ("position", "rotation", "scale", "color"):
            values = obj.get(field)
            if not isinstance(values, list) or len(values) != 3:
                raise ValueError(f"Object {obj['id']} has invalid {field}.")
            if not all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in values):
                raise ValueError(f"Object {obj['id']} has non-numeric {field}.")
        if any(abs(float(v)) < 0.0001 for v in obj["scale"]):
            raise ValueError(f"Object {obj['id']} has a zero scale.")
        if "components" in obj:
            if not isinstance(obj["components"], list):
                raise ValueError(f"Object {obj['id']} components must be a list.")
            component_ids: set[str] = set()
            for component in obj["components"]:
                if not isinstance(component, dict) or not isinstance(component.get("type"), str) or not component["type"]:
                    raise ValueError(f"Object {obj['id']} has a component without a type.")
                cid = component.get("id")
                if cid is not None:
                    if not isinstance(cid, str) or not cid or cid in component_ids:
                        raise ValueError(f"Object {obj['id']} has an invalid or duplicate component id.")
                    component_ids.add(cid)

    # Validate optional hierarchy references and reject cycles before the editor
    # or serializer can accidentally create an infinite traversal.
    for obj in by_id.values():
        parent_id = obj.get("parent_id")
        if parent_id is not None and (not isinstance(parent_id, str) or not parent_id):
            raise ValueError(f"Object {obj['id']} has an invalid parent_id.")
        if parent_id is not None and parent_id not in by_id:
            raise ValueError(f"Object {obj['id']} references missing parent {parent_id}.")
        if parent_id == obj["id"]:
            raise ValueError(f"Object {obj['id']} cannot be its own parent.")
    for obj in by_id.values():
        visited: set[str] = set()
        current = obj
        while current.get("parent_id") is not None:
            parent_id = current["parent_id"]
            if parent_id in visited:
                raise ValueError(f"Parent cycle detected at object {parent_id}.")
            visited.add(parent_id)
            current = by_id[parent_id]

    data.setdefault("variables", {})
    data.setdefault("journal", [])
    data.setdefault("assets", [])
    data.setdefault("name", "Untitled Scene")
    data.setdefault("version", 1)
    data.setdefault("format", "game-engen-python-scene")
    return data


def atomic_save(path: str | Path, data: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(validate_project(_clone(data)), indent=2, ensure_ascii=False, allow_nan=False)
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
        return validate_project(json.load(stream, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"Invalid JSON number: {value}"))))


def dialogue_graph_issues(dialogue: Any) -> list[str]:
    """Return actionable graph errors: missing start node and broken choice links."""
    issues: list[str] = []
    if not isinstance(dialogue, dict):
        return ["Dialogue must be an object."]
    nodes = dialogue.get("nodes")
    if not isinstance(nodes, dict):
        return ["Dialogue 'nodes' must be an object keyed by node id."]
    start = dialogue.get("start")
    if not isinstance(start, str) or start not in nodes:
        issues.append(f"Dialogue start node {start!r} does not exist.")
    for node_id, node in nodes.items():
        if not isinstance(node, dict):
            issues.append(f"Node {node_id!r} must be an object.")
            continue
        choices = node.get("choices", [])
        if not isinstance(choices, list):
            issues.append(f"Node {node_id!r} choices must be a list.")
            continue
        for index, choice in enumerate(choices):
            if not isinstance(choice, dict):
                issues.append(f"Node {node_id!r} choice {index} must be an object.")
                continue
            target = choice.get("next")
            if target not in (None, "") and (not isinstance(target, str) or target not in nodes):
                issues.append(f"Node {node_id!r} choice {index} links to missing node {target!r}.")
    return issues


def apply_choice(project: dict[str, Any], node: dict[str, Any], choice: dict[str, Any]) -> str | None:
    """Apply a dialogue choice's variable effects and journal entry."""
    effects = choice.get("effects", {})
    if not isinstance(effects, dict):
        raise ValueError("Dialogue choice effects must be an object.")
    project.setdefault("variables", {}).update(effects)
    journal_entry = node.get("journal") or choice.get("journal")
    if journal_entry:
        journal = project.setdefault("journal", [])
        if journal_entry not in journal:
            journal.append(journal_entry)
    return choice.get("next")


def resolve_asset_reference(project_root: str | Path, reference: str) -> tuple[Path, bool]:
    """Resolve a project-relative asset and report missing files without raising.

    Absolute paths and paths escaping the project root are rejected to keep
    projects portable and avoid accidentally reading arbitrary local files.
    """
    if not isinstance(reference, str) or not reference.strip():
        raise ValueError("Asset reference must be a non-empty relative path.")
    root = Path(project_root).resolve()
    ref = Path(reference)
    if ref.is_absolute():
        raise ValueError("Asset references must be project-relative.")
    resolved = (root / ref).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError("Asset reference escapes the project directory.") from exc
    return resolved, resolved.is_file()


def aabb_intersects(a_min, a_max, b_min, b_max) -> bool:
    return all(a_min[i] <= b_max[i] and a_max[i] >= b_min[i] for i in range(3))


class SceneDocument:
    """Single authoritative, JSON-compatible scene model for editor subsystems."""
    def __init__(self, data: dict[str, Any] | None = None):
        self.data = validate_project(_clone(data if data is not None else default_project()))

    @property
    def objects(self) -> list[dict[str, Any]]:
        return self.data["objects"]

    def object(self, object_id: str) -> dict[str, Any]:
        for obj in self.objects:
            if obj["id"] == object_id:
                return obj
        raise KeyError(f"Unknown scene object: {object_id}")

    def create_object(self, name: str = "Object", object_type: str = "box", **fields: Any) -> dict[str, Any]:
        obj = {
            "id": str(uuid.uuid4()), "name": name, "type": object_type,
            "position": [0.0, 0.0, 0.0], "rotation": [0.0, 0.0, 0.0],
            "scale": [1.0, 1.0, 1.0], "color": [0.65, 0.68, 0.72],
            "components": [],
        }
        obj.update(_clone(fields))
        before = len(self.objects)
        self.objects.append(obj)
        try:
            validate_project(self.data)
        except Exception:
            del self.objects[before:]
            raise
        return obj

    def set_transform(self, object_id: str, *, position=None, rotation=None, scale=None) -> None:
        obj = self.object(object_id)
        before = _clone(obj)
        for key, value in (("position", position), ("rotation", rotation), ("scale", scale)):
            if value is not None:
                obj[key] = list(value)
        try:
            validate_project(self.data)
        except Exception:
            obj.clear()
            obj.update(before)
            raise

    def reparent(self, object_id: str, parent_id: str | None) -> None:
        obj = self.object(object_id)
        if parent_id is not None:
            self.object(parent_id)
        previous = obj.get("parent_id")
        if parent_id is None:
            obj.pop("parent_id", None)
        else:
            obj["parent_id"] = parent_id
        try:
            validate_project(self.data)
        except Exception:
            if previous is None:
                obj.pop("parent_id", None)
            else:
                obj["parent_id"] = previous
            raise

    def duplicate(self, object_id: str) -> dict[str, Any]:
        source = self.object(object_id)
        duplicate = _clone(source)
        duplicate["id"] = str(uuid.uuid4())
        duplicate["name"] = f"{source.get('name', 'Object')} Copy"
        duplicate["position"] = [float(v) + (0.5 if i == 0 else 0.0) for i, v in enumerate(source["position"])]
        # Components are owned by their entity; never duplicate component IDs.
        for component in duplicate.get("components", []):
            component["id"] = str(uuid.uuid4())
        self.objects.append(duplicate)
        try:
            validate_project(self.data)
        except Exception:
            self.objects.remove(duplicate)
            raise
        return duplicate

    def delete(self, object_id: str) -> list[str]:
        self.object(object_id)
        to_delete = {object_id}
        changed = True
        while changed:
            changed = False
            for obj in self.objects:
                if obj.get("parent_id") in to_delete and obj["id"] not in to_delete:
                    to_delete.add(obj["id"])
                    changed = True
        self.data["objects"] = [obj for obj in self.objects if obj["id"] not in to_delete]
        return list(to_delete)


class UndoHistory:
    """Bounded undo/redo history for JSON-compatible project state snapshots."""
    def __init__(self, limit: int = 100):
        self.limit = max(1, int(limit))
        self.undo_stack: list[dict[str, Any]] = []
        self.redo_stack: list[dict[str, Any]] = []

    @staticmethod
    def clone(value):
        return _clone(value)

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
