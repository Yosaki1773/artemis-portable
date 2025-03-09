from typing import BinaryIO

from wacky.package import Package, PackageStruct


def load(uasset: BinaryIO, uexp: BinaryIO) -> Package:
    bytes_ = uasset.read() + uexp.read()
    return PackageStruct.parse(bytes_)


def dump(package: Package, uasset: BinaryIO, uexp: BinaryIO) -> None:
    """Dump package to uasset and uexp"""
    bytes_with_wrong_offsets = PackageStruct.build(package)
    reparsed = PackageStruct.parse(bytes_with_wrong_offsets)
    reparsed.fix_offsets_and_sizes()
    bytes_ = PackageStruct.build(reparsed)

    uasset_bytes = bytes_[: package.total_header_size]
    uexp_bytes = bytes_[package.total_header_size :]
    uasset.write(uasset_bytes)
    uexp.write(uexp_bytes)


def jsonify(uasset: BinaryIO, uexp: BinaryIO) -> list:
    package = load(uasset=uasset, uexp=uexp)
    return package.jsonify()


def update(uasset: BinaryIO, uexp: BinaryIO, changes: list) -> Package:
    package = load(uasset=uasset, uexp=uexp)
    package.update(changes)
    return package
