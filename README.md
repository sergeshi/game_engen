# GAME ENGEN — Narrative RPG Studio

This branch now launches the **original editor UI in a native Python desktop window** instead of launching the reduced Panda3D demo. The existing editor panels, scene tools, material/lighting controls, dialogue graph, play-test, model import and JSON project workflow remain in the bundled editor UI.

## Quick start (Windows)

1. Install Python 3.10 or newer.
2. From the repository folder run:

```bat
pip install -r requirements.txt
python main.py
```

Or double-click `RUN_GAME_ENGEN.bat`.

## What this build is — and is not

- `main.py` starts `desktop.py`, a Python/PySide6 desktop host.
- The host embeds `legacy_web/index.html` using Qt WebEngine. The original Three.js UI is intentionally preserved so this version does not lose the features and layout already present in `feature/narrative-rpg-foundation`.
- The 3D viewport currently uses the original Three.js/WebGL renderer. This is a compatibility bridge, **not yet a complete native Python/OpenGL/Vulkan renderer**. Vulkan parity is not claimed.
- `python_prototype/main.py` remains available as an isolated Panda3D engine experiment, but it is not the primary launcher because it does not yet match the original editor's feature set.
- The UI imports Three.js modules from jsDelivr, so first launch needs internet access. Project JSON exports are saved to the app's `downloads/` directory when initiated by the embedded browser.

## Features preserved from the original editor

- Three-dimensional viewport, orbit camera, grid, shadows, ambient/directional lighting and post-processing controls.
- Blockout primitives, hierarchy, selection, transform gizmo, numeric transform inspector, snapping, duplicate/delete, undo/redo.
- Materials with color, roughness, metalness, opacity and glow controls.
- Point/spot lights and global environment settings.
- Dialogue graph with nodes, speakers, text, choices, links and play-test.
- WASD/arrows movement and interaction in play-test.
- JSON project export/import and GLB/glTF/OBJ model import.
- SketchUp Ruby export helper/workflow and custom dialogue-widget styling controls.

The original project documents additional limitations honestly: lightmap baking, robust physics/navmesh, complete scripting/debugging, native SKP parsing and packaged standalone game builds are not implemented yet.

## Python engine prototype and tests

The separate `python_prototype/` directory contains an early native Panda3D experiment and renderer-independent core tests. Run:

```sh
python -m unittest discover -s python_prototype/tests -v
python python_prototype/main.py --renderer opengl
```

Panda3D's Vulkan display plugin is experimental and may not be present in the installed build. No Vulkan support is claimed until it has been tested on a real machine.

## Next migration stages

1. Preserve UI behavior with regression tests and document every original control/action.
2. Port project/scene/material/light/dialogue data models and persistence to Python without changing the user-facing workflow.
3. Replace the embedded Three.js viewport with a native Python renderer behind the same editor layout; validate picking, transforms, materials, lighting, imported assets and play mode before removing the compatibility bridge.
4. Validate OpenGL first, then Vulkan as a separately tested backend. Do not remove a working original feature until its Python replacement passes the same acceptance tests.
