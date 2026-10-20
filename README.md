# GAME ENGEN — Python 3D Editor / RPG Prototype

**The primary application on this branch is Python, not HTML.** The previous browser prototype is archived under `legacy_web/` and is not the app entry point.

## Quick start

Requires Python 3.10+ and a desktop environment with graphics drivers.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
python main.py
```

The root `main.py` launches `python_prototype/main.py`.

## Renderer

```bash
python main.py --renderer opengl
python main.py --renderer vulkan
```

OpenGL is the baseline. Vulkan is experimental and attempts to load Panda3D's `p3vulkandisplay` module. That module is not included in every Panda3D build; Vulkan support is not claimed as validated or feature-equivalent until tested on a build with the module and a real GPU.

## Implemented prototype features

- Lightweight Panda3D 3D viewport with grid and lighting.
- Object hierarchy, viewport picking, move/rotate/scale modes, duplicate/delete.
- Undo/redo and JSON scene save/load with validation and atomic writes.
- Play mode, simple player movement and blockout collision.
- NPC interaction, branching dialogue, variables and journal entries.
- Unit tests for renderer-independent core and GitHub Actions compile/test workflow.

## Tests

```bash
python -m unittest discover -s python_prototype/tests -v
```

CI runs source compilation and core unit tests. The GUI and graphics backend still require interactive testing on a real desktop.

## Project structure

```text
main.py                       # primary launcher
requirements.txt              # Python dependencies
python_prototype/
  main.py                     # editor/runtime
  engine/core.py              # validation, persistence, dialogue primitives, undo
  tests/test_core.py
  ROADMAP.md
legacy_web/index.html         # archived browser prototype; not the primary app
```

## Scope

This is a working foundation/prototype, not yet a production-ready engine. The next roadmap steps are numeric inspector fields and transform gizmos, robust scene hierarchy and asset pipeline, character controller with gravity/jump, one shared dialogue schema, visual dialogue graph, quests/inventory, and a tested renderer abstraction with OpenGL/Vulkan parity.

See [Python prototype README](python_prototype/README.md) and [improvement roadmap](python_prototype/ROADMAP.md).
