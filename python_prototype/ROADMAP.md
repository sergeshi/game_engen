# Improvement plan: from prototype to a usable engine

This roadmap separates a reliable vertical slice from features that should only be added after the core contracts are stable.

## Phase 0 — Reproducible baseline

- [x] Create an isolated Python prototype branch; leave the browser branch unchanged.
- [x] Add a runnable application entry point and dependency manifest.
- [x] Add standard-library tests for scene validation, JSON round-trip, dialogue effects, AABB checks and undo/redo.
- [x] Add static regression checks for viewport click wiring, transparent-surface picking, tab switching and resize observers.
- [ ] Add CI on Windows/Linux, linting, type checking and a smoke-start test with a virtual display.

**Exit criteria:** clean install, repeatable launch, all tests green.

## Phase 1 — Scene/document model

- [x] Add renderer-independent SceneDocument operations for create, transform, duplicate, reparent and subtree delete.
- [x] Validate unique object/component IDs, transform values, parent references and hierarchy cycles.
- [x] Make JSON save atomic; preserve component data and unknown extension fields in round-trip tests.
- [x] Validate dialogue start nodes and links; report missing asset files and reject paths escaping the project root.
- [ ] Integrate SceneDocument as the sole source of truth across viewport, hierarchy, inspector and persistence.
- [ ] Add a transactional command system for every editor mutation and schema migrations.
- [ ] Add autosave, recovery files, dirty-state indication and project settings.
- Add autosave, recovery files, dirty-state indication and project settings.
- Test round-trip preservation for every supported field.

**Exit criteria:** editing and saving never silently discards scene data.

## Phase 2 — Editor workflow

- Replace the prototype list with a virtualized hierarchy, search, folders and drag/drop parenting.
- Add transform gizmos, numeric inspector fields, pivot/origin controls, snapping, local/world coordinates and multi-select.
- Add keyboard shortcuts, command palette, contextual menus and configurable layouts.
- Add asset browser, thumbnails, import settings and missing-resource diagnostics.
- Add prefab/linked-instance support and safe propagation of asset changes.

**Exit criteria:** a user can build, organize, inspect and reopen a small level without editing JSON manually.

## Phase 3 — Runtime and physics

- Separate editor camera/input from player camera/input.
- Replace placeholder selection spheres with accurate collision shapes and a dedicated raycast service.
- Add deterministic fixed-step simulation, character controller, gravity, jump, triggers, interaction volumes and collision layers.
- Add navigation mesh/pathfinding and runtime debugging overlays.
- Keep rendering and simulation decoupled so a renderer change does not alter game logic.

**Exit criteria:** movement, picking and interaction behave consistently in editor and play mode.

## Phase 4 — Narrative/RPG systems

- One dialogue schema and one runtime interpreter shared by editor preview and game mode.
- [x] Add renderer-independent validation for missing dialogue start nodes and broken choice links.
- [x] Apply dialogue choice effects and deduplicated journal entries in the shared core primitives.
- [ ] Wire the shared validator/interpreter into both the visual node graph and game runtime.
- Typed variables, conditions, effects, quest states, journal, inventory, skill checks and dialogue portraits.
- Save/load of runtime state with schema versioning and migration.
- NPC/trigger bindings through stable entity IDs, never hard-coded scene references.

**Exit criteria:** a sample quest can be authored, played, saved and resumed.

## Phase 5 — Rendering and assets

- Establish a backend interface for device creation, resources, render passes, frame timing and diagnostics.
- OpenGL is the baseline; Vulkan is a separate backend with feature checks, swapchain/device-loss handling and GPU validation.
- Use lightweight forward rendering first: depth testing, frustum culling, batching/instancing, shadow maps and tone mapping.
- Add glTF import, texture/material pipeline, mipmaps, asset caching and asynchronous loading.
- Build explicit capability fallbacks; never claim a backend is active unless device creation succeeds.

**Exit criteria:** identical scene content works on both tested backends with a documented feature matrix and no renderer-specific game logic.

## Phase 6 — Quality and distribution

- Unit, integration and golden-scene tests; headless serialization tests; performance benchmarks.
- Crash logs, diagnostics bundle, safe-mode startup and project recovery.
- Build/install packages for Windows and Linux, pinned dependencies and a clean-machine smoke test.
- Document licensing, supported hardware, minimum graphics API and known limitations.

**Exit criteria:** a reproducible release can be installed and tested on a clean machine.

## Architecture target

```text
python_prototype/
  main.py                 # application entry point
  engine/
    core.py               # schema, serialization, undo, dialogue primitives
    scene.py              # entities/components and scene graph
    runtime.py            # fixed-step simulation and gameplay state
    collision.py          # picking, collision layers and queries
    dialogue.py           # dialogue/quest interpreter
    assets.py             # import/cache/reference resolution
    render/
      interface.py        # backend contract
      opengl.py           # OpenGL backend
      vulkan.py           # Vulkan backend
  editor/
    hierarchy.py
    inspector.py
    viewport.py
    dialogue_graph.py
    asset_browser.py
  tests/
    test_core.py
    test_serialization.py
    test_dialogue.py
    test_runtime.py
```

The current code intentionally implements only a small vertical slice. The Vulkan switch is a guarded attempt to load Panda3D's experimental `p3vulkandisplay` module; Vulkan is **not** considered validated until tested with a build that includes that module and a real GPU/driver, and the backend is not assumed to have OpenGL feature parity. A production dual-backend renderer needs a dedicated backend implementation and parity tests.


## Work completed in python-prototype-foundation (2026-10-21)

- Viewport picking now ignores non-primary clicks, climbs child-mesh hits to the owning scene object, and can pass through translucent materials unless the object explicitly sets `userData.pickThrough = false`. The click handler remains wired to the viewport.
- Added static regression tests for picker wiring, transparent-surface behavior, tab-to-mode wiring and viewport resizing.
- Extended the renderer-independent core with a `SceneDocument`, hierarchy validation, duplicate/delete operations, dialogue-link validation, journal effects and safe project-relative asset resolution.
- These are foundation improvements, not full completion of the requested roadmap. The embedded editor still uses Three.js/WebGL; the native Python UI and renderer migration, complete end-to-end editor validation, material/light parity, importer validation, debugger and packaged builds remain open.
