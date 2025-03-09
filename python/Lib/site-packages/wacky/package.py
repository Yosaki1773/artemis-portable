from collections import ChainMap, UserString
from dataclasses import dataclass
from typing import List, Optional, TypeVar, Union
from uuid import UUID

from construct import (
    Adapter,
    Array,
    Bytes,
    Check,
    Computed,
    Const,
    Container,
    Error,
    Flag,
    If,
    IfThenElse,
    LazyBound,
    PrefixedArray,
    Rebuild,
    RepeatUntil,
    Switch,
    Tell,
    this,
)
from construct_typed import DataclassMixin, DataclassStruct, csfield

from wacky.basic_types.floats import f32, f64
from wacky.basic_types.guid import GUIDStruct
from wacky.basic_types.integers import i8, i16, i32, i64, u16, u32, u64
from wacky.basic_types.large_bool import LargeBool
from wacky.basic_types.package_index import IndexKind, PackageIndex, PackageIndexStruct
from wacky.basic_types.string import String
from wacky.enums.compression_flags import CompressionFlag, CompressionFlagStruct
from wacky.enums.object_flags import ObjectFlag, ObjectFlagStruct
from wacky.enums.package_flags import PackageFlag, PackageFlagStruct
from wacky.enums.ue4_version import UE4Version
from wacky.hashing.strings import crc32_string_hash, deprecated_string_hash

# from wacky.structs.localization_metadata import GatherableText


@dataclass
class CustomVersion(DataclassMixin):
    key: UUID = csfield(GUIDStruct)
    version: int = csfield(i32)


@dataclass
class Generation(DataclassMixin):
    num_export: int = csfield(u32)
    num_names: int = csfield(u32)


@dataclass
class Version(DataclassMixin):
    major: int = csfield(u16)
    minor: int = csfield(u16)
    patch: int = csfield(u16)
    changelist: int = csfield(u32)
    branch: str = csfield(String)


VersionStruct = DataclassStruct(Version)


@dataclass
class CompressedChunk(DataclassMixin):
    len_compressed: int = csfield(u32)
    ofs_compressed: int = csfield(u32)
    len_uncompressed: int = csfield(u32)
    ofs_uncompressed: int = csfield(u32)


@dataclass
class RawName(DataclassMixin):
    value: str = csfield(String)
    non_case_preserving_hash: Optional[int] = csfield(
        If(
            lambda this: this._root.file_version_ue4
            < UE4Version.NAME_HASHES_SERIALIZED,
            Rebuild(u16, lambda this: deprecated_string_hash(this.value) & 0xFFFF),
        )
    )
    case_preserving_hash: Optional[int] = csfield(
        If(
            lambda this: this._root.file_version_ue4
            < UE4Version.NAME_HASHES_SERIALIZED,
            Rebuild(u16, lambda this: crc32_string_hash(this.value) & 0xFFFF),
        )
    )


class NameAdapter(Adapter):
    def _decode(self, obj: RawName, context, path: str) -> str:
        return obj.value

    def _encode(self, obj: str, context, path) -> RawName:
        return RawName(value=obj)


Name = NameAdapter(DataclassStruct(RawName))


@dataclass
class RawNameReference(DataclassMixin):
    index: int = csfield(u32)
    number: int = csfield(u32)


class ReferencedName(UserString):
    def __init__(self, seq: str, original_reference: RawNameReference):
        super().__init__(seq)
        self.original_reference = original_reference


class NameReferenceAdapter(Adapter):
    def _decode(self, obj: RawNameReference, context, path) -> ReferencedName:
        return ReferencedName(
            context._root.names[obj.index],
            obj,
        )

    def _encode(self, obj: ReferencedName, context, path) -> RawNameReference:
        return obj.original_reference


NameReference = NameReferenceAdapter(DataclassStruct(RawNameReference))


