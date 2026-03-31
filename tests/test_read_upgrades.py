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


def test_read_upgrades_from_file():
    with patch(
        "refresh_rpm_lockfiles.Path.open",
        mock_open(read_data=UPGRADES_JSON),
    ):
        assert read_upgrades_from_file(Path("test.json")) == [
            Upgrade(package_file="subfolder/Containerfile"),
            Upgrade(package_file="Dockerfile"),
        ]
