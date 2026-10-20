import os
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import ANY, MagicMock, call, patch

from refresh_rpm_lockfiles import RPM_LOCKFILE_PROTOTYPE_DNF_CACHE, Upgrade, update_lockfiles


def test_update_lockfiles():
    upgrades = [
        Upgrade(package_file="subfolder/Containerfile"),
        Upgrade(package_file="Dockerfile"),
    ]

    input_file_map = {
        "subfolder/Containerfile": ["subfolder/rpms.in.yaml"],
        "Dockerfile": ["rpms.in.yaml"],
    }

    with patch(
        "refresh_rpm_lockfiles.subprocess.run",
        side_effect=[CompletedProcess("", 0), CompletedProcess("", 0)],
    ) as subprocess_run_mock:
        assert update_lockfiles(upgrades, input_file_map) is False
        subprocess_run_mock.assert_has_calls(
            [
                call(
                    [
                        "rpm-lockfile-prototype",
                        "subfolder/rpms.in.yaml",
                        "--outfile",
                        Path("subfolder/rpms.lock.yaml"),
                    ],
                    env=ANY,
                    check=False,
                ),
                call(
                    [
                        "rpm-lockfile-prototype",
                        "rpms.in.yaml",
                        "--outfile",
                        Path("rpms.lock.yaml"),
                    ],
                    env=ANY,
                    check=False,
                ),
            ],
        )


def test_update_one_fails():
    upgrades = [
        Upgrade(package_file="subfolder/Containerfile"),
        Upgrade(package_file="Dockerfile"),
    ]

    input_file_map = {
        "subfolder/Containerfile": ["subfolder/rpms.in.yaml"],
        "Dockerfile": ["rpms.in.yaml"],
    }

    with patch(
        "refresh_rpm_lockfiles.subprocess.run",
        side_effect=[CompletedProcess("", 1), CompletedProcess("", 0)],
    ) as subprocess_run_mock:
        assert update_lockfiles(upgrades, input_file_map) is True
        subprocess_run_mock.assert_has_calls(
            [
                call(
                    [
                        "rpm-lockfile-prototype",
                        "subfolder/rpms.in.yaml",
                        "--outfile",
                        Path("subfolder/rpms.lock.yaml"),
                    ],
                    env=ANY,
                    check=False,
                ),
                call(
                    [
                        "rpm-lockfile-prototype",
                        "rpms.in.yaml",
                        "--outfile",
                        Path("rpms.lock.yaml"),
                    ],
                    env=ANY,
                    check=False,
                ),
            ],
        )


def test_update_lockfiles_creates_and_cleans_up_dnf_cache_dir():
    upgrades = [Upgrade(package_file="Dockerfile")]
    input_file_map = {"Dockerfile": ["rpms.in.yaml"]}

    fake_cache_dir = "/fake/dnf-cache"
    temporary_directory_mock = MagicMock()
    temporary_directory_mock.__enter__.return_value = fake_cache_dir

    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop(RPM_LOCKFILE_PROTOTYPE_DNF_CACHE, None)

        created_cache_dirs = []

        def fake_run(*_args, **kwargs):
            created_cache_dirs.append(kwargs["env"][RPM_LOCKFILE_PROTOTYPE_DNF_CACHE])
            return CompletedProcess("", 0)

        with (
            patch("refresh_rpm_lockfiles.subprocess.run", side_effect=fake_run),
            patch(
                "refresh_rpm_lockfiles.tempfile.TemporaryDirectory",
                return_value=temporary_directory_mock,
            ) as temporary_directory_class_mock,
        ):
            assert update_lockfiles(upgrades, input_file_map) is False

        temporary_directory_class_mock.assert_called_once_with(ignore_cleanup_errors=True)
        temporary_directory_mock.__exit__.assert_called_once()
        assert RPM_LOCKFILE_PROTOTYPE_DNF_CACHE not in os.environ
        assert created_cache_dirs == [fake_cache_dir]


def test_update_lockfiles_skips_dnf_cache_dir_when_no_matching_upgrades():
    upgrades = [Upgrade(package_file="unrelated/Dockerfile")]
    input_file_map = {"Dockerfile": ["rpms.in.yaml"]}

    with (
        patch.dict(os.environ, {}, clear=False),
        patch("refresh_rpm_lockfiles.subprocess.run") as subprocess_run_mock,
        patch("refresh_rpm_lockfiles.tempfile.TemporaryDirectory") as temporary_directory_mock,
    ):
        os.environ.pop(RPM_LOCKFILE_PROTOTYPE_DNF_CACHE, None)

        assert update_lockfiles(upgrades, input_file_map) is False

        subprocess_run_mock.assert_not_called()
        temporary_directory_mock.assert_not_called()


def test_update_lockfiles_reuses_existing_dnf_cache_dir():
    upgrades = [
        Upgrade(package_file="subfolder/Containerfile"),
        Upgrade(package_file="Dockerfile"),
    ]
    input_file_map = {
        "subfolder/Containerfile": ["subfolder/rpms.in.yaml"],
        "Dockerfile": ["rpms.in.yaml"],
    }

    with patch.dict(os.environ, {RPM_LOCKFILE_PROTOTYPE_DNF_CACHE: "/pre/existing/cache"}):
        with patch(
            "refresh_rpm_lockfiles.subprocess.run",
            side_effect=[CompletedProcess("", 0), CompletedProcess("", 0)],
        ) as subprocess_run_mock:
            assert update_lockfiles(upgrades, input_file_map) is False

            for recorded_call in subprocess_run_mock.call_args_list:
                assert (
                    recorded_call.kwargs["env"][RPM_LOCKFILE_PROTOTYPE_DNF_CACHE]
                    == "/pre/existing/cache"
                )

        assert os.environ[RPM_LOCKFILE_PROTOTYPE_DNF_CACHE] == "/pre/existing/cache"
