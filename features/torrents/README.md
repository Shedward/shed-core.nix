# External tracks after download

`link-external-tracks.py` operates on **one season folder**. Episode videos
must be in its root. External audio and subtitles may be anywhere beneath its
subfolders; container names such as `Audio` or `Subtitles` are not hardcoded.
Files already beside the videos are left in place and are not source tracks.
See the [glossary](../../CONTEXT.md).

## Matching and naming

A source filename must equal the complete episode stem, or start with that
stem followed by a dot and a version suffix. The longest matching root episode
stem wins. Video files in subfolders are not matching candidates. No matching
by episode number, fuzzy title matching, or moving/renaming torrent data is done.

Destination names follow fixed rules, regardless of other files present:

| Source relative to the season folder | Destination beside the video |
| --- | --- |
| `Audio/Episode.mka` | `Episode.external.mka` |
| `Audio/[Group A]/Episode.mka` | `Episode.Group A.mka` |
| `Subtitles/Episode.en.ass` | `Episode.en.ass` |
| `Audio/[Group A]/Episode.Group B.mka` | `Episode.Group B.mka` |

Extensions are normalized to lowercase. Square brackets surrounding a version
folder name are omitted from the version label.

The script creates hard links. Existing destinations referencing the same file
(device and inode) are skipped successfully. A destination holding a different
file, including a separate copy with identical bytes, is a conflict. Multiple
different sources claiming the same destination are also a conflict; no source
wins by traversal order and no numeric suffix is invented. Conflicts return a
nonzero exit status while unrelated tracks can still be processed.

Old links with different names are preserved. A canonical link may be added even
if an old link already references that source. Subsequent runs reuse the canonical
name, including when other source tracks are added or removed.

Both source members of an `.idx`/`.sub` pair must exist in the same folder with
the same stem. Both destinations are checked before either link is created. If
creation fails partway through, the script attempts to remove only links created
by that job. This is not an atomic two-file filesystem transaction; cleanup errors
are reported. An incomplete source pair is an error.

Unmatched sources are reported and skipped. Filesystem errors produce a nonzero
exit status. Source symlinks and symlinked subfolders are not traversed; destination
symlinks are treated as conflicts. The Transmission completion hook has no automatic
retry: fix the reported issue and rerun the command for that season.

## Manual processing on the server

Run as the user owning the downloaded files (`shed` in this configuration):

```sh
cd /etc/nixos
nix-shell -p python3 --run 'python3 features/torrents/link-external-tracks.py --dry-run "/path/to/season"'
```

Remove `--dry-run` to create links. Hard-link creation must run on the server's
local filesystem, with source and destination on the same filesystem.

Tests use only Python's standard library:

```sh
python3 -B features/torrents/test_link_external_tracks.py
```