@dataclass
class ImportEntry(DataclassMixin):
    class_package: str = csfield(NameReference)
    class_name: str = csfield(NameReference)
    outer_index: PackageIndex = csfield(PackageIndexStruct)
    object_name: str = csfield(NameReference)


@dataclass
class ExportEntry(DataclassMixin):
    class_index: PackageIndex = csfield(PackageIndexStruct)
    super_index: PackageIndex = csfield(PackageIndexStruct)
    template_index: PackageIndex = csfield(PackageIndexStruct)
    outer_index: PackageIndex = csfield(PackageIndexStruct)
    object_name: str = csfield(NameReference)
    object_flags: ObjectFlag = csfield(ObjectFlagStruct)
    len_serial: int = csfield(u64)
    ofs_serial: int = csfield(u64)
    forced_export: bool = csfield(LargeBool)
    not_for_client: bool = csfield(LargeBool)
    not_for_server: bool = csfield(LargeBool)
    package_guid: UUID = csfield(GUIDStruct)
    package_flags: PackageFlag = csfield(PackageFlagStruct)
    not_always_loaded_for_editor_game: bool = csfield(LargeBool)
    is_asset: bool = csfield(LargeBool)
    first_export_dependency: int = csfield(i32)
    num_serialization_before_serialization_dependencies: int = csfield(u32)
    num_create_before_serialization_dependencies: int = csfield(u32)
    num_serialization_before_create_dependencies: int = csfield(u32)
    num_create_before_create_dependencies: int = csfield(u32)


@dataclass
class PreloadDependencies(DataclassMixin):
    export_map_entry: ExportEntry = csfield(
        Computed(lambda this: this._root.exports_map[this._._index])
    )
    serialization_before_serialization_dependencies: List[PackageIndex] = csfield(
        Array(
            lambda this: this.export_map_entry.num_serialization_before_serialization_dependencies,
            PackageIndexStruct,
        )
    )
    create_before_serialization_dependencies: List[PackageIndex] = csfield(
        Array(
            lambda this: this.export_map_entry.num_create_before_serialization_dependencies,
            PackageIndexStruct,
        )
    )
    serialization_before_create_dependencies: List[PackageIndex] = csfield(
        Array(
            lambda this: this.export_map_entry.num_serialization_before_create_dependencies,
            PackageIndexStruct,
        )
    )
    create_before_create_dependencies: List[PackageIndex] = csfield(
        Array(
            lambda this: this.export_map_entry.num_create_before_create_dependencies,
            PackageIndexStruct,
        )
    )


@dataclass
class MapTag(DataclassMixin):
    key_type: str = csfield(NameReference)
    value_type: str = csfield(NameReference)


@dataclass
class StructTag(DataclassMixin):
    name: str = csfield(NameReference)
    guid: UUID = csfield(GUIDStruct)


TagValue = Union[
    bool,
    str,
    StructTag,
    MapTag,
]


@dataclass
class Tag(DataclassMixin):
    name: str = csfield(NameReference)
    type_: Optional[str] = csfield(
        If(
            lambda this: this.name != "None",
            NameReference,
        )
    )
    size: Optional[int] = csfield(
        If(
            lambda this: this.name != "None",
            i32,
        )
    )
    array_index: Optional[int] = csfield(
        If(
            lambda this: this.name != "None",
            i32,
        )
    )
    value: Optional[TagValue] = csfield(
        If(
            lambda this: this.name != "None",
            Switch(
                lambda this: this.type_,
                {
                    "BoolProperty": Bytes(1),
                    "ByteProperty": NameReference,
                    "EnumProperty": NameReference,
                    "ArrayProperty": NameReference,
                    "SetProperty": NameReference,
                    "MapProperty": DataclassStruct(MapTag),
                    "StructProperty": DataclassStruct(StructTag),
                },
            ),
        )
    )
    has_guid_next: Optional[bool] = csfield(
        If(
            lambda this: this.name != "None",
            Flag,
        )
    )
    guid: Optional[UUID] = csfield(
        If(
            lambda this: this.name != "None" and this.has_guid_next,
            GUIDStruct,
        )
    )


