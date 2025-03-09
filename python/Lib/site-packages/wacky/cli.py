import json
from typing import BinaryIO, TextIO

import click
from ruamel.yaml import YAML

from wacky import dump, jsonify, update


@click.group()
def main() -> None:
    ...


@main.command()
@click.argument("uasset", type=click.File(mode="rb"))
@click.argument("uexp", type=click.File(mode="rb"))
@click.option("--json", "use_json", is_flag=True, help="Output json instead of yaml")
@click.option(
    "-o", "--output", type=click.File(mode="w", encoding="utf-8"), default="-"
)
def unpack(uasset: BinaryIO, uexp: BinaryIO, output: TextIO, use_json: bool) -> None:
    """Convert the file to a more human friendly format"""
    jsonified = jsonify(uasset, uexp)
    if use_json:
        json.dump(jsonified, output, indent=4, ensure_ascii=False)
    else:
        yaml = YAML()
        yaml.dump(jsonified, output)


@main.command()
@click.argument("src_uasset", type=click.File(mode="rb"))
@click.argument("src_uexp", type=click.File(mode="rb"))
@click.argument("new_data", type=click.File(mode="r", encoding="utf-8"))
@click.argument("dst_uasset", type=click.File(mode="wb"))
@click.argument("dst_uexp", type=click.File(mode="wb"))
def repack(
    src_uasset: BinaryIO,
    src_uexp: BinaryIO,
    new_data: TextIO,
    dst_uasset: BinaryIO,
    dst_uexp: BinaryIO,
) -> None:
    """Create new modified .uasset and .uexp files by using SRC_UASSET and
    SRC_UEXP as templates and applying the changes specified by NEW_DATA"""
    yaml = YAML(typ="safe")
    changes = yaml.load(new_data)
    package = update(src_uasset, src_uexp, changes)
    dump(package, dst_uasset, dst_uexp)


if __name__ == "__main__":
    main()
