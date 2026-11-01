import os, base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

AES_KEY_B64 = os.getenv("AES_KEY_B64")
if not AES_KEY_B64:
    raise RuntimeError("AES_KEY_B64 not set")

def aes_key_bytes() -> bytes:
    return base64.b64decode(AES_KEY_B64)

def aes_encrypt(plaintext: bytes):
    key = aes_key_bytes()
    iv = os.urandom(12)
    aes = AESGCM(key)
    ct = aes.encrypt(iv, plaintext, None)
    tag = ct[-16:]; body = ct[:-16]
    return body, iv, tag

def aes_decrypt(cipher: bytes, iv: bytes, tag: bytes) -> bytes:
    key = aes_key_bytes()
    aes = AESGCM(key)
    return aes.decrypt(iv, cipher + tag, None)