TagStruct = DataclassStruct(Tag)

Value = Union[bytes, bool, int, float, PackageIndex, str, UUID]

NORMAL_VALUE_SWITCH = {
    "ByteProperty": IfThenElse(
        lambda this: this.tag.value == "None",
        Bytes(1),
        NameReference,
    ),
    "BoolProperty": IfThenElse(
        lambda this: not this._root.package_flags & PackageFlag.UnversionedProperties,
        Computed(lambda this: this.tag.value),
        Bytes(1),
    ),
    "IntProperty": i32,
    "FloatProperty": f32,
    "ObjectProperty": PackageIndexStruct,
    "NameProperty": NameReference,
    "DelegateProperty": NameReference,
    "DoubleProperty": f64,
    "ArrayProperty": LazyBound(lambda: DataclassStruct(UArray)),
    # "StructProperty": struct_property # Unused by the DataTable file
    "StrProperty": String,
    # "TextProperty": # TODO
    # "LazyObjectProperty": # TODO
    # "SoftObjectProperty": # TODO
    # "AssetObjectProperty": # TODO
    "UInt64Property": u64,
    "UInt32Property": u32,
    "UInt16Property": u16,
    "Int64Property": i64,
    "Int16Property": i16,
    "Int8Property": i8,
    # "MapProperty": # TODO
    # "SetProperty": # TODO
    "EnumProperty": NameReference,
    "Guid": GUIDStruct,
}

ARRAY_VALUE_SWITCH = ChainMap({"BoolProperty": Bytes(1)}, NORMAL_VALUE_SWITCH)

JSONIFIERS = {
    "ByteProperty": (
        lambda val: str(val)
        if isinstance(val, ReferencedName)
        else int.from_bytes(val, "little")
    ),
    "BoolProperty": (lambda val: bool(val[0]) if isinstance(val, bytes) else bool(val)),
    "IntProperty": int,
    "FloatProperty": float,
    "ObjectProperty": PackageIndex.jsonify,
    "NameProperty": str,
    "DelegateProperty": str,
    "DoubleProperty": float,
    "ArrayProperty": lambda val: val.jsonify(),
    # "StructProperty": struct_property # Unused by the DataTable file
    "StrProperty": str,
    # "TextProperty": # TODO
    # "LazyObjectProperty": # TODO
    # "SoftObjectProperty": # TODO
    # "AssetObjectProperty": # TODO
    "UInt64Property": int,
    "UInt32Property": int,
    "UInt16Property": int,
    "Int64Property": int,
    "Int16Property": int,
    "Int8Property": int,
    # "MapProperty": # TODO
    # "SetProperty": # TODO
    "EnumProperty": str,
    "Guid": str,
}

COMPATIBLE_TYPES = {
    "ByteProperty": [str, int],
    "BoolProperty": [bool],
    "IntProperty": [int],
    "FloatProperty": [float],
    "ObjectProperty": [int],
    "NameProperty": [str],
    "DelegateProperty": [str],
    "DoubleProperty": [float],
    "ArrayProperty": [list],
    # "StructProperty": struct_property # Unused by the DataTable file
    "StrProperty": [str],
    # "TextProperty": # TODO
    # "LazyObjectProperty": # TODO
    # "SoftObjectProperty": # TODO
    # "AssetObjectProperty": # TODO
    "UInt64Property": [int],
    "UInt32Property": [int],
    "UInt16Property": [int],
    "Int64Property": [int],
    "Int16Property": [int],
    "Int8Property": [int],
    # "MapProperty": # TODO
    # "SetProperty": # TODO
    "EnumProperty": [str],
    "Guid": [str],
}

T = TypeVar("T")


