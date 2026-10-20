"""Lightweight Python scene editor/runtime prototype for GAME ENGEN."""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

from panda3d.core import (
    AmbientLight, BitMask32, CollisionHandlerQueue, CollisionNode,
    CollisionRay, CollisionTraverser, DirectionalLight, LineSegs,
    Point3, Vec3, KeyboardButton, loadPrcFileData,
)
from direct.gui.DirectGui import DirectButton, DirectFrame, DirectLabel
from direct.showbase.ShowBase import ShowBase
from engine.core import atomic_save, load_project, validate_project, apply_choice, UndoHistory

APP_DIR = Path(__file__).resolve().parent
DEFAULT_SCENE = APP_DIR / "scenes" / "sample_scene.json"


def default_project() -> dict[str, Any]:
    return {
        "format": "game-engen-python-scene",
        "version": 1,
        "name": "Untitled Scene",
        "variables": {"quest_started": False, "trust": 0},
        "journal": [],
        "objects": [
            {"id": "floor", "name": "Ground", "type": "floor", "position": [0, 0, -0.15],
             "rotation": [0, 0, 0], "scale": [18, 18, 0.2], "color": [0.16, 0.19, 0.22], "solid": False},
            {"id": "crate_a", "name": "Crate A", "type": "box", "position": [-2, 1, 0.6],
             "rotation": [0, 0, 0], "scale": [1.2, 1.2, 1.2], "color": [0.75, 0.31, 0.18], "solid": True},
            {"id": "crate_b", "name": "Crate B", "type": "box", "position": [1.5, 2.5, 0.6],
             "rotation": [0, 0, 18], "scale": [1.2, 1.2, 1.2], "color": [0.18, 0.48, 0.75], "solid": True},
            {"id": "npc_guide", "name": "Guide NPC", "type": "npc", "position": [2, -1, 0.9],
             "rotation": [0, 0, 0], "scale": [0.8, 0.8, 1.8], "color": [0.92, 0.72, 0.25], "solid": True,
             "dialogue": {"start": "hello", "nodes": {
                 "hello": {"speaker": "Guide", "text": "The old road is blocked. Can you help me move the crates?",
                           "choices": [{"text": "I'll help.", "next": "thanks", "effects": {"quest_started": True, "trust": 1}},
                                       {"text": "Not now.", "next": "later", "effects": {}}]},
                 "thanks": {"speaker": "Guide", "text": "Thank you. I've added the task to your journal.", "choices": [],
                            "journal": "Help the guide clear the old road."},
                 "later": {"speaker": "Guide", "text": "Come back if you change your mind.", "choices": []}
             }}},
            {"id": "wall", "name": "Test Wall", "type": "box", "position": [-4, 2, 1],
             "rotation": [0, 0, 0], "scale": [0.35, 4, 2], "color": [0.32, 0.36, 0.41], "solid": True},
        ],
    }


