# Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

from __future__ import annotations

from parsec._parsec import DateTime, SequesterServiceID, VlobID

class Req:
    def __init__(
        self,
        encryption_revision: int,
        vlob_id: VlobID,
        timestamp: DateTime,
        version: int,
        blob: bytes,
        sequester_blob: dict[SequesterServiceID, bytes] | None,
    ) -> None: ...
    def dump(self) -> bytes: ...
    @property
    def encryption_revision(self) -> int: ...
    @property
    def vlob_id(self) -> VlobID: ...
    @property
    def timestamp(self) -> DateTime: ...
    @property
    def version(self) -> int: ...
    @property
    def blob(self) -> bytes: ...
    @property
    def sequester_blob(self) -> dict[SequesterServiceID, bytes] | None: ...

class Rep:
    @staticmethod
    def load(raw: bytes) -> Rep: ...
    def dump(self) -> bytes: ...

class RepUnknownStatus(Rep):
    def __init__(self, status: str, reason: str | None) -> None: ...
    @property
    def status(self) -> str: ...
    @property
    def reason(self) -> str | None: ...

class RepOk(Rep):
    def __init__(
        self,
    ) -> None: ...

class RepNotFound(Rep):
    def __init__(self, reason: str | None) -> None: ...
    @property
    def reason(self) -> str | None: ...

class RepNotAllowed(Rep):
    def __init__(
        self,
    ) -> None: ...

class RepBadVersion(Rep):
    def __init__(
        self,
    ) -> None: ...

class RepBadEncryptionRevision(Rep):
    def __init__(
        self,
    ) -> None: ...

class RepInMaintenance(Rep):
    def __init__(
        self,
    ) -> None: ...

class RepRequireGreaterTimestamp(Rep):
    def __init__(self, strictly_greater_than: DateTime) -> None: ...
    @property
    def strictly_greater_than(self) -> DateTime: ...

class RepBadTimestamp(Rep):
    def __init__(
        self,
        reason: str | None,
        ballpark_client_early_offset: float,
        ballpark_client_late_offset: float,
        backend_timestamp: DateTime,
        client_timestamp: DateTime,
    ) -> None: ...
    @property
    def reason(self) -> str | None: ...
    @property
    def ballpark_client_early_offset(self) -> float: ...
    @property
    def ballpark_client_late_offset(self) -> float: ...
    @property
    def backend_timestamp(self) -> DateTime: ...
    @property
    def client_timestamp(self) -> DateTime: ...

class RepNotASequesteredOrganization(Rep):
    def __init__(
        self,
    ) -> None: ...

class RepSequesterInconsistency(Rep):
    def __init__(
        self, sequester_authority_certificate: bytes, sequester_services_certificates: list[bytes]
    ) -> None: ...
    @property
    def sequester_authority_certificate(self) -> bytes: ...
    @property
    def sequester_services_certificates(self) -> list[bytes]: ...

class RepRejectedBySequesterService(Rep):
    def __init__(self, service_id: SequesterServiceID, service_label: str, reason: str) -> None: ...
    @property
    def service_id(self) -> SequesterServiceID: ...
    @property
    def service_label(self) -> str: ...
    @property
    def reason(self) -> str: ...

class RepTimeout(Rep):
    def __init__(
        self,
    ) -> None: ...
