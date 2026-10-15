import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from config import settings


def get_encryption_key() -> bytes:
    try:
        key = bytes.fromhex(settings.FILE_ENCRYPTION_KEY)
    except ValueError as exc:
        raise ValueError("FILE_ENCRYPTION_KEY must be a valid hex string") from exc

    if len(key) != 32:
        raise ValueError("FILE_ENCRYPTION_KEY must be exactly 32 bytes")

    return key


def encrypt_file(data: bytes) -> bytes:
    key = get_encryption_key()
    nonce = os.urandom(12)

    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, data, None)

    # Store nonce alongside ciphertext so decryption is possible later.
    return b"ZTS1" + nonce + ciphertext


def decrypt_file(encrypted_data: bytes) -> bytes:
    if len(encrypted_data) < 32 or encrypted_data[:4] != b"ZTS1":
        raise ValueError("Invalid encrypted file format")

    key = get_encryption_key()
    nonce = encrypted_data[4:16]
    ciphertext = encrypted_data[16:]

    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None)