def new_if_different(original: T, new: T) -> T:
    if original != new:
        return new
    else:
        return original


def update_byte_property(original: Union[ReferencedName, int], new: Union[str, int]):
    if isinstance(original, ReferencedName):
        if not isinstance(new, str):
            raise ValueError(
                f"Invalid type to update name reference : {new!r} should be a string"
            )
        return update_name_reference(original, new)
    else:
        if type(new) != int:
            raise ValueError(
                f"Invalid type to update byte property : {new!r} should be an int"
            )
        return new_if_different(original, bytes([new]))


def update_bool_property(original: bytes, new: bool) -> bytes:
    if bool(original[0]) == new:
        return original
    else:
        return bytes([new])


def update_package_index(original: PackageIndex, new: int) -> PackageIndex:
    original.update(new)
    return original


def update_array_property(original: "UArray", new: list) -> "UArray":
    original.update(new)
    return original


def update_name_reference(original: ReferencedName, new: str) -> ReferencedName:
    if original != new:
        raise ValueError(
            f"{original!r} is a name reference, updating name references is not supported yet"
        )
    return original


def update_guid(original: UUID, new: str):
    return new_if_different(original, UUID(new))


SPECIAL_UPDATERS = {
    "ByteProperty": update_byte_property,
    "BoolProperty": update_bool_property,
    "ObjectProperty": update_package_index,
    "NameProperty": update_name_reference,
    "DelegateProperty": update_name_reference,
    "ArrayProperty": update_array_property,
    "EnumProperty": update_name_reference,
    "Guid": update_guid,
}


@dataclass
class UArray(DataclassMixin):
    num_items: int = csfield(u32)
    tag: Optional[Tag] = csfield(
        If(
            lambda this: this._.tag.value in ["StructProperty", "ArrayProperty"],
            TagStruct,
        )
    )
    value_type: str = csfield(Computed(this._.tag.value))
    values: List[Value] = csfield(
        Array(
            lambda this: this.num_items,
            Switch(
                lambda this: this.value_type,
                ARRAY_VALUE_SWITCH,
                default=Error,
            ),
        )
    )

    def jsonify(self) -> list:
        return [JSONIFIERS[self.value_type](val) for val in self.values]

    def update(self, new: list):
        raise ValueError("Updating arrays is not yet supported")


@dataclass
class Property(DataclassMixin):
    tag: Tag = csfield(TagStruct)
    value: Optional[Value] = csfield(
        If(
            lambda this: this.tag.name != "None",
            Switch(
                lambda this: this.tag.type_,
                NORMAL_VALUE_SWITCH,
            ),
        )
    )

    def jsonify(self) -> tuple:
        jsonifier = JSONIFIERS.get(self.tag.type_)
        if jsonifier is not None:
            return (str(self.tag.name), jsonifier(self.value))
        else:
            return (str(self.tag.name), None)

    def update(self, change: Value) -> None:
        compatible_types = COMPATIBLE_TYPES.get(self.tag.type_)
        if compatible_types is None:
            if change is None:
                return
            else:
                raise ValueError(
                    f"Invalid value for property {self.tag.name} : "
                    f"should be null but found {change!r}"
                )

        # Can't use isinstance here because bool is a subclass of int
        if type(change) not in compatible_types:
            raise ValueError(
                f"Invalid value for property {self.tag.name} : "
                f"{change!r} is not of type {' or '.join(t.__name__ for t in compatible_types)}"
            )

        special_updater = SPECIAL_UPDATERS.get(self.tag.type_)
        if special_updater is None:
            if self.value != change:
                self.value = change
        else:
            self.value = special_updater(self.value, change)


PropertyStruct = DataclassStruct(Property)
PropertyList = RepeatUntil(
    lambda prop, lst, ctx: prop.tag.name == "None",
    PropertyStruct,
)


