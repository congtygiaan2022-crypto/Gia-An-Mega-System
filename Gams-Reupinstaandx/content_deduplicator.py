"""
content_deduplicator.py

Co che loc trung bai viet dua tren fingerprint noi dung:
- Text: SimHash 64-bit (so sanh Hamming Distance)
- Anh: Perceptual Hash / aHash 64-bit (so sanh Hamming Distance)
- Video: MD5 cua 100KB dau file
"""

import hashlib
import struct
import os
import re


def _hash_token(token: str) -> int:
    digest = hashlib.md5(token.encode('utf-8')).digest()
    return struct.unpack('Q', digest[:8])[0]


def _to_signed64(n: int) -> int:
    """Convert unsigned 64-bit int to signed 64-bit int (SQLite compatible)."""
    if n >= (1 << 63):
        n -= (1 << 64)
    return n

def compute_simhash_text(text: str) -> int:
    if not text or not text.strip():
        return 0
    text_norm = text.lower().strip()
    tokens = re.findall(r'\b\w+\b', text_norm, re.UNICODE)
    if not tokens:
        return 0
    vector = [0] * 64
    for token in tokens:
        h = _hash_token(token)
        for i in range(64):
            if (h >> i) & 1:
                vector[i] += 1
            else:
                vector[i] -= 1
    fingerprint = 0
    for i in range(64):
        if vector[i] > 0:
            fingerprint |= (1 << i)
    return _to_signed64(fingerprint)


def hamming_distance_64(a: int, b: int) -> int:
    a_u = a & 0xffffffffffffffff
    b_u = b & 0xffffffffffffffff
    xor = a_u ^ b_u
    if hasattr(xor, 'bit_count'):
        return xor.bit_count()
    count = 0
    while xor:
        count += xor & 1
        xor >>= 1
    return count



def is_text_similar(hash_a: int, hash_b: int, threshold: int = 10) -> bool:
    if hash_a == 0 or hash_b == 0:
        return False
    return hamming_distance_64(hash_a, hash_b) <= threshold


def compute_phash_image(image_path: str) -> int:
    try:
        from PIL import Image
        img = Image.open(image_path).convert('L')
        img = img.resize((8, 8), Image.LANCZOS)
        pixels = list(img.getdata())
        avg = sum(pixels) / len(pixels)
        fingerprint = 0
        for i, px in enumerate(pixels):
            if px >= avg:
                fingerprint |= (1 << i)
        return _to_signed64(fingerprint)
    except ImportError:
        return _compute_file_partial_md5_as_int(image_path)
    except Exception:
        return 0


def _compute_file_partial_md5_as_int(file_path: str, read_bytes: int = 102400) -> int:
    try:
        with open(file_path, 'rb') as f:
            data = f.read(read_bytes)
        digest = hashlib.md5(data).digest()
        return struct.unpack('Q', digest[:8])[0]
    except Exception:
        return 0


def is_image_similar(hash_a: int, hash_b: int, threshold: int = 8) -> bool:
    if hash_a == 0 or hash_b == 0:
        return False
    return hamming_distance_64(hash_a, hash_b) <= threshold


def compute_video_md5(video_path: str) -> str:
    try:
        with open(video_path, 'rb') as f:
            data = f.read(102400)
        return hashlib.md5(data).hexdigest()
    except Exception:
        return ""


def compute_fingerprints(caption: str, media_path: str, media_type: str) -> dict:
    text_simhash = compute_simhash_text(caption) if caption else 0
    media_hash = ""
    if media_path and os.path.exists(media_path):
        if media_type == "video":
            media_hash = compute_video_md5(media_path)
        elif media_type == "image":
            phash = compute_phash_image(media_path)
            media_hash = str(phash) if phash else ""
    return {
        "text_simhash": text_simhash,
        "media_hash": media_hash,
        "media_type": media_type
    }


def is_duplicate(new_fp: dict, existing_fps: list) -> tuple:
    new_text = new_fp.get("text_simhash", 0)
    new_media = new_fp.get("media_hash", "")
    new_media_type = new_fp.get("media_type", "")
    
    for fp in existing_fps:
        old_text = fp.get("text_simhash", 0)
        old_media = fp.get("media_hash", "")
        old_media_type = fp.get("media_type", "")
        
        if new_text and old_text:
            if is_text_similar(new_text, old_text, threshold=10):
                dist = hamming_distance_64(new_text, old_text)
                return True, f"Trung noi dung text (Hamming={dist}/64)"
        
        if new_media and old_media and new_media_type == old_media_type:
            if new_media_type == "video":
                if new_media == old_media:
                    return True, "Trung video (MD5 identical)"
            elif new_media_type == "image":
                try:
                    a = int(new_media)
                    b = int(old_media)
                    if is_image_similar(a, b, threshold=8):
                        dist = hamming_distance_64(a, b)
                        return True, f"Trung anh (pHash Hamming={dist}/64)"
                except (ValueError, TypeError):
                    if new_media == old_media:
                        return True, "Trung media (hash exact)"
    
    return False, ""
