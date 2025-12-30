import pytest
from pathlib import Path


@pytest.fixture
def empty_dir(tmp_path):
    """An empty directory."""
    d = tmp_path / "empty"
    d.mkdir()
    return d


@pytest.fixture
def valid_flac_dir(tmp_path):
    """Directory with only .flac files."""
    d = tmp_path / "artist" / "album"
    d.mkdir(parents=True)
    (d / "01 - track.flac").touch()
    (d / "02 - track.flac").touch()
    (d / "03 - track.flac").touch()
    return d


@pytest.fixture
def valid_mp3_dir(tmp_path):
    """Directory with only .mp3 files."""
    d = tmp_path / "artist" / "album"
    d.mkdir(parents=True)
    (d / "01 - track.mp3").touch()
    (d / "02 - track.mp3").touch()
    return d


@pytest.fixture
def valid_mixed_audio_dir(tmp_path):
    """Directory with mixed audio filetypes."""
    d = tmp_path / "artist" / "album"
    d.mkdir(parents=True)
    (d / "01 - track.flac").touch()
    (d / "02 - track.mp3").touch()
    (d / "03 - track.m4a").touch()
    return d


@pytest.fixture
def invalid_mixed_dir(tmp_path):
    """Directory with audio and non-audio files."""
    d = tmp_path / "artist" / "album"
    d.mkdir(parents=True)
    (d / "01 - track.flac").touch()
    (d / "cover.jpg").touch()
    (d / "info.txt").touch()
    return d


@pytest.fixture
def only_non_audio_dir(tmp_path):
    """Directory with no audio files."""
    d = tmp_path / "docs"
    d.mkdir()
    (d / "readme.txt").touch()
    (d / "cover.jpg").touch()
    return d


@pytest.fixture
def nested_artist_structure(tmp_path):
    """
    Nested structure:
    tmp_path/
      artist1/
        album1/
          track.flac
        album2/
          track.flac
      artist2/
        album1/
          track.mp3
    """
    a1 = tmp_path / "artist1"
    a1_album1 = a1 / "album1"
    a1_album2 = a1 / "album2"
    a2 = tmp_path / "artist2"
    a2_album1 = a2 / "album1"

    for d in [a1_album1, a1_album2, a2_album1]:
        d.mkdir(parents=True)

    (a1_album1 / "track.flac").touch()
    (a1_album2 / "track.flac").touch()
    (a2_album1 / "track.mp3").touch()

    return tmp_path


@pytest.fixture
def dir_with_subdirs(tmp_path):
    """Directory containing subdirectories (not a leaf)."""
    d = tmp_path / "artist"
    d.mkdir()
    (d / "album1").mkdir()
    (d / "album2").mkdir()
    return d
