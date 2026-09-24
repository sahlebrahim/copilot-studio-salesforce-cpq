# prints salesforce field names in a form you can paste into agent instructions
# usage: python scripts/describe_fields.py --org cpq --objects Opportunity Account SBQQ__Quote__c(cpq quotes)

import argparse
import json
import shutil
import subprocess
import sys

# system fields nobody asks questions about
SYSTEM_FIELDS = {
    "IsDeleted", "CreatedById", "CreatedDate", "LastModifiedById",
    "LastModifiedDate", "SystemModstamp", "LastActivityDate",
    "LastViewedDate", "LastReferencedDate", "OwnerId",
}


def describe(sf, obj, org):
    result = subprocess.run(
        [sf, "sobject", "describe", "--sobject", obj, "--target-org", org, "--json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"warning: {obj} returned no readable output", file=sys.stderr)
        return None

    if data.get("status") != 0:
        print(f"warning: {obj} failed: {data.get('message')}", file=sys.stderr)
        return None

    return data["result"]


def print_object(obj, describe_result):
    fields = [
        f for f in describe_result["fields"]
        if not f["deprecatedAndHidden"] and f["name"] not in SYSTEM_FIELDS
    ]

    print()
    print(obj)
    print("  fields: " + ", ".join(f["name"] for f in fields))


    lookups = [
        f"{f['relationshipName']} -> {'/'.join(f['referenceTo'])}"
        for f in fields if f.get("relationshipName")
    ]
    if lookups:
        print("  lookups: " + ", ".join(lookups))

    children = [
        f"{c['relationshipName']} -> {c['childSObject']}"
        for c in describe_result["childRelationships"]
        if c.get("relationshipName") and c["childSObject"].endswith("__c")
    ]
    if children:
        print("  children: " + ", ".join(children))

    for f in fields:
        if f["type"] == "picklist":
            values = [p["value"] for p in f["picklistValues"] if p["active"]]
            if values:
                print(f"  {f['name']}: {', '.join(values)}")


def main():
    parser = argparse.ArgumentParser(description="print salesforce field names for agent instructions")
    parser.add_argument("--org", default="cpq", help="org alias, see: sf org list")
    parser.add_argument("--objects", nargs="+", default=["Opportunity", "Account"])
    args = parser.parse_args()

    # on windows sf is a .cmd shim, so resolve the full path first
    sf = shutil.which("sf")
    if not sf:
        sys.exit("sf cli not found. install it or add it to PATH")

    for obj in args.objects:
        result = describe(sf, obj, args.org)
        if result:
            print_object(obj, result)


if __name__ == "__main__":
    main()