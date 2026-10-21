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


if __name__ == "__main__":
    unittest.main()
