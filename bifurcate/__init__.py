"""Bifurcate — a chaos-seeded hybrid Feistel cipher."""

from .cipher import Bifurcate, decrypt_block, encrypt_block
from .container import decrypt, encrypt, parse
from .mac import IntegrityError
from .kdf import derive_subkeys
from .keyschedule import expand

__version__ = "0.1.0"
__all__ = [
    "Bifurcate", "encrypt_block", "decrypt_block", "derive_subkeys", "expand",
    "encrypt", "decrypt", "parse", "IntegrityError",
]
