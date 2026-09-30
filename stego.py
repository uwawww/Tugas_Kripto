"""Steganografi gambar dengan metode LSB (Least Significant Bit).

Alur gabungan dengan Vigenère:
    Sembunyikan : plaintext --Vigenère--> ciphertext --LSB--> gambar PNG
    Ekstrak     : gambar PNG --LSB--> ciphertext --Vigenère--> plaintext

Setiap byte pesan dipecah menjadi 8 bit (MSB dulu). Tiap bit disimpan pada
bit paling tidak signifikan (LSB) dari satu kanal warna (R, G, B) piksel,
sehingga perubahan warna maksimal hanya 1 dari 255 dan tidak terlihat mata.

Format data yang disisipkan (big-endian):
    4 byte  MAGIC  "VGST"
    1 byte  FLAG   bit 0 = pesan sudah dienkripsi Vigenère
    4 byte  LENGTH panjang payload (byte)
    N byte  PAYLOAD pesan (UTF-8)

Output harus disimpan sebagai PNG (lossless). JPEG akan merusak bit LSB.
"""

import io
import struct

from PIL import Image, UnidentifiedImageError

MAGIC = b"VGST"
HEADER_FORMAT = ">4sBI"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)  # 9 byte
FLAG_VIGENERE = 0x01
CHANNELS = 3  # R, G, B
MAX_PIXELS = 16_000_000
ALLOWED_FORMATS = {"PNG", "BMP", "JPEG", "WEBP", "GIF", "TIFF"}


class StegoError(ValueError):
    """Error validasi / pemrosesan steganografi."""


def capacity_bytes(width, height):
    """Jumlah byte payload maksimal yang muat pada gambar width x height."""
    total_bits = width * height * CHANNELS
    return max(0, total_bits // 8 - HEADER_SIZE)


def _open_image(image_bytes):
    if not image_bytes:
        raise StegoError("File gambar tidak boleh kosong.")
    try:
        img = Image.open(io.BytesIO(image_bytes))
        if img.format not in ALLOWED_FORMATS:
            raise StegoError("Format gambar tidak didukung. Gunakan PNG, BMP, JPEG, atau WEBP.")
        if img.width * img.height > MAX_PIXELS:
            raise StegoError("Resolusi gambar terlalu besar (maksimal 16 megapiksel).")
        has_alpha = img.mode in ("RGBA", "LA", "PA") or "transparency" in img.info
        img.load()
    except StegoError:
        raise
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise StegoError("File bukan gambar yang valid.")
    return img.convert("RGB"), has_alpha


def _bits(data):
    for byte in data:
        for shift in range(7, -1, -1):
            yield (byte >> shift) & 1


def embed(image_bytes, payload, encrypted=False):
    """Sisipkan payload (bytes) ke gambar. Mengembalikan (png_bytes, info)."""
    if not payload:
        raise StegoError("Pesan tidak boleh kosong.")

    img, has_alpha = _open_image(image_bytes)
    cap = capacity_bytes(img.width, img.height)
    if len(payload) > cap:
        raise StegoError(
            f"Pesan terlalu besar untuk gambar ini: {len(payload)} byte, kapasitas {cap} byte. "
            "Gunakan gambar yang lebih besar atau pesan yang lebih pendek."
        )

    header = struct.pack(HEADER_FORMAT, MAGIC, FLAG_VIGENERE if encrypted else 0, len(payload))
    data = bytearray(img.tobytes())
    for i, bit in enumerate(_bits(header + payload)):
        data[i] = (data[i] & 0xFE) | bit

    out = Image.frombytes("RGB", img.size, bytes(data))
    buf = io.BytesIO()
    out.save(buf, format="PNG")
    return buf.getvalue(), {
        "width": img.width,
        "height": img.height,
        "capacity_bytes": cap,
        "payload_bytes": len(payload),
        "had_alpha": has_alpha,
    }


def _read_bytes(data, start_byte, count):
    out = bytearray()
    pos = start_byte * 8
    for _ in range(count):
        value = 0
        for k in range(8):
            value = (value << 1) | (data[pos + k] & 1)
        out.append(value)
        pos += 8
    return bytes(out)


def extract(image_bytes):
    """Baca payload dari gambar. Mengembalikan (payload_bytes, encrypted_flag)."""
    img, _ = _open_image(image_bytes)
    data = img.tobytes()
    if len(data) < HEADER_SIZE * 8:
        raise StegoError("Gambar terlalu kecil untuk memuat pesan.")

    magic, flag, length = struct.unpack(HEADER_FORMAT, _read_bytes(data, 0, HEADER_SIZE))
    if magic != MAGIC:
        raise StegoError(
            "Tidak ditemukan pesan tersembunyi. Pastikan gambar adalah PNG hasil "
            "penyisipan aplikasi ini (JPEG/hasil kompresi akan merusak pesan)."
        )
    if length == 0 or length > capacity_bytes(img.width, img.height):
        raise StegoError("Data pesan pada gambar rusak atau tidak valid.")

    payload = _read_bytes(data, HEADER_SIZE, length)
    return payload, bool(flag & FLAG_VIGENERE)