class EngineApp(ShowBase):
    def __init__(self, renderer: str = "opengl", scene_path: str | Path | None = None):
        self.renderer_name = renderer
        if renderer == "vulkan":
            loadPrcFileData("game-engen", "load-display p3vulkandisplay")
        else:
            loadPrcFileData("game-engen", "load-display pandagl")
        loadPrcFileData("game-engen", "window-title GAME ENGEN — Python Prototype")
        loadPrcFileData("game-engen", "win-size 1440 900")
        loadPrcFileData("game-engen", "sync-video true")
        loadPrcFileData("game-engen", "frame-rate-meter false")
        super().__init__()
        self.disableMouse()
        self.setBackgroundColor(0.055, 0.067, 0.085, 1)
        self.scene_path = Path(scene_path) if scene_path else DEFAULT_SCENE
        self.project = load_project(self.scene_path) if self.scene_path.exists() else default_project()
        self.selected_id: str | None = None
        self.nodes: dict[str, Any] = {}
        self.history = UndoHistory(limit=100)
        self.play_mode = False
        self.dialogue_state: dict[str, Any] | None = None
        self.camera_heading = 0.0
        self.camera_pitch = -22.0
        self.camera_distance = 21.0
        self.dragging_camera = False
        self.last_mouse = None
        self.move_mode = "move"
        self.status_text = "Ready"
        self._setup_lighting()
        self._build_grid()
        self._build_picker()
        self._build_ui()
        self._rebuild_scene()
        self._update_camera()
        self.accept("mouse1", self.pick_object)
        self.accept("mouse3", self.begin_camera_drag)
        self.accept("mouse3-up", self.end_camera_drag)
        self.accept("wheel_up", self.zoom, [-1])
        self.accept("wheel_down", self.zoom, [1])
        self.accept("escape", self.close_dialogue_or_quit)
        self.accept("g", self.set_mode, ["move"])
        self.accept("r", self.set_mode, ["rotate"])
        self.accept("s", self.set_mode, ["scale"])
        self.accept("arrow_left", self.transform, [-1, 0, 0])
        self.accept("arrow_right", self.transform, [1, 0, 0])
        self.accept("arrow_up", self.transform, [0, 1, 0])
        self.accept("arrow_down", self.transform, [0, -1, 0])
        self.accept("page_up", self.transform, [0, 0, 1])
        self.accept("page_down", self.transform, [0, 0, -1])
        self.accept("control-s", self.save_scene)
        self.accept("control-o", self.open_scene)
        self.accept("control-z", self.undo)
        self.accept("control-y", self.redo)
        self.accept("control-d", self.duplicate_selected)
        self.accept("delete", self.delete_selected)
        self.accept("f5", self.toggle_play)
        self.accept("e", self.interact)
        self.accept("1", self.add_box)
        self.accept("2", self.add_npc)
        self.accept("f", self.focus_selected)
        self.accept("enter", self.dialogue_continue)
        self.taskMgr.add(self._tick, "game-engen-tick")
        self._refresh_hierarchy()

    def _setup_lighting(self):
        ambient = AmbientLight("ambient")
        ambient.setColor((0.42, 0.45, 0.52, 1))
        self.render.setLight(self.render.attachNewNode(ambient))
        sun = DirectionalLight("sun")
        sun.setColor((0.95, 0.9, 0.8, 1))
        sun_np = self.render.attachNewNode(sun)
        sun_np.setHpr(-35, -55, 0)
        self.render.setLight(sun_np)

    def _build_grid(self):
        lines = LineSegs("editor-grid")
        lines.setThickness(1)
        lines.setColor(0.20, 0.24, 0.29, 1)
        for i in range(-20, 21):
            lines.moveTo(i, -20, -0.02); lines.drawTo(i, 20, -0.02)
            lines.moveTo(-20, i, -0.02); lines.drawTo(20, i, -0.02)
        grid = self.render.attachNewNode(lines.create())
        grid.setLightOff(1)
        grid.setDepthWrite(False)

    def _build_picker(self):
        self.picker = CollisionTraverser("editor-picker")
        self.picker_queue = CollisionHandlerQueue()
        ray_node = CollisionNode("mouse-ray")
        ray_node.setFromCollideMask(BitMask32.bit(1))
        ray_node.setIntoCollideMask(BitMask32.allOff())
        self.picker_ray = CollisionRay()
        ray_node.addSolid(self.picker_ray)
        self.picker_np = self.camera.attachNewNode(ray_node)
        self.picker.addCollider(self.picker_np, self.picker_queue)

    def _build_ui(self):
        self.left_panel = DirectFrame(frameColor=(0.055, 0.07, 0.09, 0.96),
                                      frameSize=(-1.32, -0.72, -0.96, 0.96),
                                      pos=(-0.34, 0, 0))
        DirectLabel(parent=self.left_panel, text="GAME ENGEN", text_align=0,
                    text_fg=(0.94, 0.96, 1, 1), scale=0.055, pos=(-0.55, 0, 0.87),
                    frameColor=(0, 0, 0, 0))
        DirectLabel(parent=self.left_panel, text="SCENE HIERARCHY", text_align=0,
                    text_fg=(0.55, 0.75, 0.92, 1), scale=0.035, pos=(-0.55, 0, 0.76),
                    frameColor=(0, 0, 0, 0))
        self.hierarchy_labels = []
        self.inspector_label = DirectLabel(parent=self.left_panel, text="No selection",
            text_align=0, text_fg=(0.84, 0.87, 0.92, 1), scale=0.031,
            pos=(-0.55, 0, -0.35), frameColor=(0, 0, 0, 0), text_wordwrap=17)
        self.status_label = DirectLabel(text="Ready", text_align=0,
            text_fg=(0.82, 0.86, 0.91, 1), scale=0.035, pos=(-1.28, 0, -0.94),
            frameColor=(0.04, 0.05, 0.07, 0.95), frameSize=(-0.04, 2.6, -0.05, 0.06))
        self.help_label = DirectLabel(text="LMB select | RMB orbit | WASD move | G/R/S transform | F5 play",
            text_align=1, text_fg=(0.72, 0.77, 0.85, 1), scale=0.032,
            pos=(0.35, 0, -0.94), frameColor=(0.04, 0.05, 0.07, 0.95),
            frameSize=(-1.15, 1.15, -0.05, 0.06))
        self.dialogue_frame = DirectFrame(frameColor=(0.045, 0.055, 0.075, 0.97),
            frameSize=(-0.85, 0.85, -0.72, 0.72), pos=(0.1, 0, -0.05))
        self.dialogue_title = DirectLabel(parent=self.dialogue_frame, text="",
            text_fg=(0.95, 0.76, 0.32, 1), scale=0.05, pos=(0, 0, 0.56),
            frameColor=(0, 0, 0, 0))
        self.dialogue_body = DirectLabel(parent=self.dialogue_frame, text="",
            text_fg=(0.92, 0.93, 0.96, 1), scale=0.04, pos=(-0.72, 0, 0.28),
            text_align=0, text_wordwrap=34, frameColor=(0, 0, 0, 0))
        self.dialogue_buttons = []
        self.dialogue_frame.hide()

    def _refresh_hierarchy(self):
        for widget in self.hierarchy_labels:
            widget.destroy()
        self.hierarchy_labels = []
        for index, obj in enumerate(self.project["objects"][:13]):
            prefix = "▶ " if obj["id"] == self.selected_id else "   "
            button = DirectButton(parent=self.left_panel,
                text=prefix + obj.get("name", obj["id"]), text_align=0,
                text_fg=(1, 0.8, 0.32, 1) if obj["id"] == self.selected_id else (0.8, 0.84, 0.9, 1),
                text_scale=0.032, frameColor=(0.12, 0.15, 0.19, 0.7) if obj["id"] == self.selected_id else (0, 0, 0, 0),
                frameSize=(-0.56, 0.56, -0.026, 0.026), relief=0,
                pos=(-0.95, 0, 0.67 - index * 0.065),
                command=self.select_id, extraArgs=[obj["id"]])
            self.hierarchy_labels.append(button)
        self._refresh_inspector()

    def _refresh_inspector(self):
        obj = self._selected_object()
        if not obj:
            self.inspector_label["text"] = "No selection\n\n1: Add box\n2: Add NPC\nCtrl+S: Save"
            return
        p, r, s = obj["position"], obj["rotation"], obj["scale"]
        self.inspector_label["text"] = (
            f"INSPECTOR\n{obj.get('name', obj['id'])}\nType: {obj.get('type', 'box')}\n\n"
            f"Position\nX {p[0]:.2f}  Y {p[1]:.2f}  Z {p[2]:.2f}\n"
            f"Rotation\nX {r[0]:.1f}  Y {r[1]:.1f}  Z {r[2]:.1f}\n"
            f"Scale\nX {s[0]:.2f}  Y {s[1]:.2f}  Z {s[2]:.2f}\n\n"
            f"Mode: {self.move_mode.upper()}\nArrow keys / PgUp/PgDn to edit\n"
            "Shift is simulated with larger steps\n\nCtrl+D duplicate\nDelete remove\nF focus"
        )

    def _selected_object(self):
        return next((o for o in self.project["objects"] if o["id"] == self.selected_id), None)

    def _rebuild_scene(self):
        for node in self.nodes.values():
            node.removeNode()
        self.nodes.clear()
        for obj in self.project["objects"]:
            self._create_object_node(obj)
        self._refresh_hierarchy()

    def _create_object_node(self, obj):
        kind = obj.get("type", "box")
        if kind == "floor":
            model = self.loader.loadModel("models/box")
        elif kind == "npc":
            model = self.loader.loadModel("models/misc/rgbCube")
        else:
            model = self.loader.loadModel("models/box")
        model.reparentTo(self.render)
        model.setName(obj["id"])
        model.setPos(*obj["position"])
        model.setHpr(*obj["rotation"])
        model.setScale(*obj["scale"])
        color = obj.get("color", [0.6, 0.6, 0.65])
        model.setColor(float(color[0]), float(color[1]), float(color[2]), 1)
        model.setTag("object-id", obj["id"])
        if obj["id"] == self.selected_id:
            model.setColorScale(1.25, 1.18, 0.65, 1)
        self.nodes[obj["id"]] = model
        if obj.get("solid", True) and kind != "floor":
            cnode = CollisionNode("pick-" + obj["id"])
            cnode.setFromCollideMask(BitMask32.allOff())
            cnode.setIntoCollideMask(BitMask32.bit(1))
            cnode.addSolid(__import__("panda3d.core", fromlist=["CollisionSphere"]).CollisionSphere(0, 0, 0, 0.85))
            cnp = model.attachNewNode(cnode)
            cnp.setTag("object-id", obj["id"])

    def select_id(self, object_id):
        self.selected_id = object_id
        self._rebuild_scene()
        self._set_status(f"Selected: {object_id}")

    def pick_object(self):
        if self.dialogue_state or self.play_mode or not self.mouseWatcherNode.hasMouse():
            return
        mouse = self.mouseWatcherNode.getMouse()
        self.picker_ray.setFromLens(self.camNode, mouse.x, mouse.y)
        self.picker_queue.clearEntries()
        self.picker.traverse(self.render)
        self.picker_queue.sortEntries()
        if self.picker_queue.getNumEntries():
            for entry in self.picker_queue.getEntries():
                into = entry.getIntoNodePath()
                if into.hasTag("object-id"):
                    self.select_id(into.getTag("object-id"))
                    return
                parent = into.getParent()
                if parent.hasTag("object-id"):
                    self.select_id(parent.getTag("object-id"))
                    return
        self.selected_id = None
        self._rebuild_scene()

    def _snapshot(self):
        return json.loads(json.dumps(self.project))

    def _commit_edit(self):
        self.history.record(self.project)

    def transform(self, dx, dy, dz):
        obj = self._selected_object()
        if not obj or self.play_mode:
            return
        self._commit_edit()
        amount = 0.5 if self.mouseWatcherNode.isButtonDown(KeyboardButton.shift()) else 0.2
        if self.move_mode == "move":
            for i, delta in enumerate((dx, dy, dz)):
                obj["position"][i] += delta * amount
        elif self.move_mode == "rotate":
            for i, delta in enumerate((dx, dy, dz)):
                obj["rotation"][i] += delta * 5
        else:
            for i, delta in enumerate((dx, dy, dz)):
                if delta:
                    obj["scale"][i] = max(0.1, obj["scale"][i] + delta * amount)
        self._rebuild_scene()

    def set_mode(self, mode):
        self.move_mode = mode
        self._refresh_inspector()
        self._set_status(f"{mode.title()} mode")

    def add_box(self):
        self._add_object("box", "Box", [0.45, 0.53, 0.64])

    def add_npc(self):
        self._add_object("npc", "NPC", [0.95, 0.7, 0.25])

    def _add_object(self, kind, name, color):
        self._commit_edit()
        base_id = kind
        suffix = 1
        ids = {o["id"] for o in self.project["objects"]}
        while f"{base_id}_{suffix}" in ids:
            suffix += 1
        obj = {"id": f"{base_id}_{suffix}", "name": f"{name} {suffix}", "type": kind,
               "position": [0, 0, 0.8], "rotation": [0, 0, 0],
               "scale": [1, 1, 1.6] if kind == "npc" else [1, 1, 1],
               "color": color, "solid": True}
        if kind == "npc":
            obj["dialogue"] = {"start": "start", "nodes": {"start": {
                "speaker": obj["name"], "text": "Hello, traveler.", "choices": [
                    {"text": "Goodbye.", "next": None, "effects": {}}]}}}
        self.project["objects"].append(obj)
        self.selected_id = obj["id"]
        self._rebuild_scene()
        self._set_status(f"Created {obj['name']}")

    def duplicate_selected(self):
        obj = self._selected_object()
        if not obj or self.play_mode:
            return
        self._commit_edit()
        clone = json.loads(json.dumps(obj))
        clone["id"] = obj["id"] + "_copy"
        index = 2
        existing = {o["id"] for o in self.project["objects"]}
        while clone["id"] in existing:
            clone["id"] = obj["id"] + f"_copy{index}"
            index += 1
        clone["name"] = obj.get("name", obj["id"]) + " Copy"
        clone["position"][0] += 0.6
        self.project["objects"].append(clone)
        self.selected_id = clone["id"]
        self._rebuild_scene()

    def delete_selected(self):
        if not self.selected_id or self.play_mode:
            return
        self._commit_edit()
        self.project["objects"] = [o for o in self.project["objects"] if o["id"] != self.selected_id]
        self.selected_id = None
        self._rebuild_scene()
        self._set_status("Object deleted")

    def undo(self):
        restored = self.history.undo(self.project)
        if restored is None:
            self._set_status("Nothing to undo"); return
        self.project = restored
        self.selected_id = None
        self._rebuild_scene()
        self._set_status("Undo")

    def redo(self):
        restored = self.history.redo(self.project)
        if restored is None:
            self._set_status("Nothing to redo"); return
        self.project = restored
        self.selected_id = None
        self._rebuild_scene()
        self._set_status("Redo")

    def save_scene(self):
        try:
            atomic_save(self.scene_path, self.project)
            self._set_status(f"Saved {self.scene_path}")
        except Exception as exc:
            self._set_status(f"Save failed: {exc}")

    def open_scene(self):
        try:
            self.project = load_project(self.scene_path)
            self.selected_id = None
            self.history = UndoHistory(limit=100)
            self._rebuild_scene()
            self._set_status(f"Loaded {self.scene_path}")
        except Exception as exc:
            self._set_status(f"Load failed: {exc}")

    def toggle_play(self):
        self.play_mode = not self.play_mode
        self.selected_id = None if self.play_mode else self.selected_id
        self._refresh_hierarchy()
        self._set_status("PLAY mode — E near NPC to interact" if self.play_mode else "Editor mode")

    def interact(self):
        if not self.play_mode or self.dialogue_state:
            return
        player_pos = self.camera.getPos(self.render)
        candidates = []
        for obj in self.project["objects"]:
            if obj.get("type") == "npc":
                pos = Point3(*obj["position"])
                distance = (pos - player_pos).length()
                if distance < 8:
                    candidates.append((distance, obj))
        if not candidates:
            self._set_status("No NPC nearby"); return
        _, npc = min(candidates, key=lambda pair: pair[0])
        self._start_dialogue(npc)

    def _start_dialogue(self, npc):
        dialogue = npc.get("dialogue", {})
        nodes = dialogue.get("nodes", {})
        start = dialogue.get("start")
        if start not in nodes:
            self._set_status("NPC dialogue is missing a valid start node"); return
        self.dialogue_state = {"npc": npc, "nodes": nodes, "node": start}
        self._show_dialogue_node()

    def _show_dialogue_node(self):
        for button in self.dialogue_buttons:
            button.destroy()
        self.dialogue_buttons = []
        node = self.dialogue_state["nodes"][self.dialogue_state["node"]]
        self.dialogue_title["text"] = node.get("speaker", self.dialogue_state["npc"].get("name", "NPC"))
        self.dialogue_body["text"] = node.get("text", "")
        self.dialogue_frame.show()
        choices = node.get("choices", [])
        if not choices:
            self.dialogue_buttons.append(DirectButton(parent=self.dialogue_frame, text="Close",
                text_scale=0.04, frameColor=(0.2, 0.27, 0.36, 1), pos=(0, 0, -0.5),
                command=self._end_dialogue))
        else:
            for i, choice in enumerate(choices[:4]):
                self.dialogue_buttons.append(DirectButton(parent=self.dialogue_frame,
                    text=f"{i + 1}. {choice.get('text', 'Continue')}", text_scale=0.035,
                    text_align=0, frameColor=(0.14, 0.19, 0.26, 1),
                    frameSize=(-0.7, 0.7, -0.045, 0.045), pos=(0, 0, -0.38 - i * 0.11),
                    command=self._choose_dialogue, extraArgs=[choice]))
        self._set_status("Dialogue — choose a response")

    def _choose_dialogue(self, choice):
        node = self.dialogue_state["nodes"][self.dialogue_state["node"]]
        next_node = apply_choice(self.project, node, choice)
        if next_node and next_node in self.dialogue_state["nodes"]:
            self.dialogue_state["node"] = next_node
            self._show_dialogue_node()
        else:
            self._end_dialogue()

    def dialogue_continue(self):
        if not self.dialogue_state:
            return
        node = self.dialogue_state["nodes"][self.dialogue_state["node"]]
        choices = node.get("choices", [])
        if choices:
            self._choose_dialogue(choices[0])
        else:
            self._end_dialogue()

    def _end_dialogue(self):
        self.dialogue_frame.hide()
        self.dialogue_state = None
        self._set_status("Dialogue closed")

    def close_dialogue_or_quit(self):
        if self.dialogue_state:
            self._end_dialogue()
        else:
            self.userExit()

    def begin_camera_drag(self):
        self.dragging_camera = True
        self.last_mouse = None

    def end_camera_drag(self):
        self.dragging_camera = False
        self.last_mouse = None

    def zoom(self, direction):
        self.camera_distance = max(5, min(55, self.camera_distance + direction * 1.5))
        self._update_camera()

    def _update_camera(self):
        target = Point3(0, 0, 0)
        heading = math.radians(self.camera_heading)
        pitch = math.radians(self.camera_pitch)
        horizontal = self.camera_distance * math.cos(pitch)
        pos = Point3(target.x + math.sin(heading) * horizontal,
                     target.y - math.cos(heading) * horizontal,
                     target.z - self.camera_distance * math.sin(pitch))
        self.camera.setPos(pos)
        self.camera.lookAt(target)

    def focus_selected(self):
        obj = self._selected_object()
        if obj:
            self.camera.setPos(obj["position"][0] + 10, obj["position"][1] - 13, obj["position"][2] + 9)
            self.camera.lookAt(*obj["position"])

    def _tick(self, task):
        dt = min(globalClock.getDt(), 0.05)
        if self.dragging_camera and self.mouseWatcherNode.hasMouse():
            mouse = self.mouseWatcherNode.getMouse()
            if self.last_mouse is not None:
                self.camera_heading -= (mouse.x - self.last_mouse[0]) * 150
                self.camera_pitch = max(-75, min(-5, self.camera_pitch + (mouse.y - self.last_mouse[1]) * 100))
                self._update_camera()
            self.last_mouse = (mouse.x, mouse.y)
        if self.play_mode and not self.dialogue_state:
            speed = 7 * dt
            dx = (int(self.mouseWatcherNode.isButtonDown(KeyboardButton.asciiKey("d"))) - int(self.mouseWatcherNode.isButtonDown(KeyboardButton.asciiKey("a")))) * speed
            dy = (int(self.mouseWatcherNode.isButtonDown(KeyboardButton.asciiKey("w"))) - int(self.mouseWatcherNode.isButtonDown(KeyboardButton.asciiKey("s")))) * speed
            if dx or dy:
                self.camera.setPos(self.camera, dx, dy, 0)
        return task.cont

    def _set_status(self, text):
        self.status_text = text
        self.status_label["text"] = text
        self._refresh_inspector()

    def userExit(self):
        try:
            self.save_scene()
        finally:
            super().userExit()


def main():
    parser = argparse.ArgumentParser(description="GAME ENGEN Python prototype")
    parser.add_argument("--renderer", choices=("opengl", "vulkan"), default="opengl")
    parser.add_argument("--scene", type=Path, default=None)
    args = parser.parse_args()
    try:
        app = EngineApp(args.renderer, args.scene)
        app.run()
    except Exception as exc:
        if args.renderer == "vulkan":
            print("Vulkan renderer could not start. This Panda3D build may not include the p3vulkandisplay display plugin.", file=sys.stderr)
        print(f"GAME ENGEN startup failed: {exc}", file=sys.stderr)
        raise


if __name__ == "__main__":
    main()
