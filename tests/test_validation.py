"""Tests for directory validation functions."""
import pytest
from cetcher.main import _is_valid_leaf, find_all_valid_leaves


class TestIsValidLeaf:
    """Tests for _is_valid_leaf function (uses any() - valid if ANY audio file exists)."""

    def test_empty_directory_is_invalid(self, empty_dir):
        """Empty directories should not be valid leaves."""
        assert _is_valid_leaf(empty_dir) is False

    def test_flac_only_directory_is_valid(self, valid_flac_dir):
        """Directory containing only .flac files is valid."""
        assert _is_valid_leaf(valid_flac_dir) is True

    def test_mp3_only_directory_is_valid(self, valid_mp3_dir):
        """Directory containing only .mp3 files is valid."""
        assert _is_valid_leaf(valid_mp3_dir) is True

    def test_mixed_audio_directory_is_valid(self, valid_mixed_audio_dir):
        """Directory with mixed audio types (.flac, .mp3, .m4a) is valid."""
        assert _is_valid_leaf(valid_mixed_audio_dir) is True

    def test_mixed_audio_and_non_audio_is_valid(self, invalid_mixed_dir):
        """Directory with audio and non-audio files is valid (audio files will be processed)."""
        assert _is_valid_leaf(invalid_mixed_dir) is True

    def test_non_audio_only_is_invalid(self, only_non_audio_dir):
        """Directory with only non-audio files is invalid."""
        assert _is_valid_leaf(only_non_audio_dir) is False

    def test_directory_with_only_subdirs_is_invalid(self, dir_with_subdirs):
        """Directory containing only subdirectories (no audio files) is not a valid leaf."""
        assert _is_valid_leaf(dir_with_subdirs) is False

    def test_case_insensitive_extensions(self, tmp_path):
        """File extensions should be case-insensitive."""
        d = tmp_path / "album"
        d.mkdir()
        (d / "track.FLAC").touch()
        (d / "track2.Flac").touch()
        (d / "track3.MP3").touch()
        assert _is_valid_leaf(d) is True


class TestFindAllValidLeaves:
    """Tests for find_all_valid_leaves function."""

    def test_finds_all_album_directories(self, nested_artist_structure):
        """Should find all valid album directories in nested structure."""
        leaves = list(find_all_valid_leaves(nested_artist_structure))
        assert len(leaves) == 3

    def test_returns_sorted_directories(self, nested_artist_structure):
        """Results should be sorted."""
        leaves = list(find_all_valid_leaves(nested_artist_structure))
        leaf_names = [l.name for l in leaves]
        assert leaf_names == sorted(leaf_names)

    def test_empty_root_returns_nothing(self, empty_dir):
        """Empty directory should yield no results."""
        leaves = list(find_all_valid_leaves(empty_dir))
        assert leaves == []

    def test_finds_directories_with_mixed_content(self, tmp_path):
        """Should find directories that contain audio files, even with non-audio files."""
        album1 = tmp_path / "artist" / "album1"
        album2 = tmp_path / "artist" / "album2"
        album1.mkdir(parents=True)
        album2.mkdir(parents=True)

        (album1 / "track.flac").touch()
        (album2 / "track.flac").touch()
        (album2 / "notes.txt").touch()  # non-audio file shouldn't disqualify

        leaves = list(find_all_valid_leaves(tmp_path))
        assert len(leaves) == 2

    def test_skips_directories_without_audio(self, tmp_path):
        """Should skip directories that have no audio files."""
        valid = tmp_path / "artist" / "valid_album"
        invalid = tmp_path / "artist" / "docs"
        valid.mkdir(parents=True)
        invalid.mkdir(parents=True)

        (valid / "track.flac").touch()
        (invalid / "notes.txt").touch()

        leaves = list(find_all_valid_leaves(tmp_path))
        assert len(leaves) == 1
        assert leaves[0].name == "valid_album"

    def test_single_valid_leaf_at_root(self, valid_flac_dir):
        """When starting from a valid leaf's parent, should find that leaf."""
        parent = valid_flac_dir.parent
        leaves = list(find_all_valid_leaves(parent))
        assert len(leaves) == 1
        assert leaves[0] == valid_flac_dir

    def test_deeply_nested_structure(self, tmp_path):
        """Should find leaves in deeply nested structures."""
        deep = tmp_path / "a" / "b" / "c" / "d" / "album"
        deep.mkdir(parents=True)
        (deep / "track.flac").touch()

        leaves = list(find_all_valid_leaves(tmp_path))
        assert len(leaves) == 1
        assert leaves[0] == deep
