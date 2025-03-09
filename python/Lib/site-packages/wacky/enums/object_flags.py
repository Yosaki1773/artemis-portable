from enum import IntFlag

from wacky.basic_types.integers import u32
from wacky.enums.adapter import enum_adapter


class ObjectFlag(IntFlag):

    NoFlags = 0x00000000

    Public = 0x00000001
    Standalone = 0x00000002
    MarkAsNative = 0x00000004

    Transactional = 0x00000008
    ClassDefaultObject = 0x00000010
    ArchetypeObject = 0x00000020
    Transient = 0x00000040

    MarkAsRootSet = 0x00000080

    TagGarbageTemp = 0x00000100

    NeedInitialization = 0x00000200
    NeedLoad = 0x00000400
    KeepForCooker = 0x00000800
    NeedPostLoad = 0x00001000
    NeedPostLoadSubobjects = 0x00002000
    NewerVersionExists = 0x00004000
    BeginDestroyed = 0x00008000
    FinishDestroyed = 0x00010000

    # Misc. Flags
    BeingRegenerated = 0x00020000
    DefaultSubObject = 0x00040000
    WasLoaded = 0x00080000
    TextExportTransient = 0x00100000
    LoadCompleted = 0x00200000
    InheritableComponentTemplate = 0x00400000
    DuplicateTransient = 0x00800000
    StrongRefOnFrame = 0x01000000
    NonPIEDuplicateTransient = 0x02000000
    Dynamic = 0x04000000
    WillBeLoaded = 0x08000000
    HasExternalPackage = 0x10000000

    # Extras
    Load = (
        Public
        or Standalone
        or Transactional
        or ClassDefaultObject
        or ArchetypeObject
        or DefaultSubObject
        or TextExportTransient
        or InheritableComponentTemplate
        or DuplicateTransient
        or NonPIEDuplicateTransient
    )

    PropagateToSubObjects = Public | ArchetypeObject | Transactional | Transient


ObjectFlagStruct = enum_adapter(u32, ObjectFlag)
