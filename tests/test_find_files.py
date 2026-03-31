import tempfile
from pathlib import Path
from unittest.mock import mock_open, patch

from refresh_rpm_lockfiles import (
    find_rpm_input_files_in_repo,
)

TMP_PATH = Path(tempfile.gettempdir())


RPMS_IN_YAML_NO_CONTAINERFILE = """contentOrigin:
  repofiles:
    - ./ubi.repo
packages: [cargo]
"""


RPMS_IN_YAML_WITH_CONTAINERFILE = """contentOrigin:
  repofiles:
    - ./ubi.repo
packages: [cargo]
context:
  containerfile: Containerfile
"""


def _make_walk_entry(directory: Path, files: list[str]):
    """Return a single os.walk-style tuple for use in Path.walk() mocks."""
    return (directory, [], files)


def test_find_rpm_input_files_no_rpms_in_yaml():
    """Returns an empty map when no rpms.in.yaml files are found."""
    walk_entries = [_make_walk_entry(TMP_PATH, ["Dockerfile", "README.md"])]

    with (
        patch("refresh_rpm_lockfiles.Path.cwd", return_value=TMP_PATH),
        patch.object(Path, "walk", return_value=iter(walk_entries)),
    ):
        result = find_rpm_input_files_in_repo()

    assert result == {}


def test_find_rpm_input_files_dockerfile_sibling_exists():
    """Uses Dockerfile as the containerfile when it exists next to rpms.in.yaml."""
    walk_entries = [_make_walk_entry(TMP_PATH, ["rpms.in.yaml", "Dockerfile"])]

    with (
        patch("refresh_rpm_lockfiles.Path.cwd", return_value=TMP_PATH),
        patch.object(
            Path,
            "walk",
            return_value=iter(walk_entries),
        ),
        patch(
            "refresh_rpm_lockfiles.Path.open",
            mock_open(read_data=RPMS_IN_YAML_NO_CONTAINERFILE),
        ),
        patch(
            "refresh_rpm_lockfiles.Path.exists",
            side_effect=[True, False],  # Dockerfile exists
        ),
    ):
        result = find_rpm_input_files_in_repo()

    assert result == {"Dockerfile": "rpms.in.yaml"}


def test_find_rpm_input_files_containerfile_sibling_exists():
    """Uses Dockerfile as the containerfile when it exists next to rpms.in.yaml."""
    walk_entries = [_make_walk_entry(TMP_PATH, ["rpms.in.yaml", "Containerfile"])]

    with (
        patch("refresh_rpm_lockfiles.Path.cwd", return_value=TMP_PATH),
        patch.object(
            Path,
            "walk",
            return_value=iter(walk_entries),
        ),
        patch(
            "refresh_rpm_lockfiles.Path.open",
            mock_open(read_data=RPMS_IN_YAML_NO_CONTAINERFILE),
        ),
        patch(
            "refresh_rpm_lockfiles.Path.exists",
            side_effect=[False, True],  # Containerfile exists, but not Dockerfile
        ),
    ):
        result = find_rpm_input_files_in_repo()

    assert result == {"Containerfile": "rpms.in.yaml"}


def test_find_rpm_input_files_dockerfile_configured():
    """Uses Dockerfile as the containerfile when it exists next to rpms.in.yaml."""
    walk_entries = [_make_walk_entry(TMP_PATH, ["rpms.in.yaml", "Dockerfile"])]

    with (
        patch("refresh_rpm_lockfiles.Path.cwd", return_value=TMP_PATH),
        patch.object(
            Path,
            "walk",
            return_value=iter(walk_entries),
        ),
        patch(
            "refresh_rpm_lockfiles.Path.open",
            mock_open(read_data=RPMS_IN_YAML_WITH_CONTAINERFILE),
        ),
        patch(
            "refresh_rpm_lockfiles.Path.exists",
            side_effect=[False],  # Dockerfile exists
        ),
    ):
        result = find_rpm_input_files_in_repo()

    assert result == {}


def test_find_rpm_input_files_containerfile_configured():
    """Uses Dockerfile as the containerfile when it exists next to rpms.in.yaml."""
    walk_entries = [_make_walk_entry(TMP_PATH, ["rpms.in.yaml", "Containerfile"])]

    with (
        patch("refresh_rpm_lockfiles.Path.cwd", return_value=TMP_PATH),
        patch.object(
            Path,
            "walk",
            return_value=iter(walk_entries),
        ),
        patch(
            "refresh_rpm_lockfiles.Path.open",
            mock_open(read_data=RPMS_IN_YAML_WITH_CONTAINERFILE),
        ),
        patch(
            "refresh_rpm_lockfiles.Path.exists",
            side_effect=[True],  # Containerfile exists, but not Dockerfile
        ),
    ):
        result = find_rpm_input_files_in_repo()

    assert result == {"Containerfile": "rpms.in.yaml"}
