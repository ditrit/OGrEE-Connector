import os
import sys
import common.Api as Api
import logging
import json
import argparse
from os.path import exists

log = logging.getLogger(__name__)
log.addHandler(logging.StreamHandler())


def ReadEnv(pathToEnvFile: str) -> tuple[str, dict[str, str], str]:
    """Read information in the env.json to setup API request. Returns url, token, headers and endpoint for the API."""
    file_exists = exists(pathToEnvFile)
    if file_exists:
        f = open(pathToEnvFile, "r")
        data = json.load(f)
        url = data["api_url"]
        f.close()
        return url
    else:
        log.error("Cannot find .env.json file in the root")
        sys.exit()


def Serial(location: str):
    pathToEnvFile = f"{os.path.dirname(__file__)}/.env.json"
    url = ReadEnv(pathToEnvFile)
    payload = {
        "columns": [
            {"name": "tiMultiField", "filter": {"contains": location}},
        ],
        "selectedColumns": [
            {"name": "cmbCabinet"},
            {"name": "tiName"},
            {"name": "tiAlias"},
            {"name": "cmbLocation"},
            {"name": "cmbChassis"},
            {"name": "tiSerialNumber"},
        ],
    }
    result = Api.PostRequest(
        url, {"Content-Type": "application/json"}, "api/v2/quicksearch/items", payload
    )["searchResults"]["items"]
    
    outPath = f"{os.path.dirname(os.path.realpath(__file__))}/out/"
    with open(f"{outPath}serial.ocli", "w") as newTemplate:
        for item in result:
            if "tiSerialNumber" not in item.keys():
                continue

            if "tiAlias" in item.keys():
                item["tiName"] = item["tiAlias"]

            site, room = item["cmbLocation"].split(" > ")
            string = f"EDF.{site}.BI2.{room}"

            if item["tiName"].startswith("NOEC") and item["tiName"][5] == "-":
                item["tiName"] = item["tiName"][6:]

            if "cmbCabinet" in item.keys() and item["cmbCabinet"] != item["tiName"]:
                if (
                    item["cmbCabinet"].startswith("NOEC")
                    and item["cmbCabinet"][5] == "-"
                ):
                    item["cmbCabinet"] = item["cmbCabinet"][6:]
                string += f".{item['cmbCabinet']}"

            if "cmbChassis" in item.keys() and item["cmbChassis"] != item["tiName"]:
                string += f".{item['cmbChassis']}"

            string += f".{item['tiName']}:serial={item['tiSerialNumber']}"
            newTemplate.write(string + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Return OGrEE commands to set serial number"
    )
    parser.add_argument(
        "--location",
        help="""which location to check (support wild card at start or end of string)""",
        required=True,
    )
    args = vars(parser.parse_args())
    Serial(args["location"])