@dataclass
class Row(DataclassMixin):
    name: str = csfield(NameReference)
    properties: List[Property] = csfield(PropertyList)

    def jsonify(self) -> tuple:
        return (str(self.name), dict(prop.jsonify() for prop in self.properties[:-1]))

    def update(self, changes: dict) -> None:
        original_props = {prop.tag.name: prop for prop in self.properties[:-1]}
        unknown_props = changes.keys() - original_props.keys()
        if unknown_props:
            raise ValueError(
                f"New data for row {self.name} has unknown properties : {unknown_props}"
            )

        for key, prop_changes in changes.items():
            original_props[key].update(prop_changes)


@dataclass
class DataTable(DataclassMixin):
    properties: List[Property] = csfield(PropertyList)
    has_guid_next: bool = csfield(LargeBool)
    guid: Optional[UUID] = csfield(
        If(
            lambda this: this.has_guid_next
            and not (this._.map_entry.object_flags & ObjectFlag.ClassDefaultObject),
            GUIDStruct,
        )
    )
    rows: List[Row] = csfield(PrefixedArray(u32, DataclassStruct(Row)))

    def jsonify(self) -> dict:
        return {
            "properties": dict(prop.jsonify() for prop in self.properties[:-1]),
            "rows": dict(row.jsonify() for row in self.rows),
        }

    def update(self, changes) -> None:
        original_props = {prop.tag.name: prop for prop in self.properties[:-1]}
        unknown_props = changes["properties"].keys() - original_props.keys()
        if unknown_props:
            raise ValueError(f"New data has unknown properties : {unknown_props}")

        for key, prop_changes in changes["properties"].items():
            original_props[key].update(prop_changes)

        original_rows = {row.name: row for row in self.rows}
        unknown_rows = changes["rows"].keys() - original_rows.keys()
        if unknown_rows:
            raise ValueError(f"New data has unknown rows : {unknown_rows}")

        for name, row_changes in changes["rows"].items():
            original_rows[name].update(row_changes)


def select_actual_type(this: Container) -> str:
    if this.map_entry.class_index.kind == IndexKind.NULL:
        return this.inline_type
    elif this.map_entry.class_index.kind == IndexKind.IMPORT:
        return this._root.imports_map[this.map_entry.class_index.value].object_name
    elif this.map_entry.super_index.kind == IndexKind.IMPORT:
        return this._root.imports_map[this.map_entry.super_index.kind].object_name
    else:
        return this._root.exports_map[this.map_entry.super_index.kind].object_name


@dataclass
class Export(DataclassMixin):
    map_entry: ExportEntry = csfield(
        Computed(lambda this: this._root.exports_map[this._._index])
    )
    computed_offset: int = csfield(Tell)
    inline_type: Optional[str] = csfield(
        If(
            lambda this: this.map_entry.class_index.kind == IndexKind.NULL,
            NameReference,
        )
    )
    type_: str = csfield(Computed(select_actual_type))
    _check_type_is_datatable: None = csfield(Check(this.type_ == "DataTable"))
    value: DataTable = csfield(DataclassStruct(DataTable))

    def jsonify(self) -> dict:
        return self.value.jsonify()

    def update(self, changes: dict) -> None:
        self.value.update(changes)


