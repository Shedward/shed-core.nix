# External media tracks

## Language

**Season folder**: A downloaded release containing one season. Its root contains the episode videos.

**Episode**: A video identified by its complete filename without the extension. Multiple video formats with that same name represent the same episode.

**External track**: Audio or subtitles belonging to an episode, stored separately from its video. An idx/sub pair is one external subtitle track represented by two files.

**Track container**: An immediate subfolder of the season folder containing external tracks, directly or inside version folders. Its name does not determine its role.

**Version folder**: A folder nested inside a track container that names a particular dub or subtitle version. For a track in a deeper hierarchy, its immediate parent provides this name.

**Version suffix**: The part of a track filename after the complete episode name and before its extension. It identifies the track version and takes precedence over the version folder.

**Unnamed version**: A track with neither a version suffix nor a version folder. Its version label is `external`.
