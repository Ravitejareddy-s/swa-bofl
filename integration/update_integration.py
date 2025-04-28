"""Update integration."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import requests
import urllib3
import urllib3.exceptions
import yaml

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

NEXUS_URL = "https://nexus-tools.swacorp.com"
GROUP_ID = "com.swacorp.ccplat"
REPO_ID = "releases"


def update_versions(yml_file: Path) -> dict[str, Any]:
    """Update versions."""
    data = yaml.safe_load(yml_file.read_bytes())
    if "modules" in data:
        update_module_versions(data["modules"], data, "modules")
    elif "stages" in data:
        stages = data["stages"]
        for index, stage in enumerate(stages):
            update_module_versions(stage["modules"], data, "stages", index)

    yml_file.write_text(yaml.safe_dump(data))

    return data


def update_module_versions(
    modules: dict[str, dict[str, Any]], data: dict[str, Any], key: str, index: int = 0
) -> None:
    """Update versions of each module."""
    for title, module_def in modules.items():
        module_name = module_def["name"]
        module_version = module_def["version"]
        module_group_id = module_def.get("groupId", "cloudCatalog")
        if module_version != "local":
            url = (
                f"{NEXUS_URL}/service/rest/v1/search?repository={REPO_ID}&"
                f"group={GROUP_ID}.{module_group_id}&name={module_name}&sort=version"
            )
            versions = [
                item["version"]
                for item in json.loads(
                    requests.get(url, timeout=900, verify=False).text  # noqa: S501
                )["items"]
            ]

            latest_version = (
                versions[0]
                if versions
                else get_latest_version_nexus2(module_group_id, module_name)
            )

            if latest_version != module_version:
                # replace module version with latest
                if key == "modules":
                    data["modules"][title]["version"] = latest_version
                elif key == "stages":
                    data["stages"][index]["modules"][title]["version"] = latest_version


def get_latest_version_nexus2(
    module_group_id: str, module_name: str
) -> str:  # cov: ignore
    """Lookup latest version in nexus2."""
    url = (
        # cspell: disable-next-line
        f"{NEXUS_URL}/CCPLAT/service/local/lucene/search?g={GROUP_ID}.{module_group_id}"
        f"&a={module_name}&p=zip&repositoryId=DEV"
    )
    # parse latest version
    result = re.search(
        r"(<latestRelease>)([\d.]*)(<\/latestRelease>)",
        requests.get(url, timeout=900, verify=False).text,  # noqa: S501
    )
    if result:
        return result.group(2)
    raise ValueError("latest version can't be determined")


if __name__ == "__main__":
    main_files = []
    if Path("deployments").exists():
        main_files = [
            f for f in os.listdir("deployments") if re.match(r"[0-9]*-main.yml", f)
        ]
    for main_file in main_files:
        update_versions(Path("deployments") / main_file)

    pre_deploy_main_files = []
    if Path("pre-deployments/deployments").exists():
        pre_deploy_main_files = [
            f
            for f in os.listdir("pre-deployments/deployments")
            if re.match(r"[0-9]*-main.yml", f)
        ]
    for main_file in pre_deploy_main_files:
        update_versions(Path("pre-deployments/deployments") / main_file)
