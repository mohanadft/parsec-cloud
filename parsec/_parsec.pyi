class SecretKey:
    def __init__(self, data: bytes) -> None: ...
    def __repr__(self) -> str: ...
    def __eq__(self, other: SecretKey) -> bool: ...
    def __ne__(self, other: SecretKey) -> bool: ...
    @property
    def secret(self) -> bytes: ...
    def generate() -> SecretKey: ...
    def encrypt(self, data: bytes) -> bytes: ...
    def decrypt(self, ciphered: bytes) -> bytes: ...
    def hmac(self, data: bytes, digest_size: int) -> bytes: ...

class HashDigest:
    def __init__(self, hash: bytes) -> None: ...
    def __repr__(self) -> str: ...
    def __eq__(self, other: HashDigest) -> bool: ...
    def __ne__(self, other: HashDigest) -> bool: ...
    @property
    def digest(self) -> bytes: ...
    @staticmethod
    def from_data(data: bytes) -> HashDigest: ...
    def hexdigest(self) -> str: ...

class SigningKey:
    def __init__(self, data: bytes) -> None: ...
    def __repr__(self) -> str: ...
    def __eq__(self, other: SigningKey) -> bool: ...
    def __ne__(self, other: SigningKey) -> bool: ...
    @property
    def verify_key(self) -> VerifyKey: ...
    def generate() -> SigningKey: ...
    def sign(self, data: bytes) -> bytes: ...
    def encode(self) -> bytes: ...

class VerifyKey:
    def __init__(self, data: bytes) -> None: ...
    def __repr__(self) -> str: ...
    def __eq__(self, other: VerifyKey) -> bool: ...
    def __ne__(self, other: VerifyKey) -> bool: ...
    def __bytes__(self) -> bytes: ...
    def verify(self, signed: bytes) -> bytes: ...
    def unsecure_unwrap(signed: bytes) -> bytes: ...
    def encode(self) -> bytes: ...

class PrivateKey:
    def __init__(self, data: bytes) -> None: ...
    def __repr__(self) -> str: ...
    def __eq__(self, other: PrivateKey) -> bool: ...
    def __ne__(self, other: PrivateKey) -> bool: ...
    @property
    def public_key(self) -> PublicKey: ...
    def generate() -> PrivateKey: ...
    def decrypt_from_self(self, ciphered: bytes) -> bytes: ...
    def encode(self) -> bytes: ...

class PublicKey:
    def __init__(self, data: bytes) -> None: ...
    def __repr__(self) -> str: ...
    def __eq__(self, other: PublicKey) -> bool: ...
    def __ne__(self, other: PublicKey) -> bool: ...
    def encrypt_for_self(self, data: bytes) -> bytes: ...
    def encode(self) -> bytes: ...
