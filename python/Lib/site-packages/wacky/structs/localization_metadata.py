from dataclasses import dataclass
from enum import IntEnum
from typing import List, Type, Union

from construct import LazyBound, PrefixedArray, Switch
from construct_typed import DataclassMixin, DataclassStruct, csfield

from wacky.basic_types.integers import i32, u32
from wacky.basic_types.large_bool import LargeBool
from wacky.basic_types.string import String
from wacky.enums.adapter import enum_adapter


class ValueType(IntEnum):
    NONE = 0
    BOOLEAN = 1
    STRING = 2
    ARRAY = 3
    OBJECT = 4


ValueTypeStruct = enum_adapter(i32, ValueType)


@dataclass
class LocMetadataValue(DataclassMixin):
    value_type: ValueType = csfield(ValueTypeStruct)
    value: Union[bool, str, List["LocMetadataValue"]] = csfield(
        Switch(
            lambda this: this.value_type,
            {
                ValueType.BOOLEAN: LargeBool,
                ValueType.STRING: String,
                ValueType.ARRAY: PrefixedArray(u32, LazyBound(get_loc_metadata_value)),
                # ValueType.OBJECT: Error  # LazyBound(lambda: LocMetadataObject),
            },
            # default=Error,
        )
    )


def get_loc_metadata_value() -> Type[DataclassMixin]:
    return LocMetadataValue


@dataclass
class LocMetadataEntry(DataclassMixin):
    key: str = csfield(String)
    value: LocMetadataValue = csfield(DataclassStruct(LocMetadataValue))


LocMetadataObject = PrefixedArray(u32, DataclassStruct(LocMetadataEntry))


@dataclass
class TextSourceSiteContext(DataclassMixin):
    key_name: str = csfield(String)
    site_description: str = csfield(String)
    is_editor_only: bool = csfield(LargeBool)
    is_optional: bool = csfield(LargeBool)
    info_metadata: List[LocMetadataEntry] = csfield(LocMetadataObject)
    key_metadata: List[LocMetadataEntry] = csfield(LocMetadataObject)


@dataclass
class GatherableText(DataclassMixin):
    namespace_name: str = csfield(String)
    source_string: str = csfield(String)
    source_string_metadata: List[LocMetadataEntry] = csfield(LocMetadataObject)
    source_site_contexts: List[TextSourceSiteContext] = csfield(
        PrefixedArray(u32, DataclassStruct(TextSourceSiteContext))
    )
