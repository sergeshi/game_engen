import json
import tempfile
import unittest
from pathlib import Path

from python_prototype.engine.core import (
    SceneDocument, UndoHistory, aabb_intersects, apply_choice, atomic_save,
    default_project, dialogue_graph_issues, load_project, resolve_asset_reference,
    validate_project,
)


class ProjectTests(unittest.TestCase):
    def sample(self):
        return {
            "format": "game-engen-python-scene", "version": 1,
            "name": "Test", "variables": {}, "journal": [],
            "objects": [{
                "id": "box", "name": "Box", "type": "box",
                "position": [0, 0, 0], "rotation": [0, 0, 0],
                "scale": [1, 1, 1], "color": [0.5, 0.5, 0.5],
                "components": [{"id": "mesh-1", "type": "MeshRenderer", "material": "mat-1"}],
            }],
        }

    def test_round_trip_preserves_components_and_unknown_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scene.json"
            project = self.sample()
            project["objects"][0]["custom_extension"] = {"authoring": "kept"}
            atomic_save(path, project)
            loaded = load_project(path)
            self.assertEqual(loaded["objects"][0]["id"], "box")
            self.assertEqual(loaded["objects"][0]["components"][0]["material"], "mat-1")
            self.assertEqual(loaded["objects"][0]["custom_extension"], {"authoring": "kept"})

    def test_duplicate_ids_rejected(self):
        project = self.sample()
        project["objects"].append(dict(project["objects"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate object id"):
            validate_project(project)

    def test_zero_scale_rejected(self):
        project = self.sample()
        project["objects"][0]["scale"] = [1, 0, 1]
        with self.assertRaisesRegex(ValueError, "zero scale"):
            validate_project(project)

    def test_missing_parent_rejected(self):
        project = self.sample()
        project["objects"][0]["parent_id"] = "missing"
        with self.assertRaisesRegex(ValueError, "missing parent"):
            validate_project(project)

    def test_parent_cycle_rejected(self):
        project = self.sample()
        child = dict(project["objects"][0], id="child", parent_id="box")
        project["objects"][0]["parent_id"] = "child"
        project["objects"].append(child)
        with self.assertRaisesRegex(ValueError, "Parent cycle"):
            validate_project(project)

    def test_dialogue_effects_and_journal(self):
        project = self.sample()
        next_node = apply_choice(project, {"journal": "Find the key"}, {
            "next": "done", "effects": {"quest_started": True, "trust": 2}
        })
        self.assertEqual(next_node, "done")
        self.assertTrue(project["variables"]["quest_started"])
        self.assertEqual(project["variables"]["trust"], 2)
        self.assertEqual(project["journal"], ["Find the key"])
        apply_choice(project, {"journal": "Find the key"}, {"effects": {}})
        self.assertEqual(project["journal"], ["Find the key"])

    def test_dialogue_graph_reports_broken_links(self):
        issues = dialogue_graph_issues({
            "start": "intro",
            "nodes": {"intro": {"choices": [{"text": "Go", "next": "absent"}]}},
        })
        self.assertEqual(len(issues), 1)
        self.assertIn("missing node", issues[0])

    def test_dialogue_graph_requires_existing_start(self):
        issues = dialogue_graph_issues({"start": "absent", "nodes": {"intro": {"choices": []}}})
        self.assertTrue(any("start node" in issue for issue in issues))

    def test_scene_document_transform_duplicate_and_delete(self):
        scene = SceneDocument(self.sample())
        scene.set_transform("box", position=[2, 0, 0])
        self.assertEqual(scene.object("box")["position"], [2, 0, 0])
        duplicate = scene.duplicate("box")
        self.assertNotEqual(duplicate["id"], "box")
        self.assertNotEqual(duplicate["components"][0]["id"], "mesh-1")
        self.assertEqual(duplicate["position"], [2.5, 0, 0])
        self.assertEqual(scene.delete("box"), ["box"])
        self.assertEqual([o["id"] for o in scene.objects], [duplicate["id"]])

    def test_reparent_rejects_cycles_and_rolls_back(self):
        project = self.sample()
        project["objects"].append({
            "id": "child", "name": "Child", "type": "box",
            "position": [0, 0, 0], "rotation": [0, 0, 0],
            "scale": [1, 1, 1], "color": [1, 1, 1], "parent_id": "box",
        })
        scene = SceneDocument(project)
        with self.assertRaisesRegex(ValueError, "Parent cycle"):
            scene.reparent("box", "child")
        self.assertNotIn("parent_id", scene.object("box"))

    def test_asset_reference_and_path_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "textures").mkdir()
            (root / "textures" / "stone.png").write_bytes(b"asset")
            resolved, exists = resolve_asset_reference(root, "textures/stone.png")
            self.assertTrue(exists)
            self.assertEqual(resolved.name, "stone.png")
            _, missing = resolve_asset_reference(root, "models/missing.glb")
            self.assertFalse(missing)
            with self.assertRaisesRegex(ValueError, "escapes"):
                resolve_asset_reference(root, "../outside.txt")

    def test_undo_redo(self):
        history = UndoHistory(limit=3)
        state = {"value": 1}
        history.record(state)
        changed = {"value": 2}
        undone = history.undo(changed)
        self.assertEqual(undone, {"value": 1})
        redone = history.redo(undone)
        self.assertEqual(redone, {"value": 2})

    def test_aabb(self):
        self.assertTrue(aabb_intersects((0, 0, 0), (1, 1, 1), (0.5, 0.5, 0.5), (2, 2, 2)))
        self.assertFalse(aabb_intersects((0, 0, 0), (1, 1, 1), (2, 2, 2), (3, 3, 3)))


if __name__ == "__main__":
    unittest.main()
