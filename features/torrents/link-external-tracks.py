"""Link external audio and subtitles beside the videos in a season folder."""

import argparse
from collections import defaultdict
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
VOBSUB = {".idx", ".sub"}


def destination(root, track, episodes):
    matches = [stem for stem in episodes
               if track.stem == stem or track.stem.startswith(stem + ".")]
    if not matches:
        print(f"SKIP no matching episode in season root: {track}")
        return None
    episode = max(matches, key=len)
    version = track.stem[len(episode) + 1:]
    if not version:
        if track.parent.parent == root:
            version = "external"
        else:
            version = track.parent.name.strip("[]") or track.parent.name
    return root / f"{episode}.{version}{track.suffix.lower()}"


def link_job(job, dry_run):
    """Preflight the entire track (one file or an idx/sub pair) before writing."""
    created = []
    try:
        missing = []
        for source, target in job:
            if source.is_symlink() or not source.is_file():
                raise OSError(f"source is not a regular file: {source}")
            if os.path.lexists(target):
                if target.is_symlink() or not os.path.samefile(source, target):
                    raise FileExistsError(f"destination contains a different file: {target}")
                print(f"SKIP already linked: {target}")
            else:
                missing.append((source, target))
        for source, target in missing:
            if dry_run:
                print(f"WOULD LINK {source} -> {target}")
                continue
            try:
                os.link(source, target, follow_symlinks=False)
                created.append((source, target))
            except FileExistsError:
                # Another hook may have created the same link after preflight.
                if target.is_symlink() or not os.path.samefile(source, target):
                    raise
        for source, target in created:
            print(f"LINK {source} -> {target}")
        return True
    except OSError as error:
        print(f"ERROR {job[0][0]}: {error}", file=sys.stderr)
        # Do not leave half of a newly created VobSub pair after a link failure.
        # Links which existed before this job are never removed.
        for source, target in reversed(created):
            try:
                if not target.is_symlink() and os.path.samefile(source, target):
                    target.unlink()
            except OSError as cleanup_error:
                print(f"ERROR rolling back {target}: {cleanup_error}", file=sys.stderr)
        return False


def process(root, dry_run=False):
    failed = False

    def scan_error(error):
        nonlocal failed
        print(f"ERROR scanning {error.filename}: {error}", file=sys.stderr)
        failed = True

    files = []
    for directory, dirs, names in os.walk(root, followlinks=False, onerror=scan_error):
        dirs[:] = sorted(d for d in dirs if not (Path(directory) / d).is_symlink())
        files.extend(Path(directory) / name for name in sorted(names)
                     if not (Path(directory) / name).is_symlink()
                     and (Path(directory) / name).is_file())
    # Multiple video formats with the same stem represent the same episode.
    episodes = {p.stem for p in files if p.parent == root and p.suffix.lower() in VIDEO}
    tracks = [p for p in files if p.parent != root and p.suffix.lower() in AUDIO | SUBTITLES]
    pairs = defaultdict(list)
    jobs = []
    for track in tracks:
        target = destination(root, track, episodes)
        if target is None:
            continue
        if track.suffix.lower() in VOBSUB:
            pairs[track.parent, track.stem].append((track, target))
        else:
            jobs.append([(track, target)])
    for pair in pairs.values():
        if len(pair) != 2 or {p.suffix.lower() for p, _ in pair} != VOBSUB:
            print(f"ERROR incomplete or ambiguous idx/sub pair: {pair[0][0]}", file=sys.stderr)
            failed = True
        else:
            jobs.append(pair)

    # Detect competing sources before creating any destinations, including on
    # dry runs. A shared file (hard links in multiple source folders) is OK.
    claims = defaultdict(list)
    for job in jobs:
        for source, target in job:
            claims[target].append(source)
    conflicts = set()
    for target, sources in claims.items():
        try:
            if any(not os.path.samefile(sources[0], other) for other in sources[1:]):
                raise FileExistsError(f"different sources claim the same destination: {sources}")
        except OSError as error:
            print(f"ERROR planning {target}: {error}", file=sys.stderr)
            conflicts.add(target)
            failed = True
    for job in jobs:
        if any(target in conflicts for _, target in job):
            continue
        if not link_job(job, dry_run):
            failed = True
    return 1 if failed else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path,
                        help="season directory; defaults to Transmission's event variables")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    root = args.root
    if root is None:
        directory = os.environ.get("TR_TORRENT_DIR")
        name = os.environ.get("TR_TORRENT_NAME")
        if not directory or not name:
            parser.error("provide a season directory or TR_TORRENT_DIR and TR_TORRENT_NAME")
        base = Path(directory).resolve()
        root = base / name
        if root.is_symlink():
            parser.error(f"season directory must not be a symlink: {root}")
        root = root.resolve()
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
