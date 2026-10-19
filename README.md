# GAME ENGEN — Narrative RPG Studio

Browser-first prototype for top-down 3D narrative RPGs inspired by dialogue-heavy isometric games.

## Run
Serve this folder with a local static server and open `index.html` in a modern browser. Three.js modules load from jsDelivr, so internet access is required on first run.

## Current editor prototype
- Three.js 3D viewport, orbit camera, grid, shadow maps, hemisphere and directional light.
- Blockout primitives: boxes, walls, floors, spheres, cylinders, stairs and capsule placeholders.
- Scene hierarchy, object selection, transform gizmo, transform inspector, snapping, duplicate/delete and basic undo/redo.
- Material library with base color, roughness, metalness and opacity controls.
- Dynamic point/spot lights and environment controls.
- Dialogue graph with draggable nodes, speaker/text, choices, links and dialogue play-test.
- WASD/arrows movement and E interaction in the play-test.
- JSON project export/import and GLB/glTF/OBJ model import.
- SketchUp Ruby export helper/workflow.

## New engine foundation modules
- `engine/core.js`: serializable project normalization, scene/dialogue reference validation, dialogue condition/effect interpreter (skill checks, flags/variables and chance checks), dialogue history/journal snapshots, and axis-aligned collision helpers.
- `tests/core.test.js`: Node test coverage for project validation, dialogue checks/effects/save restoration, and AABB collision helpers.
- `package.json`: `npm test` and `npm run serve` scripts.

Run tests with Node.js 20+:
```sh
npm test
```

## Known limitations — do not mistake these for implemented features
This is an early prototype, not a production engine. The core modules are being separated from the viewport incrementally; the existing HTML editor does not yet use every helper in `engine/core.js`. Full collision integration in the play mode, mouse-wired dialogue connectors, a complete skill/variable inspector, and automated end-to-end browser tests are still to be integrated.

Static lightmap baking, UV generation and painting, robust physics, navmesh/pathfinding, full scripting/debugging, native SKP parsing and packaged standalone builds are not implemented yet. Browser model import supports GLB/glTF and OBJ. Native SketchUp files must be exported to an interchange format first. The current SketchUp helper relies on formats available in the installed SketchUp version; it is not a native SKP importer or a fully bidirectional live link.

## Roadmap
1. Stabilize scene serialization, geometry/material round-tripping, selection, transform editing and undo/redo.
2. Integrate dialogue graph connectors, validation panel, skills, variables, probability checks, journal and branch debugger.
3. Build an isolated top-down runtime with capsule movement, collision, interactables, triggers and save/load.
4. Add texture slots and UV controls, then realtime lighting quality settings and a real static-light baking pipeline.
5. Improve asset import and resource relinking; build a SketchUp bridge that can reliably re-export changed models.
6. Add project validation, runtime packaging and standalone game builds.

## Architecture direction
Keep scene objects, materials, lights, dialogue graphs and runtime state serializable and independent from Three.js viewport objects. This supports testing and gradual migration of performance-critical runtime systems to C# while keeping HTML-based editor tooling where useful.
