from pathlib import PurePath

import pytest

from refresh_rpm_lockfiles import resolve_relative_path


@pytest.mark.parametrize(
    ("input_path", "expected"),
    [
        ("a/b/c", "a/b/c"),  # no relative specifiers
        ("a/./b", "a/b"),  # single dot mid-path
        ("./a/b", "a/b"),  # leading dot
        ("a/b/.", "a/b"),  # trailing dot
        ("a/./b/./c", "a/b/c"),  # multiple dots
        ("a/b/../c", "a/c"),  # double dot goes up one level
        ("a/b/c/..", "a/b"),  # trailing double dot
        ("a/b/c/../../d", "a/d"),  # multiple double dots
        ("a/./b/../c", "a/c"),  # dot and double dot combined
        ("a", "a"),  # single component
    ],
)
def test_resolve_relative_path(input_path, expected):
    assert resolve_relative_path(PurePath(input_path)) == PurePath(expected)
