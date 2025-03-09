from enum import IntFlag

from wacky.basic_types.integers import u32
from wacky.enums.adapter import enum_adapter


class PackageFlag(IntFlag):
    NewlyCreated = 0x00000001
    ClientOptional = 0x00000002
    ServerSideOnly = 0x00000004
    # Unused = 0x00000008
    CompiledIn = 0x00000010
    ForDiffing = 0x00000020
    EditorOnly = 0x00000040
    Developer = 0x00000080
    # Loaded only in uncooked builds (i.e. runtime in editor)
    UncookedOnly = 0x00000100
    Cooked = 0x00000200
    # Package doesn't contain any asset object (although asset tags can be
    # present)
    ContainsNoAsset = 0x00000400
    # Unused = 0x00000800
    # Unused = 0x00001000
    # Uses unversioned property serialization instead of versioned tagged
    # property serialization
    UnversionedProperties = 0x00002000
    # Contains map data (UObjects only referenced by a single ULevel) but is
    # stored in a different package
    ContainsMapData = 0x00004000
    # Unused = 0x00008000
    Compiling = 0x00010000
    # Package contains a ULevel/ UWorld object
    ContainsMap = 0x00020000
    # Package contains any data to be gathered by localization
    RequiresLocalizationGather = 0x00040000
    # Unused = 0x00080000
    # Package was created for the purpose of PIE
    PlayInEditor = 0x00100000
    # Package is allowed to contain UClass objects
    ContainsScript = 0x00200000
    # Editor should not export asset in this package
    DisallowExport = 0x00400000
    # Unused = 0x00800000
    # Unused = 0x01000000
    # Unused = 0x02000000
    # Unused = 0x04000000
    # Unused = 0x08000000
    # This package should resolve dynamic imports from its export at runtime.
    DynamicImports = 0x10000000
    # This package contains elements that are runtime generated, and may not
    # follow standard loading order rules
    RuntimeGenerated = 0x20000000
    # This package is reloading in the cooker, try to avoid getting data we
    # will never need. We won't save this package.
    ReloadingForCooker = 0x40000000
    # Package has editor-only data filtered out
    FilterEditorOnly = 0x80000000


PackageFlagStruct = enum_adapter(u32, PackageFlag)
