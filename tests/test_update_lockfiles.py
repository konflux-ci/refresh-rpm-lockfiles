from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import call, patch

from refresh_rpm_lockfiles import Upgrade, update_lockfiles


def test_update_lockfiles():
    upgrades = [
        Upgrade(package_file="subfolder/Containerfile"),
        Upgrade(package_file="Dockerfile"),
    ]

    input_file_map = {
        "subfolder/Containerfile": "subfolder/rpms.in.yaml",
        "Dockerfile": "rpms.in.yaml",
    }

    with patch(
        "refresh_rpm_lockfiles.subprocess.run",
        side_effect=[CompletedProcess("", 0), CompletedProcess("", 0)],
    ) as subprocess_run_mock:
        assert update_lockfiles(upgrades, input_file_map) == 0
        subprocess_run_mock.assert_has_calls(
            [
                call(
                    [
                        "rpm-lockfile-prototype",
                        "subfolder/rpms.in.yaml",
                        "--outfile",
                        Path("subfolder/rpms.lock.yaml"),
                    ],
                    check=True,
                ),
                call(
                    [
                        "rpm-lockfile-prototype",
                        "rpms.in.yaml",
                        "--outfile",
                        Path("rpms.lock.yaml"),
                    ],
                    check=True,
                ),
            ]
        )


def test_update_one_fails():
    upgrades = [
        Upgrade(package_file="subfolder/Containerfile"),
        Upgrade(package_file="Dockerfile"),
    ]

    input_file_map = {
        "subfolder/Containerfile": "subfolder/rpms.in.yaml",
        "Dockerfile": "rpms.in.yaml",
    }

    with patch(
        "refresh_rpm_lockfiles.subprocess.run",
        side_effect=[CompletedProcess("", 1), CompletedProcess("", 0)],
    ) as subprocess_run_mock:
        assert update_lockfiles(upgrades, input_file_map) == 1
        subprocess_run_mock.assert_has_calls(
            [
                call(
                    [
                        "rpm-lockfile-prototype",
                        "subfolder/rpms.in.yaml",
                        "--outfile",
                        Path("subfolder/rpms.lock.yaml"),
                    ],
                    check=True,
                ),
                call(
                    [
                        "rpm-lockfile-prototype",
                        "rpms.in.yaml",
                        "--outfile",
                        Path("rpms.lock.yaml"),
                    ],
                    check=True,
                ),
            ]
        )
