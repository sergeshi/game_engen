import json
import tempfile
import unittest
from pathlib import Path

from engine.core import (
    UndoHistory, aabb_intersects, apply_choice, atomic_save,
    default_project, load_project, validate_project,
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
            }],
        }

    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scene.json"
            project = self.sample()
            atomic_save(path, project)
            self.assertEqual(load_project(path)["objects"][0]["id"], "box")

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

    def test_dialogue_effects_and_journal(self):
        project = self.sample()
        node = {"journal": "Find the key"}
        next_node = apply_choice(project, node, {
            "next": "done", "effects": {"quest_started": True, "trust": 2}
        })
        self.assertEqual(next_node, "done")
        self.assertTrue(project["variables"]["quest_started"])
        self.assertEqual(project["variables"]["trust"], 2)
        self.assertEqual(project["journal"], ["Find the key"])

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
