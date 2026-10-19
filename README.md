# GAME ENGEN — Narrative RPG Studio

Browser-first prototype for top-down 3D narrative RPGs inspired by dialogue-heavy isometric games.

## Run
Serve this folder with a local static server and open `index.html` in a modern browser. Three.js modules load from jsDelivr, so internet access is required on first run.

## Implemented prototype features
- Three.js viewport, orbit camera, grid, shadows, hemisphere and directional light.
- Blockout primitives: boxes, walls, floors, spheres, cylinders, stairs and capsule placeholders.
- Scene hierarchy, selection, transform gizmo, transform inspector, snapping, duplicate/delete and basic undo/redo.
- Material library with base color, roughness, metalness and opacity.
- Dynamic point/spot lights and environment controls.
- Dialogue graph with draggable nodes, speaker/text fields, player choices, outgoing links, simple flag conditions/effects and a dialogue play-test.
- WASD/arrows movement and E interaction in the play-test.
- JSON scene export/import and GLB/glTF/OBJ model import.
- SketchUp bridge helper in `plugins/sketchup/`.

## Known limitations
This is an early prototype, not a production engine. Static lightmap baking, UV generation, navmesh/pathfinding, robust physics/collision, full scripting/debugging, texture painting/UV editing, native SKP parsing and packaged standalone builds are not implemented yet. Browser model import supports GLB/glTF and OBJ. Native SketchUp files must be exported to an interchange format first. Keep exported JSON backups while the scene format evolves.

## Architecture direction
Keep scene objects, materials, lights, dialogue graphs and runtime data serializable and independent from viewport objects. This supports a gradual migration of performance-critical runtime systems to C# while keeping HTML-based editor tooling where useful.