# refresh-rpm-lockfiles

`refresh-rpm-lockfiles` is a script meant to be run as a postUpgradeTask
in Renovate after a Dockerfile/Container is update to a newer base image version.
The script will refresh all associated RPM lockfiles using [rpm-lockfile-prototype](https://github.com/konflux-ci/rpm-lockfile-prototype).

## Configuration

### Using presets

Using the [MintMaker presets](https://github.com/konflux-ci/mintmaker-presets), this will enable RPM lockfile updates
for **all** Dockerfile or Containerfile updates.

```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": [
    "github>konflux-ci/mintmaker-presets:group-python-requirements"
  ]
}
```

### Manual

Add a packageRule with any required matching rules, but keep the `postUpgradeTask`
configuration intact. This allows for fine-grained updates, e.g. only for
some files, but not others.

```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "packageRules": [
    {
      "matchManagers": [
        "dockerfile"
      ],
      "postUpgradeTasks": {
        "commands": [
          "refresh-rpm-lockfiles -f \"$RENOVATE_POST_UPGRADE_COMMAND_DATA_FILE\""
        ],
        "fileFilters": [
          "**/rpms.lock.yaml"
        ],
        "executionMode": "branch",
        "dataFileTemplate": "[{{#each upgrades}}{\"packageFile\": \"{{{packageFile}}}\"}{{#unless @last}},{{\/unless}}{{\/each}}]"
      }
    }
  ]
}
```
