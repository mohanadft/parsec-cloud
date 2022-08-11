from typing import Optional, Tuple
from parsec._parsec_pyi import BackendOrganizationAddr
from parsec._parsec_pyi.crypto import PrivateKey, PublicKey, SecretKey, SigningKey, VerifyKey
from parsec._parsec_pyi.ids import (
    DeviceID,
    DeviceLabel,
    DeviceName,
    EntryID,
    HumanHandle,
    OrganizationID,
    UserID,
)

from parsec.api.protocol.types import UserProfile
from pendulum import DateTime

class LocalDevice:
    def __init__(
        self,
        organization_addr: BackendOrganizationAddr,
        device_id: DeviceID,
        device_label: Optional[DeviceLabel],
        human_handle: Optional[HumanHandle],
        signing_key: SigningKey,
        private_key: PrivateKey,
        profile: UserProfile,
        user_manifest_id: EntryID,
        user_manifest_key: SecretKey,
        local_symkey: SecretKey,
    ) -> None: ...
    def __repr__(self) -> str: ...
    def __eq__(self, other: LocalDevice) -> bool: ...
    def __ne__(self, other: LocalDevice) -> bool: ...
    def __lt__(self, other: LocalDevice) -> bool: ...
    def __gt__(self, other: LocalDevice) -> bool: ...
    def __le__(self, other: LocalDevice) -> bool: ...
    def __ge__(self, other: LocalDevice) -> bool: ...
    def evolve(
        self,
        organization_addr: Optional[BackendOrganizationAddr],
        device_id: Optional[DeviceID],
        device_label: Optional[DeviceLabel],
        human_handle: Optional[HumanHandle],
        signing_key: Optional[SigningKey],
        private_key: Optional[PrivateKey],
        profile: Optional[UserProfile],
        user_manifest_id: Optional[EntryID],
        user_manifest_key: Optional[SecretKey],
        local_symkey: Optional[SecretKey],
    ) -> LocalDevice: ...
    @property
    def is_admin(self) -> bool: ...
    @property
    def is_outsider(self) -> bool: ...
    @property
    def slug(self) -> str: ...
    @property
    def slughash(self) -> str: ...
    @property
    def root_verify_key(self) -> VerifyKey: ...
    @property
    def organization_id(self) -> OrganizationID: ...
    @property
    def device_name(self) -> DeviceName: ...
    @property
    def user_id(self) -> UserID: ...
    @property
    def verify_key(self) -> VerifyKey: ...
    @property
    def public_key(self) -> PublicKey: ...
    @property
    def user_display(self) -> str: ...
    @property
    def short_user_display(self) -> str: ...
    @property
    def device_display(self) -> str: ...
    @property
    def organization_addr(self) -> BackendOrganizationAddr: ...
    @property
    def device_id(self) -> DeviceID: ...
    @property
    def device_label(self) -> Optional[DeviceLabel]: ...
    @property
    def human_handle(self) -> Optional[HumanHandle]: ...
    @property
    def signing_key(self) -> SigningKey: ...
    @property
    def private_key(self) -> PrivateKey: ...
    @property
    def profile(self) -> UserProfile: ...
    @property
    def user_manifest_id(self) -> EntryID: ...
    @property
    def user_manifest_key(self) -> SecretKey: ...
    @property
    def local_symkey(self) -> SecretKey: ...
    def timestamp(self) -> DateTime: ...
    def dump(self) -> bytes: ...
    @classmethod
    def load_slug(cls, slug: str) -> Tuple[OrganizationID, DeviceID]: ...
    @classmethod
    def load(cls, encrypted: bytes) -> LocalDevice: ...