@dataclass
class Package(DataclassMixin):
    magic: bytes = csfield(Const(bytes([0xC1, 0x83, 0x2A, 0x9E])))
    legacy_file_version: int = csfield(i32)
    version_ue3: Optional[int] = csfield(If(this.legacy_file_version != -4, i32))
    file_version_ue4: int = csfield(i32)
    file_version_licensee_ue4: int = csfield(i32)
    custom_versions: Optional[List[CustomVersion]] = csfield(
        If(
            lambda this: this.legacy_file_version <= -2,
            PrefixedArray(u32, DataclassStruct(CustomVersion)),
        )
    )
    total_header_size: int = csfield(u32)
    folder_name: str = csfield(String)
    package_flags: PackageFlag = csfield(PackageFlagStruct)
    num_names: int = csfield(u32)
    ofs_names: int = csfield(u32)
    # localization_id: Optional[str] = csfield(If(
    #     lambda this: this.file_version_ue4 >= UE4Version.ADDED_PACKAGE_SUMMARY_LOCALIZATION_ID,
    #     String,
    # ))
    num_gatherable_text_data: Optional[int] = csfield(
        If(
            lambda this: this.file_version_ue4 >= UE4Version.SERIALIZE_TEXT_IN_PACKAGES
            or this.file_version_ue4 == 0,
            u32,
        )
    )
    ofs_gatherable_text_data: Optional[int] = csfield(
        If(
            lambda this: this.file_version_ue4 >= UE4Version.SERIALIZE_TEXT_IN_PACKAGES
            or this.file_version_ue4 == 0,
            Const(0, u32),
        )
    )
    num_exports: int = csfield(u32)
    ofs_exports_map: int = csfield(u32)
    num_imports: int = csfield(u32)
    ofs_imports_map: int = csfield(u32)
    ofs_depends_map: int = csfield(u32)
    num_soft_package_references: Optional[int] = csfield(
        If(
            lambda this: this.file_version_ue4
            >= UE4Version.ADD_STRING_ASSET_REFERENCES_MAP
            or this.file_version_ue4 == 0,
            u32,
        )
    )
    ofs_soft_package_references: Optional[int] = csfield(
        If(
            lambda this: this.file_version_ue4
            >= UE4Version.ADD_STRING_ASSET_REFERENCES_MAP
            or this.file_version_ue4 == 0,
            Const(0, u32),
        )
    )
    ofs_searchable_names: Optional[int] = csfield(
        If(
            lambda this: this.file_version_ue4 >= UE4Version.ADDED_SEARCHABLE_NAMES
            or this.file_version_ue4 == 0,
            Const(0, u32),
        )
    )
    ofs_thumbnail_table: int = csfield(Const(0, u32))
    guid: UUID = csfield(GUIDStruct)
    generations: List[Generation] = csfield(
        PrefixedArray(u32, DataclassStruct(Generation))
    )
    saved_by_engine_version: Optional[Version] = csfield(
        If(
            lambda this: this.file_version_ue4 >= UE4Version.ENGINE_VERSION_OBJECT
            or this.file_version_ue4 == 0,
            VersionStruct,
        )
    )
    compatible_with_engine_version: Optional[Version] = csfield(
        If(
            lambda this: this.file_version_ue4
            >= UE4Version.PACKAGE_SUMMARY_HAS_COMPATIBLE_ENGINE_VERSION
            or this.file_version_ue4 == 0,
            VersionStruct,
        )
    )
    compression_flags: CompressionFlag = csfield(CompressionFlagStruct)
    num_compressed_chunks: int = csfield(Const(0, u32))
    # compressed_chunks: List[CompressedChunk] = csfield(PrefixedArray(u32, DataclassStruct(CompressedChunk)))
    source: int = csfield(u32)
    additional_packages_to_cook: List[str] = csfield(PrefixedArray(u32, String))
    num_texture_allocations: Optional[int] = csfield(
        If(
            lambda this: this.legacy_file_version > -7,
            Const(0, u32),
        )
    )
    ofs_asset_registry: int = csfield(u32)
    ofs_bulk_data: int = csfield(u64)
    ofs_world_tile_info: int = csfield(Const(0, u32))
    chunk_ids: List[int] = csfield(PrefixedArray(u32, u32))
    num_preload_dependency: int = csfield(u32)
    ofs_preload_dependency: int = csfield(u32)
    computed_ofs_names: int = csfield(Tell)
    names: List[str] = csfield(Array(this.num_names, Name))
    computed_ofs_gatherable_text_data: int = csfield(Tell)
    # gatherable_text_data: Optional[List[GatherableText]] = csfield(If(
    #     lambda this: not this.package_flags & PackageFlag.FilterEditorOnly,
    #     Array(this.num_gatherable_text_data, DataclassStruct(GatherableText))
    # ))
    computed_ofs_imports_map: int = csfield(Tell)
    imports_map: List[ImportEntry] = csfield(
        Array(this.num_imports, DataclassStruct(ImportEntry))
    )
    computed_ofs_exports_map: int = csfield(Tell)
    exports_map: List[ExportEntry] = csfield(
        Array(this.num_exports, DataclassStruct(ExportEntry))
    )
    computed_ofs_depends_map: int = csfield(Tell)
    depends_map: List[List[int]] = csfield(
        Array(this.num_exports, PrefixedArray(u32, PackageIndexStruct))
    )
    computed_ofs_soft_package_references: int = csfield(Tell)
    # soft_references = ...
    computed_ofs_searchable_names: int = csfield(Tell)
    # searchable_names = ...
    computed_ofs_thumbnail_table: int = csfield(Tell)
    # thumbnails = ...
    computed_ofs_asset_registry: int = csfield(Tell)
    num_assets: int = csfield(Const(0, u32))
    # asset_registry: List[...] = csfield(PrefixedArray(...))
    computed_ofs_world_tile_info: int = csfield(Tell)
    # world_level_info = ...
    computed_ofs_preload_dependency: int = csfield(Tell)
    preload_dependencies: List[PreloadDependencies] = csfield(
        Array(this.num_exports, DataclassStruct(PreloadDependencies))
    )
    computed_total_header_size: int = csfield(Tell)
    exports: List[Export] = csfield(Array(this.num_exports, DataclassStruct(Export)))
    computed_ofs_after_last_export: int = csfield(Tell)
    computed_ofs_bulk_data: int = csfield(Tell)
    magic_at_the_end: bytes = csfield(Const(bytes([0xC1, 0x83, 0x2A, 0x9E])))

    def fix_offsets_and_sizes(self) -> None:
        self.total_header_size = self.computed_total_header_size

        # All the commented lines are for offsets that are hard-coded to zero
        # in the example file
        self.ofs_names = self.computed_ofs_names
        # self.ofs_gatherable_text_data = self.computed_ofs_gatherable_text_data
        self.ofs_exports_map = self.computed_ofs_exports_map
        self.ofs_imports_map = self.computed_ofs_imports_map
        self.ofs_depends_map = self.computed_ofs_depends_map
        # self.ofs_soft_package_references = self.computed_ofs_soft_package_references
        # self.ofs_searchable_names = self.computed_ofs_searchable_names
        # self.ofs_thumbnail_table = self.computed_ofs_thumbnail_table
        self.ofs_asset_registry = self.computed_ofs_asset_registry
        self.ofs_bulk_data = self.computed_ofs_bulk_data
        # self.ofs_world_tile_info = self.computed_ofs_world_tile_info
        self.ofs_preload_dependency = self.computed_ofs_preload_dependency

        if len(self.exports_map) != len(self.exports):
            raise ValueError("ExportsMap and Exports have different lengths")

        num_exports = len(self.exports)
        for i, (map_entry, export) in enumerate(zip(self.exports_map, self.exports)):
            map_entry.ofs_serial = export.computed_offset
            if i + 1 == num_exports:
                map_entry.len_serial = (
                    self.computed_ofs_after_last_export - export.computed_offset
                )
            else:
                map_entry.len_serial = (
                    self.exports[i + 1].computed_offset - export.computed_offset
                )

    def jsonify(self) -> list:
        return [export.jsonify() for export in self.exports]

    def update(self, new_data: list) -> None:
        if len(new_data) != len(self.exports):
            raise ValueError(
                "The new data doesn't have the same number of exports as the old one"
            )

        for changes, export in zip(new_data, self.exports):
            export.update(changes)


PackageStruct = DataclassStruct(Package)
