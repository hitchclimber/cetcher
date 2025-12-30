# Cetcher (*C*over art f*etcher*)

## Simple CLI to embed cover art to your audio files

When downloading audio from questionable sources[^1], or better yet, recording from your vinyl record collection, your audio files player might not be able to display cover art, depending on its implementation. This script remedies that by looking up the artist and album (derived from your folder structure), searching the [Cover Art Archive](coverartarchive.org) to retrieve the album's MBID, fetching the corresponding cover art (if present) and embedding this into the audio files.

[^1]: Not judging but their quality is often. _meh_

## Usage

Your folder structure should look something like this. You can run `cetcher -h` to see options and actual usage.

```

  Music/
  ├── Artist Name/
  │   ├── Album One/
  │   │   ├── 01 - Track.flac
  │   │   ├── 02 - Track.flac
  │   │   └── cover.jpg        # ignored
  │   └── Album Two/
  │       ├── 01 - Song.mp3
  │       └── 02 - Song.mp3
  └── Another Artist/
      └── Their Album/
          ├── 01 - Track.m4a
          └── notes.txt        # ignored

```
