# GAME ENGEN — SketchUp bridge

SketchUp's native `.skp` format is proprietary and is not parsed directly by the browser prototype. Use SketchUp's 3D Model export to create an interchange file (GLB/glTF or OBJ where supported), then import that file in GAME ENGEN.

The accompanying Ruby helper adds a menu action to export the active model using formats supported by the installed SketchUp version. Export support varies by version and installed extensions.