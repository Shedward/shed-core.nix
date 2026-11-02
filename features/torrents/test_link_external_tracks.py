import contextlib
import importlib.util
import io
import os
from pathlib import Path
import tempfile
import unittest


spec = importlib.util.spec_from_file_location(
    "tracks", Path(__file__).with_name("link-external-tracks.py")
)
tracks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tracks)


class TrackLinksTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.stem = "[release] Episode 01 [1080p]"
        self.file(self.stem + ".mkv")

    def file(self, name):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(name)
        return path

    def run_hook(self, dry_run=False):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(tracks.process(self.root, dry_run), 0)
        return output.getvalue()

    def test_unique_names_remain_unchanged(self):
        for ext in ("Group A.mka", "Group B.mka", "ass"):
            source = self.file(f"tracks/{self.stem}.{ext}")
            self.run_hook()
            self.assertTrue(source.samefile(self.root / source.name))
        self.assertNotIn("LINK ", self.run_hook())

    def test_identical_names_get_groups_in_dry_run_and_real_run(self):
        sources = [self.file(f"RUS Sound/[{g}]/{self.stem}.mka") for g in ("A", "B")]
        preview = self.run_hook(True)
        self.assertFalse((self.root / f"{self.stem}.mka").exists())
        for group in ("A", "B"):
            target = self.root / f"{self.stem}.{group}.mka"
            self.assertIn(str(target), preview)
            self.assertFalse(target.exists())
        self.run_hook()
        for group, source in zip(("A", "B"), sources):
            self.assertTrue(source.samefile(self.root / f"{self.stem}.{group}.mka"))
        self.assertNotIn("LINK ", self.run_hook())

    def test_existing_legacy_link_is_preserved(self):
        a = self.file(f"RUS Sound/A/{self.stem}.mka")
        b = self.file(f"RUS Sound/B/{self.stem}.mka")
        legacy = self.root / a.name
        os.link(a, legacy)
        self.run_hook()
        self.assertTrue(a.samefile(legacy))
        self.assertFalse((self.root / f"{self.stem}.A.mka").exists())
        self.assertTrue(b.samefile(self.root / f"{self.stem}.B.mka"))
        self.assertNotIn("LINK ", self.run_hook())

    def test_repeated_group_names_use_folder_paths(self):
        for parent in ("disc1", "disc2"):
            self.file(f"{parent}/Group/{self.stem}.mka")
        self.run_hook()
        for parent in ("disc1", "disc2"):
            self.assertTrue((self.root / f"{self.stem}.{parent}.Group.mka").exists())

    def test_idx_sub_keep_matching_names(self):
        self.file(f"RUS Subs/A/{self.stem}.idx")
        self.file(f"RUS Subs/A/{self.stem}.sub")
        self.file(f"RUS Subs/B/{self.stem}.sub")
        self.run_hook()
        for ext in ("idx", "sub"):
            self.assertTrue((self.root / f"{self.stem}.A.{ext}").exists())
        self.assertNotIn("LINK ", self.run_hook())

    def test_existing_file_is_not_overwritten(self):
        source = self.file(f"RUS Subs/A/{self.stem}.ass")
        existing = self.file(source.name)
        before = existing.read_bytes()
        self.run_hook()
        self.assertEqual(existing.read_bytes(), before)
        self.assertFalse((self.root / f"{self.stem}.A.ass").exists())


if __name__ == "__main__":
    unittest.main()
