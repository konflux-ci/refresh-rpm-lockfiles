from pathlib import Path
from unittest.mock import mock_open, patch

from refresh_rpm_lockfiles import Upgrade, read_upgrades_from_file

UPGRADES_JSON = """[
    {
        "packageFile": "subfolder/Containerfile"
    },
    {
        "packageFile": "Dockerfile"
    }
]
"""

# If a Dockerfile has multiple stages, referencing
# multiple Docker images, they can all be updated in
# one PR, but we only need to run rpm-lockfile-prototype once
UPGRADES_JSON_MULTIPLE_STAGES = """[
    {
        "packageFile": "Dockerfile"
    },
    {
        "packageFile": "Dockerfile"
    },
    {
        "packageFile": "subfolder/Containerfile"
    }
]
"""


def test_read_upgrades_from_file():
    with patch(
        "refresh_rpm_lockfiles.Path.open",
        mock_open(read_data=UPGRADES_JSON),
    ):
        assert read_upgrades_from_file(Path("test.json")) == [
            Upgrade(package_file="Dockerfile"),
            Upgrade(package_file="subfolder/Containerfile"),
        ]


def test_read_upgrades_from_file_multiple_stages():
    with patch(
        "refresh_rpm_lockfiles.Path.open",
        mock_open(read_data=UPGRADES_JSON_MULTIPLE_STAGES),
    ):
        assert read_upgrades_from_file(Path("test.json")) == [
            Upgrade(package_file="Dockerfile"),
            Upgrade(package_file="subfolder/Containerfile"),
        ]
