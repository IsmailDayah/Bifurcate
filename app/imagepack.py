"""Self-describing image payloads, so a decrypted image can snap back.

Raw ``Image.tobytes()`` loses the dimensions — after decryption nobody can
reshape the pixels. A 12-byte header fixes that:

    b"BIMG" | width (u32 BE) | height (u32 BE) | RGB bytes

The header travels *inside* the encrypted payload, so it is protected like
everything else, and the Decrypt page can recognise an image and render it
back — the "photo snaps back, perfect, green tick" moment of the demo.
"""

from __future__ import annotations

import io

from PIL import Image

MAGIC = b"BIMG"
HEADER_LEN = 12
MAX_DIM = 20_000  # sanity bound when parsing untrusted plaintext


def pack(img: Image.Image) -> bytes:
    """RGB image -> self-describing payload."""
    w, h = img.size
    return MAGIC + w.to_bytes(4, "big") + h.to_bytes(4, "big") + img.tobytes()


def try_unpack(data: bytes) -> Image.Image | None:
    """Payload -> image, or None if this isn't an image payload."""
    if len(data) < HEADER_LEN or data[:4] != MAGIC:
        return None
    w = int.from_bytes(data[4:8], "big")
    h = int.from_bytes(data[8:12], "big")
    if not (0 < w <= MAX_DIM and 0 < h <= MAX_DIM):
        return None
    if len(data) != HEADER_LEN + w * h * 3:
        return None
    return Image.frombytes("RGB", (w, h), data[HEADER_LEN:])


def to_png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()
