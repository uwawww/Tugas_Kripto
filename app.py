import base64
import os

from flask import Flask, jsonify, render_template, request

from cipher import (
    StegoError,
    VigenereError,
    embed,
    extract,
    generate_process,
    is_letter,
)

MAX_TEXT_LENGTH = 10000
MAX_UPLOAD_BYTES = 8 * 1024 * 1024  # 8 MB

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES


def error_response(message, status=400):
    return jsonify({"success": False, "error": message}), status


def handle_cipher(mode):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return error_response("Request body harus berupa JSON dengan field 'text' dan 'key'.")

    text = data.get("text")
    key = data.get("key")

    if not isinstance(text, str) or not text.strip():
        return error_response("Teks tidak boleh kosong.")
    if len(text) > MAX_TEXT_LENGTH:
        return error_response(f"Teks terlalu panjang (maksimal {MAX_TEXT_LENGTH} karakter).")

    try:
        output = generate_process(text, key, mode)
    except VigenereError as exc:
        return error_response(str(exc))

    warnings = []
    if any(not is_letter(c) for c in key):
        warnings.append(
            f"Karakter non-huruf pada key diabaikan. Key yang dipakai: {output['key']}."
        )
    if not output["process"]:
        warnings.append("Teks tidak mengandung huruf A-Z, sehingga tidak ada yang diproses.")

    return jsonify({
        "success": True,
        "mode": mode,
        "result": output["result"],
        "process": output["process"],
        "key": output["key"],
        "effective_key": output["effective_key"],
        "warnings": warnings,
    })


def read_image_upload():
    """Ambil bytes gambar dari field multipart 'image'."""
    file = request.files.get("image")
    if file is None or not file.filename:
        raise StegoError("Pilih file gambar terlebih dahulu.")
    return file.read()


def handle_stego_embed():
    text = request.form.get("text", "")
    key = request.form.get("key", "")

    if not text.strip():
        return error_response("Pesan rahasia tidak boleh kosong.")
    if len(text) > MAX_TEXT_LENGTH:
        return error_response(f"Pesan terlalu panjang (maksimal {MAX_TEXT_LENGTH} karakter).")

    warnings = []
    try:
        image_bytes = read_image_upload()
        encrypted = bool(key.strip())
        if encrypted:
            output = generate_process(text, key, "encrypt")
            hidden_text = output["result"]
            if any(not is_letter(c) for c in key):
                warnings.append(
                    f"Karakter non-huruf pada key diabaikan. Key yang dipakai: {output['key']}."
                )
            if not output["process"]:
                warnings.append("Pesan tidak mengandung huruf A-Z, sehingga Vigenère tidak mengubah apa pun.")
        else:
            output = None
            hidden_text = text
            warnings.append("Key kosong: pesan disisipkan tanpa enkripsi Vigenère.")

        png_bytes, info = embed(image_bytes, hidden_text.encode("utf-8"), encrypted)
    except (StegoError, VigenereError) as exc:
        return error_response(str(exc))

    if info["had_alpha"]:
        warnings.append("Transparansi gambar dihapus karena hasil disimpan sebagai PNG RGB.")

    return jsonify({
        "success": True,
        "encrypted": encrypted,
        "ciphertext": hidden_text,
        "key": output["key"] if output else None,
        "process": output["process"] if output else [],
        "image": "data:image/png;base64," + base64.b64encode(png_bytes).decode("ascii"),
        "width": info["width"],
        "height": info["height"],
        "capacity_bytes": info["capacity_bytes"],
        "payload_bytes": info["payload_bytes"],
        "warnings": warnings,
    })


def handle_stego_extract():
    key = request.form.get("key", "")
    warnings = []
    try:
        image_bytes = read_image_upload()
        payload, encrypted = extract(image_bytes)
        try:
            hidden_text = payload.decode("utf-8")
        except UnicodeDecodeError:
            raise StegoError("Data tersembunyi bukan teks UTF-8 yang valid.")

        if encrypted:
            if not key.strip():
                raise StegoError("Pesan ini dienkripsi dengan Vigenère. Masukkan key untuk mendekripsinya.")
            output = generate_process(hidden_text, key, "decrypt")
            plaintext = output["result"]
            used_key = output["key"]
            process = output["process"]
            if any(not is_letter(c) for c in key):
                warnings.append(f"Karakter non-huruf pada key diabaikan. Key yang dipakai: {used_key}.")
        else:
            plaintext, used_key, process = hidden_text, None, []
            if key.strip():
                warnings.append("Pesan ini tidak dienkripsi Vigenère, sehingga key diabaikan.")
    except (StegoError, VigenereError) as exc:
        return error_response(str(exc))

    return jsonify({
        "success": True,
        "encrypted": encrypted,
        "extracted": hidden_text,
        "plaintext": plaintext,
        "key": used_key,
        "process": process,
        "warnings": warnings,
    })


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/encrypt", methods=["POST"])
def api_encrypt():
    return handle_cipher("encrypt")


@app.route("/api/decrypt", methods=["POST"])
def api_decrypt():
    return handle_cipher("decrypt")


@app.route("/api/stego/embed", methods=["POST"])
def api_stego_embed():
    return handle_stego_embed()


@app.route("/api/stego/extract", methods=["POST"])
def api_stego_extract():
    return handle_stego_extract()


@app.errorhandler(413)
def too_large(_):
    return error_response(f"Ukuran file terlalu besar (maksimal {MAX_UPLOAD_BYTES // (1024 * 1024)} MB).", 413)


@app.errorhandler(405)
def method_not_allowed(_):
    return error_response("Method tidak diizinkan.", 405)


@app.errorhandler(500)
def server_error(_):
    return error_response("Terjadi kesalahan internal pada server.", 500)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)