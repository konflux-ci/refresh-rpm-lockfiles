"""A post upgrade task script to update all RPM lockfiles based on container file updates."""

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from loguru import logger
from yaml import safe_load


@dataclass
class Upgrade:
    """Container class for the upgrades."""

    package_file: str


type InputFileMap = dict[str, str]


def find_rpm_input_files_in_repo() -> InputFileMap:
    """Get a map between container file."""
    input_file_map: InputFileMap = {}

    for path, _, files in Path.cwd().walk():
        for file in files:
            if file == "rpms.in.yaml":
                input_file = str(path / file).removeprefix(str(Path.cwd())).removeprefix("/")
                logger.debug("Found rpms.in.yaml in: {}", input_file)

                with (Path(path) / file).open() as f:
                    data = safe_load(f)
                    containerfile = data.get("context", {}).get("containerfile", None)

                    if isinstance(containerfile, dict):
                        containerfile = containerfile["file"]

                    if containerfile is None:
                        # Find a sibling
                        logger.debug(
                            "No context.containerfile provided, looking for siblings",
                        )
                        containerfile = Path(input_file).parent / "Dockerfile"

                        if not containerfile.exists():
                            logger.debug(
                                "Sibling Dockerfile not found, trying Containerfile",
                            )
                            containerfile = Path(input_file).parent / "Containerfile"

                            if not containerfile.exists():
                                logger.error(
                                    "Neither Dockerfile nor Containerfile found"
                                    " while context.containerfile is not set",
                                )
                                continue
                    else:
                        containerfile = Path(input_file).parent / containerfile

                        if not containerfile.exists():
                            logger.error(
                                "context.containerfile provided, but file not found: {}",
                                containerfile,
                            )
                            continue

                    logger.debug("Input file detected: {}", containerfile)

                    input_file_map[str(containerfile)] = input_file

    return input_file_map


def read_upgrades_from_file(path: Path) -> list[Upgrade]:
    """Read the upgrade file and return the upgrades."""
    with Path(path).open() as f:
        return [Upgrade(package_file=upgrade["packageFile"]) for upgrade in json.load(f)]


def update_lockfiles(upgrades: list[Upgrade], input_file_map: InputFileMap) -> bool:
    """Call rpm-lockfile-prototype for each upgrade."""
    logger.debug(str(upgrades))
    logger.debug("Input file map: {}", input_file_map)

    # If any of the upgrades fail, pass that information up,
    # but try to upgrade as many files as possible
    any_failed = False

    for upgrade in upgrades:
        if upgrade.package_file in input_file_map:
            # The opposite should not happen, i.e. if a file is in the repo,
            # it may have an upgrade, but there shouldn't be an upgrade to a file
            # that's not in the repo.
            input_file = input_file_map[upgrade.package_file]

            # Output path needs to be specified using the same relative directory
            output_file = Path(input_file).parent / "rpms.lock.yaml"

            logger.info("Running rpm-lockfile-prototype for {}", input_file)
            logger.debug(
                "Executing `rpm-lockfile-prototype {} --outfile {}`",
                input_file,
                output_file,
            )

            ret = subprocess.run(  # noqa: S603
                ["rpm-lockfile-prototype", input_file, "--outfile", output_file],  # noqa: S607
                check=True,
            )

            if ret.returncode:
                logger.error("Execution failed for {}", input_file)
                any_failed = True

    return any_failed


def run() -> int:  # pragma: no cover
    """Application entrypoint."""
    logger.remove()
    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | <level>{level:8s}</level> | {message}",
        level=os.getenv("LOG_LEVEL", "DEBUG").upper(),
        colorize=True,
    )

    parser = argparse.ArgumentParser()
    parser.add_argument("--file", "-f", type=str)

    logger.debug("cwd: {}", Path.cwd())

    args = parser.parse_args()

    upgrades = read_upgrades_from_file(args.file)
    input_file_map = find_rpm_input_files_in_repo()

    return int(update_lockfiles(upgrades, input_file_map))


if __name__ == "__main__":  # pragma: no cover
    run()
