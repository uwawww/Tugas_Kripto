import base64
import io
import unittest

from PIL import Image

from app import app
from cipher import StegoError, capacity_bytes, embed, extract


def make_image(width=40, height=40, fmt="PNG", mode="RGB"):
    img = Image.new(mode, (width, height), (120, 60, 200) if mode == "RGB" else (120, 60, 200, 128))
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


class StegoCoreTests(unittest.TestCase):
    def test_capacity(self):
        self.assertEqual(capacity_bytes(40, 40), 40 * 40 * 3 // 8 - 9)

    def test_round_trip(self):
        png, info = embed(make_image(), "Halo dunia ✓".encode("utf-8"), encrypted=False)
        payload, encrypted = extract(png)
        self.assertEqual(payload.decode("utf-8"), "Halo dunia ✓")
        self.assertFalse(encrypted)
        self.assertEqual(info["payload_bytes"], len("Halo dunia ✓".encode("utf-8")))

    def test_encrypted_flag(self):
        png, _ = embed(make_image(), b"RIJVS", encrypted=True)
        self.assertEqual(extract(png), (b"RIJVS", True))

    def test_pixels_change_by_at_most_one(self):
        original = make_image()
        png, _ = embed(original, b"secret message", encrypted=False)
        a = Image.open(io.BytesIO(original)).convert("RGB").tobytes()
        b = Image.open(io.BytesIO(png)).convert("RGB").tobytes()
        self.assertTrue(all(abs(x - y) <= 1 for x, y in zip(a, b)))

    def test_too_large_message(self):
        with self.assertRaises(StegoError):
            embed(make_image(10, 10), b"x" * 200)

    def test_empty_message(self):
        with self.assertRaises(StegoError):
            embed(make_image(), b"")

    def test_no_hidden_message(self):
        with self.assertRaises(StegoError):
            extract(make_image())

    def test_jpeg_destroys_message(self):
        png, _ = embed(make_image(), b"secret", encrypted=False)
        buf = io.BytesIO()
        Image.open(io.BytesIO(png)).save(buf, format="JPEG")
        with self.assertRaises(StegoError):
            extract(buf.getvalue())

    def test_invalid_image(self):
        with self.assertRaises(StegoError):
            embed(b"bukan gambar", b"x")

    def test_rgba_input_is_accepted(self):
        png, info = embed(make_image(mode="RGBA"), b"hi")
        self.assertTrue(info["had_alpha"])
        self.assertEqual(extract(png)[0], b"hi")


class StegoApiTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def embed(self, text="HELLO WORLD", key="KEY", image=None):
        data = {"text": text, "key": key, "image": (io.BytesIO(image or make_image()), "cover.png")}
        return self.client.post("/api/stego/embed", data=data, content_type="multipart/form-data")

    def extract(self, png_bytes, key="KEY"):
        data = {"key": key, "image": (io.BytesIO(png_bytes), "stego.png")}
        return self.client.post("/api/stego/extract", data=data, content_type="multipart/form-data")

    @staticmethod
    def decode_data_url(url):
        return base64.b64decode(url.split(",", 1)[1])

    def test_full_flow_with_vigenere(self):
        res = self.embed()
        data = res.get_json()
        self.assertEqual(res.status_code, 200)
        self.assertTrue(data["encrypted"])
        self.assertEqual(data["ciphertext"], "RIJVS UYVJN")

        res = self.extract(self.decode_data_url(data["image"]))
        out = res.get_json()
        self.assertEqual(out["extracted"], "RIJVS UYVJN")
        self.assertEqual(out["plaintext"], "HELLO WORLD")

    def test_wrong_key_gives_different_plaintext(self):
        png = self.decode_data_url(self.embed().get_json()["image"])
        out = self.extract(png, key="ABC").get_json()
        self.assertNotEqual(out["plaintext"], "HELLO WORLD")

    def test_extract_encrypted_requires_key(self):
        png = self.decode_data_url(self.embed().get_json()["image"])
        res = self.extract(png, key="")
        self.assertEqual(res.status_code, 400)

    def test_embed_without_key_is_plain(self):
        data = self.embed(key="").get_json()
        self.assertFalse(data["encrypted"])
        self.assertEqual(data["ciphertext"], "HELLO WORLD")
        out = self.extract(self.decode_data_url(data["image"]), key="").get_json()
        self.assertEqual(out["plaintext"], "HELLO WORLD")

    def test_errors(self):
        self.assertEqual(self.embed(text="   ").status_code, 400)
        self.assertEqual(self.embed(key="123").status_code, 400)
        self.assertEqual(self.embed(image=b"bukan gambar").status_code, 400)
        res = self.client.post("/api/stego/embed", data={"text": "hi"}, content_type="multipart/form-data")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(self.extract(make_image()).status_code, 400)


if __name__ == "__main__":
    unittest.main()
