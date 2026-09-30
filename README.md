# Vigenère Cipher – Classical Cryptography

## 1. Project Description
Aplikasi web pembelajaran kriptografi yang mengimplementasikan **Vigenère Cipher klasik** secara manual (tanpa library kriptografi). Semua proses berjalan lokal, tanpa database dan tanpa API eksternal.

## 2. Features
- Enkripsi dan dekripsi Vigenère
- Detail proses per huruf (tabel Position, Input, Key, nilai, Operation, Output)
- Tabel Vigenère (tabula recta) 26×26 yang dibuat dinamis dengan JavaScript
- Menjaga spasi, angka, tanda baca, dan huruf besar/kecil
- Validasi input, tombol Copy Result dan Clear
- UI dark, responsif, berbasis kartu
- Unit test untuk algoritma dan API
- **Steganografi gambar (LSB) + Vigenère**: pesan dienkripsi Vigenère lalu disembunyikan di gambar PNG, dan bisa diekstrak + didekripsi kembali

## 3. Vigenère Cipher
Cipher substitusi polialfabetik yang memakai keyword. Setiap huruf digeser sejauh nilai huruf key, dan key diulang sepanjang teks. Karakter non-huruf tidak dienkripsi dan tidak menggeser posisi key.

## 4. Formula
Mapping: `A=0, B=1, ..., Z=25`

```text
Enkripsi: C = (P + K) mod 26
Dekripsi: P = (C - K) mod 26
```

## 4b. Steganografi (LSB) + Vigenère
Alur:
```text
Sembunyikan : plaintext -> Vigenère -> ciphertext -> LSB -> gambar PNG
Ekstrak     : gambar PNG -> LSB -> ciphertext -> Vigenère -> plaintext
```
- Tiap bit pesan disimpan di bit terakhir (LSB) kanal R, G, B piksel, sehingga tiap kanal berubah maksimal 1 nilai.
- Data disisipkan bersama header 9 byte (`VGST`, flag enkripsi, panjang pesan). Flag ini membuat aplikasi tahu apakah pesan perlu didekripsi Vigenère saat diekstrak.
- Kapasitas: `lebar × tinggi × 3 / 8 − 9` byte (mis. 800×600 ≈ 180 KB).
- Key boleh dikosongkan saat menyisipkan (pesan disisipkan tanpa enkripsi).
- Hasil **harus disimpan sebagai PNG**. JPEG atau kompresi ulang merusak bit LSB.
- Transparansi (alpha) pada gambar cover dihapus karena hasil disimpan sebagai PNG RGB.

API (multipart/form-data):
```text
POST /api/stego/embed    field: image, text, key(opsional)  -> gambar PNG (data URL base64) + ciphertext
POST /api/stego/extract  field: image, key                   -> teks terambil + plaintext
```

## 5. Project Structure
```text
vigenere-cipher/
├── app.py                 # Flask app & API route
├── cipher/
│   ├── __init__.py
│   ├── vigenere.py        # Logika Vigenère (murni Python)
│   └── stego.py           # Steganografi LSB (Pillow untuk baca/tulis gambar)
├── templates/index.html
├── static/css/style.css
├── static/js/script.js
├── static/js/stego.js     # UI steganografi
├── tests/test_vigenere.py
├── tests/test_stego.py
├── requirements.txt
└── README.md
```

## 6. Installation
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 7. How to Run
```bash
python app.py
```
Buka http://127.0.0.1:5000

Menjalankan test:
```bash
python -m unittest -v tests.test_vigenere tests.test_stego
```

## 8. Example Encryption
```text
Plaintext  : HELLO WORLD
Key        : KEY
Ciphertext : RIJVS UYVJN
```
Contoh huruf pertama: H = 7, K = 10, (7 + 10) mod 26 = 17 = R.

## 9. Example Decryption
```text
Ciphertext : RIJVS UYVJN
Key        : KEY
Plaintext  : HELLO WORLD
```
Contoh nilai negatif: B - Z = 1 - 25 = -24, lalu (-24 + 26) mod 26 = 2 = C.

## 10. Technologies Used
Python 3, Flask, Pillow (hanya untuk baca/tulis gambar), HTML5, CSS3, JavaScript (vanilla).