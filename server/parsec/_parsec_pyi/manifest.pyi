# Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

from __future__ import annotations

from typing import Any, Tuple, Union

from parsec._parsec import (
    BlockID,
    DateTime,
    DeviceID,
    HashDigest,
    RealmRole,
    SecretKey,
    SigningKey,
    VerifyKey,
    VlobID,
)
from parsec.types import FrozenDict

ChildManifest = Union[
    FolderManifest,
    FileManifest,
]

class EntryName:
    def __init__(self, name: str) -> None: ...
    def __str__(self) -> str: ...
    def __lt__(self, other: EntryName | None) -> bool: ...
    def __gt__(self, other: EntryName | None) -> bool: ...
    def __le__(self, other: EntryName | None) -> bool: ...
    def __ge__(self, other: EntryName | None) -> bool: ...
    def __hash__(self) -> int: ...
    @property
    def str(self) -> str: ...

class WorkspaceEntry:
    def __init__(
        self,
        name: EntryName,
        id: VlobID,
        key: SecretKey,
        encryption_revision: int,
        encrypted_on: DateTime,
        legacy_role_cache_timestamp: DateTime,
        legacy_role_cache_value: RealmRole | None,
    ) -> None: ...
    @property
    def id(self) -> VlobID: ...
    @property
    def name(self) -> EntryName: ...
    @property
    def key(self) -> SecretKey: ...
    @property
    def encryption_revision(self) -> int: ...
    @property
    def encrypted_on(self) -> DateTime: ...
    @property
    def legacy_role_cache_timestamp(self) -> DateTime: ...
    @property
    def legacy_role_cache_value(self) -> RealmRole | None: ...
    @classmethod
    def new(cls, name: EntryName, timestamp: DateTime) -> WorkspaceEntry: ...
    def evolve(self, **kwargs: Any) -> WorkspaceEntry: ...

class BlockAccess:
    def __init__(
        self, id: BlockID, key: SecretKey, offset: int, size: int, digest: HashDigest
    ) -> None: ...
    @property
    def id(self) -> BlockID: ...
    @property
    def key(self) -> SecretKey: ...
    @property
    def offset(self) -> int: ...
    @property
    def size(self) -> int: ...
    @property
    def digest(self) -> HashDigest: ...

class FolderManifest:
    def __init__(
        self,
        author: DeviceID,
        timestamp: DateTime,
        id: VlobID,
        parent: VlobID,
        version: int,
        created: DateTime,
        updated: DateTime,
        children: FrozenDict[EntryName, VlobID],
    ) -> None: ...
    @property
    def author(self) -> DeviceID: ...
    @property
    def id(self) -> VlobID: ...
    @property
    def parent(self) -> VlobID: ...
    @property
    def version(self) -> int: ...
    @property
    def timestamp(self) -> DateTime: ...
    @property
    def created(self) -> DateTime: ...
    @property
    def updated(self) -> DateTime: ...
    @property
    def children(self) -> FrozenDict[EntryName, VlobID]: ...
    def evolve(self, **kwargs: Any) -> FolderManifest: ...
    def dump_and_sign(self, author_signkey: SigningKey) -> bytes: ...
    def dump_sign_and_encrypt(self, author_signkey: SigningKey, key: SecretKey) -> bytes: ...
    @classmethod
    def decrypt_verify_and_load(
        cls,
        encrypted: bytes,
        key: SecretKey,
        author_verify_key: VerifyKey,
        expected_author: DeviceID,
        expected_timestamp: DateTime,
        expected_id: VlobID | None = None,
        expected_version: int | None = None,
    ) -> FolderManifest: ...

class FileManifest:
    def __init__(
        self,
        author: DeviceID,
        timestamp: DateTime,
        id: VlobID,
        parent: VlobID,
        version: int,
        created: DateTime,
        updated: DateTime,
        size: int,
        blocksize: int,
        blocks: Tuple[BlockAccess],
    ) -> None: ...
    @property
    def author(self) -> DeviceID: ...
    @property
    def id(self) -> VlobID: ...
    @property
    def parent(self) -> VlobID: ...
    @property
    def version(self) -> int: ...
    @property
    def timestamp(self) -> DateTime: ...
    @property
    def created(self) -> DateTime: ...
    @property
    def updated(self) -> DateTime: ...
    @property
    def size(self) -> int: ...
    @property
    def blocksize(self) -> int: ...
    @property
    def blocks(self) -> Tuple[BlockAccess]: ...
    def evolve(self, **kwargs: Any) -> FileManifest: ...
    def dump_and_sign(self, author_signkey: SigningKey) -> bytes: ...
    def dump_sign_and_encrypt(self, author_signkey: SigningKey, key: SecretKey) -> bytes: ...
    @classmethod
    def decrypt_verify_and_load(
        cls,
        encrypted: bytes,
        key: SecretKey,
        author_verify_key: VerifyKey,
        expected_author: DeviceID,
        expected_timestamp: DateTime,
        expected_id: VlobID | None = None,
        expected_version: int | None = None,
    ) -> FileManifest: ...

