# GAME ENGEN — Python Prototype

A small, runnable Python 3D editor/runtime prototype intended as a clean foundation alongside the existing browser prototype.

## What works in this prototype

- 3D scene viewport, grid, blockout geometry, lighting and camera controls.
- Hierarchy panel with selectable objects and inspector controls.
- Select objects by clicking in the viewport; move, rotate, scale, duplicate and delete.
- Undo/redo for common editor operations.
- JSON scene save/load with validation and atomic save.
- NPC interaction, branching dialogue choices, variables and journal entries.
- Runtime play mode with basic player movement and interaction.
- Automated tests for project serialization, dialogue state, and undo history.

## Requirements

Python 3.10+ recommended. Panda3D provides the lightweight scene graph, input, collision picking, and OpenGL renderer.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Run tests with `python -m unittest discover -s tests -v`.

## Renderer selection

```bash
python main.py --renderer opengl
python main.py --renderer vulkan
```

OpenGL is the supported baseline. Vulkan selection asks Panda3D to load its experimental `p3vulkandisplay` module. It is not shipped by every Panda3D build and is not feature-equivalent to OpenGL; the backend remains experimental and may fail on ordinary editor features. If the module is absent, the application reports the startup failure rather than silently claiming Vulkan is active. OpenGL is the only supported baseline in this prototype.

## Controls

- Left mouse: select an object.
- Right mouse drag: orbit camera.
- WASD: move camera; mouse wheel: zoom.
- G: move mode; R: rotate mode; S: scale mode.
- Arrow keys: transform selected object; Shift modifies step.
- Ctrl+D: duplicate; Delete: delete; Ctrl+Z / Ctrl+Y: undo/redo.
- E: interact with nearby NPC in play mode.
- F5: toggle play mode.
- Ctrl+S: save scene; Ctrl+O: load scene.
- Esc: quit.

## Current scope and limitations

This is a working blockout/editor foundation, not yet a production-ready engine. It intentionally avoids pretending to provide advanced physically based rendering, skeletal animation, navmesh authoring, a full visual dialogue graph, asset import pipeline, Vulkan parity on builds without the plugin, or cross-platform packaging. See [ROADMAP.md](ROADMAP.md).

The prototype is additive: it does not replace or rewrite the existing JavaScript branch.
