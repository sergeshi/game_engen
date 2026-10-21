"""Static regression guards for the embedded editor's critical wiring.

These do not replace an interactive GUI test, but catch regressions where a
handler exists yet is no longer connected to the actual viewport or tabs.
"""
from pathlib import Path
import unittest

EDITOR = Path(__file__).resolve().parents[2] / "legacy_web" / "index.html"


class EditorContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = EDITOR.read_text(encoding="utf-8")

    def test_viewport_click_handler_is_wired(self):
        self.assertIn("renderer.domElement.addEventListener('pointerdown',pick)", self.html)
        self.assertIn("function pick(e)", self.html)

    def test_picker_only_handles_primary_click_in_level_editor(self):
        start = self.html.index("function pick(e){")
        end = self.html.index("function hierarchy(){", start)
        picker = self.html[start:end]
        self.assertIn("e.button!==0", picker)
        self.assertIn("S.mode!=='level'", picker)
        self.assertIn("raycaster.intersectObjects", picker)
        self.assertIn("select(o.userData.id)", picker)

    def test_transparent_surfaces_allow_pick_through(self):
        start = self.html.index("function pick(e){")
        end = self.html.index("function hierarchy(){", start)
        picker = self.html[start:end]
        self.assertIn("transparentPassThrough", picker)
        self.assertIn("owner.userData.pickThrough===false", picker)

    def test_editor_tabs_are_connected_to_mode_switching(self):
        self.assertIn("$$('.tab').forEach(b=>b.onclick=()=>setMode(b.dataset.mode))", self.html)
        self.assertIn("function setMode(mode)", self.html)

    def test_viewport_resizes_after_panel_or_window_changes(self):
        self.assertIn("window.addEventListener('resize',resize)", self.html)
        self.assertIn("new ResizeObserver(()=>resize()).observe($('#viewport'))", self.html)
        self.assertIn("camera.updateProjectionMatrix()", self.html)


    def test_widget_visual_designer_has_live_preview_and_component_targets(self):
        self.assertIn('id="widgetDesigner"', self.html)
        self.assertIn("function renderWidgetDesigner()", self.html)
        self.assertIn("function widgetInspector()", self.html)
        for target in ("prompt", "dialogPanel", "speaker", "dialogText", "choice", "portrait"):
            self.assertIn(target, self.html)
        self.assertIn("updateWidgetDesignerPreview()", self.html)

    def test_widget_styles_are_saved_and_restored(self):
        self.assertIn("widgetStyles:S.widgetStyles", self.html)
        self.assertIn("S.widgetStyles=d.widgetStyles||{}", self.html)
        self.assertIn("function ensureWidgetStyles()", self.html)
        self.assertIn("Export style", self.html)
        self.assertIn("Import style", self.html)

    def test_visual_styles_apply_to_runtime_widgets(self):
        self.assertIn("const st=widgetStyle('prompt')", self.html)
        self.assertIn("panelStyle=widgetStyle('dialogPanel')", self.html)
        self.assertIn("speakerStyle=widgetStyle('speaker')", self.html)
        self.assertIn("choiceStyle=widgetStyle('choice')", self.html)

    def test_widgets_mode_displays_design_studio_instead_of_scene_canvas(self):
        self.assertIn("$('#viewport').classList.toggle('hidden',mode==='dialogue'||mode==='widgets')", self.html)
        self.assertIn("$('#widgetDesigner').classList.toggle('hidden',mode!=='widgets')", self.html)

    def test_widget_preview_supports_drag_and_numeric_offsets(self):
        self.assertIn("function beginWidgetPreviewDrag(e,target)", self.html)
        self.assertIn("Horizontal offset (px)", self.html)
        self.assertIn("Vertical offset (px)", self.html)
        self.assertIn("st.offsetX", self.html)
        self.assertIn("st.offsetY", self.html)
        self.assertIn("widgetPreviewDragInstalled", self.html)

if __name__ == "__main__":
    unittest.main()
