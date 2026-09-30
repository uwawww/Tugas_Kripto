"""Implementasi manual Vigenère Cipher klasik (tanpa library kriptografi).

Mapping : A=0, B=1, ..., Z=25
Enkripsi: C = (P + K) mod 26
Dekripsi: P = (C - K) mod 26

Aturan:
- Hanya huruf ASCII A-Z / a-z yang diproses.
- Spasi, angka, dan tanda baca dipertahankan apa adanya.
- Karakter non-huruf TIDAK menggeser posisi key.
- Huruf kecil menghasilkan huruf kecil.
"""

ALPHABET_SIZE = 26


class VigenereError(ValueError):
    """Error validasi input untuk Vigenère Cipher."""


def is_letter(ch):
    """True jika ch adalah huruf ASCII A-Z / a-z."""
    return ch.isascii() and ch.isalpha()


def char_to_num(ch):
    """A/a -> 0, B/b -> 1, ..., Z/z -> 25."""
    return ord(ch.upper()) - ord("A")


def num_to_char(num):
    """0 -> A, 1 -> B, ..., 25 -> Z."""
    return chr(num + ord("A"))


def normalize_key(key):
    """Ambil hanya huruf dari key, ubah ke uppercase.

    Karakter non-huruf pada key diabaikan secara konsisten.
    """
    if not isinstance(key, str) or not key.strip():
        raise VigenereError("Key tidak boleh kosong.")
    letters = "".join(c.upper() for c in key if is_letter(c))
    if not letters:
        raise VigenereError("Key harus memiliki minimal satu huruf alfabet (A-Z).")
    return letters


def generate_process(text, key, mode):
    """Jalankan Vigenère dan kembalikan hasil beserta detail tiap huruf.

    mode: "encrypt" atau "decrypt".
    """
    if mode not in ("encrypt", "decrypt"):
        raise VigenereError("Mode harus 'encrypt' atau 'decrypt'.")

    clean_key = normalize_key(key)
    result_chars = []
    effective_key_chars = []
    process = []
    key_index = 0  # hanya bertambah ketika menemukan huruf

    for ch in text:
        if not is_letter(ch):
            result_chars.append(ch)
            effective_key_chars.append(ch)
            continue

        key_char = clean_key[key_index % len(clean_key)]
        key_index += 1

        input_value = char_to_num(ch)
        key_value = char_to_num(key_char)

        if mode == "encrypt":
            raw_value = input_value + key_value      # P + K
            operator = "+"
        else:
            raw_value = input_value - key_value      # C - K (bisa negatif)
            operator = "-"

        output_value = raw_value % ALPHABET_SIZE     # mod 26 (hasil selalu 0..25)
        output = num_to_char(output_value)
        if ch.islower():
            output = output.lower()

        result_chars.append(output)
        effective_key_chars.append(key_char)
        process.append({
            "position": key_index,
            "input": ch,
            "key": key_char,
            "input_value": input_value,
            "key_value": key_value,
            "operation": f"({input_value} {operator} {key_value}) % {ALPHABET_SIZE}",
            "raw_value": raw_value,
            "output_value": output_value,
            "output": output,
        })

    return {
        "result": "".join(result_chars),
        "process": process,
        "key": clean_key,
        "effective_key": "".join(effective_key_chars),
    }


def encrypt(plaintext, key):
    """Enkripsi: C = (P + K) mod 26."""
    return generate_process(plaintext, key, "encrypt")["result"]


def decrypt(ciphertext, key):
    """Dekripsi: P = (C - K) mod 26."""
    return generate_process(ciphertext, key, "decrypt")["result"]