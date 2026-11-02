import contextlib
import importlib.util
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


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

    def run_hook(self, dry_run=False, expected=0):
        output, errors = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            self.assertEqual(tracks.process(self.root, dry_run), expected)
        return output.getvalue() + errors.getvalue()

    def test_version_rules_and_repeat_runs(self):
        for folder, suffix, version, ext in (
            ("audio", "", "external", ".mka"),
            ("subtitles", "", "external", ".ass"),
            ("audio/[Group A]", "", "Group A", ".ac3"),
            ("subtitles/[Group A]", "", "Group A", ".srt"),
            ("audio/[Group A]", ".Group B", "Group B", ".flac"),
            ("subtitles", ".en.forced", "en.forced", ".vtt"),
            ("audio/deeper/[Group C]", "", "Group C", ".eac3"),
        ):
            with self.subTest(folder=folder, ext=ext):
                source = self.file(f"{folder}/{self.stem}{suffix}{ext}")
                target = self.root / f"{self.stem}.{version}{ext}"
                self.assertIn(str(target), self.run_hook(True))
                self.assertFalse(target.exists())
                self.run_hook()
                self.assertTrue(source.samefile(target))
                self.assertNotIn("LINK ", self.run_hook())

    def test_root_tracks_are_preserved_but_do_not_replace_canonical_links(self):
        source = self.file(f"audio/A/{self.stem}.mka")
        legacy = self.root / source.name
        os.link(source, legacy)
        self.run_hook()
        self.assertTrue(source.samefile(legacy))
        self.assertTrue(source.samefile(self.root / f"{self.stem}.A.mka"))
        self.assertNotIn("LINK ", self.run_hook())

    def test_other_root_track_is_not_overwritten(self):
        source = self.file(f"audio/A/{self.stem}.mka")
        existing = self.file(source.name)
        before = existing.read_bytes()
        self.run_hook()
        self.assertEqual(existing.read_bytes(), before)
        self.assertTrue(source.samefile(self.root / f"{self.stem}.A.mka"))

    def test_canonical_conflict_is_error_even_for_identical_bytes(self):
        source = self.file(f"audio/A/{self.stem}.mka")
        target = self.file(f"{self.stem}.A.mka")
        target.write_bytes(source.read_bytes())
        self.file(f"subtitles/{self.stem}.ass")
        self.assertIn("different file", self.run_hook(True, expected=1))
        self.run_hook(expected=1)
        self.assertFalse(source.samefile(target))
        self.assertTrue((self.root / f"{self.stem}.external.ass").exists())

    def test_two_different_sources_claiming_one_name_both_fail(self):
        for container in ("audio1", "audio2"):
            self.file(f"{container}/A/{self.stem}.mka")
        preview = self.run_hook(True, expected=1)
        self.assertNotIn("WOULD LINK", preview)
        self.run_hook(expected=1)
        self.assertFalse((self.root / f"{self.stem}.A.mka").exists())

    def test_sources_sharing_an_inode_can_claim_one_name(self):
        a = self.file(f"audio/A/{self.stem}.mka")
        b = self.root / f"other/A/{self.stem}.mka"
        b.parent.mkdir(parents=True)
        os.link(a, b)
        self.run_hook()
        self.assertTrue(a.samefile(self.root / f"{self.stem}.A.mka"))

    def test_names_stay_stable_when_another_group_is_removed(self):
        a = self.file(f"audio/A/{self.stem}.mka")
        b = self.file(f"audio/B/{self.stem}.mka")
        self.run_hook()
        b.unlink()
        self.assertNotIn("LINK ", self.run_hook())
        self.assertTrue(a.samefile(self.root / f"{self.stem}.A.mka"))
        self.assertFalse((self.root / a.name).exists())

    def test_multiple_video_formats_are_one_episode(self):
        self.file(self.stem + ".mp4")
        source = self.file(f"subtitles/{self.stem}.ass")
        self.run_hook()
        self.assertTrue(source.samefile(self.root / f"{self.stem}.external.ass"))

    def test_nested_video_does_not_steal_a_root_episodes_track(self):
        self.file(f"bonus/{self.stem}.en.mkv")
        source = self.file(f"subtitles/{self.stem}.en.ass")
        self.run_hook()
        self.assertTrue(source.samefile(self.root / source.name))
        self.assertFalse((self.root / "bonus" / source.name).exists())

    def test_unmatched_names_and_root_tracks_are_not_reprocessed(self):
        self.file(self.stem + ".mka")
        self.file("subtitles/Episode 01.ass")
        output = self.run_hook()
        self.assertIn("no matching episode", output)
        self.assertNotIn("LINK ", output)

    def make_pair(self):
        return [self.file(f"subtitles/A/{self.stem}{ext}") for ext in (".idx", ".sub")]

    def test_pair_is_linked_with_one_basename(self):
        pair = self.make_pair()
        self.run_hook(True)
        for source in pair:
            self.assertFalse((self.root / f"{self.stem}.A{source.suffix}").exists())
        self.run_hook()
        for source in pair:
            self.assertTrue(source.samefile(self.root / f"{self.stem}.A{source.suffix}"))
        self.assertNotIn("LINK ", self.run_hook())

    def test_incomplete_pair_is_an_error(self):
        self.file(f"subtitles/A/{self.stem}.sub")
        self.assertIn("incomplete", self.run_hook(expected=1))
        self.assertFalse((self.root / f"{self.stem}.A.sub").exists())

    def test_pair_conflict_cannot_mix_two_versions(self):
        self.make_pair()
        self.file(f"{self.stem}.A.idx")
        self.run_hook(expected=1)
        self.assertFalse((self.root / f"{self.stem}.A.sub").exists())

    def test_pair_creation_failure_rolls_back_only_new_links(self):
        self.make_pair()
        real_link = os.link

        def fail_second(source, target, **kwargs):
            if source.suffix == ".sub":
                raise OSError("simulated disk error")
            return real_link(source, target, **kwargs)

        with patch.object(tracks.os, "link", side_effect=fail_second):
            self.run_hook(expected=1)
        self.assertFalse((self.root / f"{self.stem}.A.idx").exists())
        self.assertFalse((self.root / f"{self.stem}.A.sub").exists())

    def test_preexisting_pair_member_survives_a_failure(self):
        idx, _ = self.make_pair()
        target = self.root / f"{self.stem}.A.idx"
        os.link(idx, target)
        with patch.object(tracks.os, "link", side_effect=OSError("simulated disk error")):
            self.run_hook(expected=1)
        self.assertTrue(idx.samefile(target))

    def test_symlink_destination_is_not_followed_or_overwritten(self):
        source = self.file(f"audio/A/{self.stem}.mka")
        target = self.root / f"{self.stem}.A.mka"
        target.symlink_to(source)
        self.run_hook(expected=1)
        self.assertTrue(target.is_symlink())

    def test_unreadable_subdirectory_is_an_error(self):
        folder = self.root / "audio"
        folder.mkdir()
        folder.chmod(0)
        try:
            self.assertIn("ERROR scanning", self.run_hook(expected=1))
        finally:
            folder.chmod(0o700)

    def test_simultaneous_creation_of_the_same_link_is_success(self):
        self.file(f"audio/A/{self.stem}.mka")
        real_link = os.link

        def another_hook(source, target, **kwargs):
            real_link(source, target, **kwargs)
            return real_link(source, target, **kwargs)

        with patch.object(tracks.os, "link", side_effect=another_hook):
            self.run_hook()
        self.assertNotIn("LINK ", self.run_hook())


if __name__ == "__main__":
    unittest.main()
