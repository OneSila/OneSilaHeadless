import io
import math
from typing import Tuple
import requests
from PIL import Image
import imagehash

DEFAULT_HEADERS = {"User-Agent": "img-similarity/1.0"}
MAX_BYTES = 25 * 1024 * 1024  # 25 MB safety cap


def _fetch_bytes(url: str, timeout: Tuple[float, float] = (5, 20)) -> bytes:
    """Download URL into memory with a size cap."""
    with requests.get(url, headers=DEFAULT_HEADERS, stream=True, timeout=timeout) as r:
        r.raise_for_status()
        total = 0
        chunks = []
        for chunk in r.iter_content(1024 * 32):
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_BYTES:
                raise ValueError(f"Image too large (> {MAX_BYTES} bytes): {url}")
            chunks.append(chunk)
        return b"".join(chunks)


def _pil_from_source(src: str) -> Image.Image:
    if src.startswith("http://") or src.startswith("https://"):
        data = _fetch_bytes(src)
        img = Image.open(io.BytesIO(data))
    else:
        img = Image.open(src)
    img.load()
    return img


def phash_is_same(src1: str, src2: str, hash_size: int = 16, threshold: float = 95.0) -> bool:
    img1 = _pil_from_source(src1).convert("RGB")
    img2 = _pil_from_source(src2).convert("RGB")
    h1 = imagehash.phash(img1, hash_size=hash_size)
    h2 = imagehash.phash(img2, hash_size=hash_size)
    dist = int(h1 - h2)
    max_bits = hash_size * hash_size
    allowed_dist = math.floor((1.0 - threshold / 100.0) * max_bits)
    return dist <= allowed_dist
