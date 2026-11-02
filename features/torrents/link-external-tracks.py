"""Link external audio and subtitles beside matching videos without changing torrent files."""

import argparse
from collections import Counter
import os
from pathlib import Path
import sys

VIDEO = {".mkv", ".mp4", ".m4v", ".avi", ".mov", ".ts", ".m2ts", ".webm"}
AUDIO = {
    ".aac", ".ac3", ".adts", ".aif", ".aifc", ".aiff", ".caf", ".dts",
    ".dtshd", ".eac3", ".flac", ".m4a", ".mka", ".mlp", ".mp3",
    ".oga", ".ogg", ".thd", ".wav", ".wma",
}

SUBTITLES = {".srt", ".ass", ".ssa", ".vtt", ".idx", ".sub"}


def process(root, dry_run=False):
    # Do not traverse symlinks, including links outside this torrent.
    files = []
    failed = False

    def scan_error(error):
        nonlocal failed
        print(f"ERROR scanning {error.filename}: {error}", file=sys.stderr)
        failed = True

    for directory, dirs, names in os.walk(root, followlinks=False, onerror=scan_error):
        dirs[:] = sorted(d for d in dirs if not (Path(directory) / d).is_symlink())
        files.extend(Path(directory) / n for n in sorted(names)
                     if not (Path(directory) / n).is_symlink()
                     and (Path(directory) / n).is_file())
    videos = [p for p in files if p.suffix.lower() in VIDEO]
    pending = []
    for track in (p for p in files if p.suffix.lower() in AUDIO | SUBTITLES):
        # Literal string comparison: brackets in release names aren't glob syntax.
        matches = [v for v in videos if track.stem == v.stem
                   or track.stem.startswith(v.stem + ".")]
        if not matches:
            print(f"SKIP no matching video: {track}")
            continue
        longest = max(len(v.stem) for v in matches)
        matches = [v for v in matches if len(v.stem) == longest]
        if len(matches) != 1:
            print(f"SKIP ambiguous video: {track}")
            continue
        target = matches[0].parent / track.name
        if target == track:
            continue
        pending.append((track, target))

    # Plan before linking so dry runs and real runs choose the same names.
    counts = Counter(target for _, target in pending)
    rename = {track for track, target in pending if counts[target] > 1}
    # VobSub's index and data files must keep the same basename.
    pairs = {(p.parent, p.stem) for p in rename if p.suffix.lower() in {".idx", ".sub"}}
    rename.update(p for p, _ in pending
                  if p.suffix.lower() in {".idx", ".sub"} and (p.parent, p.stem) in pairs)

    def destination(track, target, full_group=False):
        if track not in rename:
            return target
        parts = track.relative_to(root).parent.parts if full_group else (track.parent.name,)
        group = ".".join(part.strip("[]") or part for part in parts)
        return target.with_name(f"{track.stem}.{group}{track.suffix}")

    named = [(track, destination(track, target)) for track, target in pending]
    counts = Counter(target for _, target in named)
    # Two nested folders can have the same group name; qualify with their path.
    qualify = {track for track, target in named if counts[target] > 1}
    qualify_pairs = {(p.parent, p.stem) for p in qualify if p.suffix.lower() in {".idx", ".sub"}}
    qualify.update(p for p, _ in pending
                   if p.suffix.lower() in {".idx", ".sub"} and (p.parent, p.stem) in qualify_pairs)
    named = [(track, destination(track, target, track in qualify)) for track, target in pending]
    counts = Counter(target for _, target in named)
    originals = dict(pending)
    for track, target in named:
        original = originals[track]
        if (os.path.lexists(original) and not original.is_symlink()
                and os.path.samefile(track, original)
                and not (track in rename and track.suffix.lower() in {".idx", ".sub"})):
            continue
        if counts[target] > 1:
            print(f"SKIP ambiguous destination: {target}")
            failed = True
            continue
        if os.path.lexists(target):
            if not target.is_symlink() and os.path.samefile(track, target):
                continue
            print(f"SKIP existing destination: {target}")
            continue
        if dry_run:
            print(f"WOULD LINK {track} -> {target}")
            continue
        try:
            os.link(track, target)
            print(f"LINK {track} -> {target}")
        except OSError as error:
            print(f"ERROR {track} -> {target}: {error}", file=sys.stderr)
            failed = True
    return 1 if failed else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path,
                        help="torrent directory; defaults to Transmission's event variables")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    root = args.root
    if root is None:
        directory = os.environ.get("TR_TORRENT_DIR")
        name = os.environ.get("TR_TORRENT_NAME")
        if not directory or not name:
            parser.error("provide a torrent directory or TR_TORRENT_DIR and TR_TORRENT_NAME")
        base = Path(directory).resolve()
        root = (base / name).resolve()
        if root == base or base not in root.parents:
            parser.error("torrent path must be inside TR_TORRENT_DIR")
    if root.is_file():
        # A single-file torrent has no nested tracks. Never scan other torrents.
        return 0
    if not root.is_dir() or root.is_symlink():
        parser.error(f"not a real directory: {root}")
    return process(root, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