class WorkspaceManifest:
    def __init__(
        self,
        author: DeviceID,
        timestamp: DateTime,
        id: VlobID,
        version: int,
        created: DateTime,
        updated: DateTime,
        children: FrozenDict[EntryName, VlobID],
    ) -> None: ...
    @property
    def author(self) -> DeviceID: ...
    @property
    def id(self) -> VlobID: ...
    @property
    def version(self) -> int: ...
    @property
    def timestamp(self) -> DateTime: ...
    @property
    def created(self) -> DateTime: ...
    @property
    def updated(self) -> DateTime: ...
    @property
    def children(self) -> FrozenDict[EntryName, VlobID]: ...
    def evolve(self, **kwargs: Any) -> WorkspaceManifest: ...
    def dump_and_sign(self, author_signkey: SigningKey) -> bytes: ...
    def dump_sign_and_encrypt(self, author_signkey: SigningKey, key: SecretKey) -> bytes: ...
    @classmethod
    def decrypt_verify_and_load(
        cls,
        encrypted: bytes,
        key: SecretKey,
        author_verify_key: VerifyKey,
        expected_author: DeviceID,
        expected_timestamp: DateTime,
        expected_id: VlobID | None = None,
        expected_version: int | None = None,
    ) -> WorkspaceManifest: ...
    @classmethod
    def verify_and_load(
        cls,
        signed: bytes,
        author_verify_key: VerifyKey,
        expected_author: DeviceID,
        expected_timestamp: DateTime,
        expected_id: VlobID | None = None,
        expected_version: int | None = None,
    ) -> WorkspaceManifest: ...

class UserManifest:
    def __init__(
        self,
        author: DeviceID,
        timestamp: DateTime,
        id: VlobID,
        version: int,
        created: DateTime,
        updated: DateTime,
        last_processed_message: int,
        workspaces: Tuple[WorkspaceEntry],
    ) -> None: ...
    @property
    def author(self) -> DeviceID: ...
    @property
    def id(self) -> VlobID: ...
    @property
    def version(self) -> int: ...
    @property
    def timestamp(self) -> DateTime: ...
    @property
    def created(self) -> DateTime: ...
    @property
    def updated(self) -> DateTime: ...
    @property
    def last_processed_message(self) -> int: ...
    @property
    def workspaces(self) -> Tuple[WorkspaceEntry]: ...
    def evolve(self, **kwargs: Any) -> UserManifest: ...
    def dump_and_sign(self, author_signkey: SigningKey) -> bytes: ...
    def dump_sign_and_encrypt(self, author_signkey: SigningKey, key: SecretKey) -> bytes: ...
    @classmethod
    def decrypt_verify_and_load(
        cls,
        encrypted: bytes,
        key: SecretKey,
        author_verify_key: VerifyKey,
        expected_author: DeviceID,
        expected_timestamp: DateTime,
        expected_id: VlobID | None = None,
        expected_version: int | None = None,
    ) -> UserManifest: ...
    def get_workspace_entry(self, workspace_id: VlobID) -> WorkspaceEntry | None: ...

def child_manifest_decrypt_verify_and_load(
    encrypted: bytes,
    key: SecretKey,
    author_verify_key: VerifyKey,
    expected_author: DeviceID,
    expected_timestamp: DateTime,
    expected_id: VlobID | None = None,
    expected_version: int | None = None,
) -> ChildManifest: ...
def child_manifest_verify_and_load(
    signed: bytes,
    author_verify_key: VerifyKey,
    expected_author: DeviceID,
    expected_timestamp: DateTime,
    expected_id: VlobID | None = None,
    expected_version: int | None = None,
) -> ChildManifest: ...
