import unittest

from app import app
from cipher import VigenereError, decrypt, encrypt, generate_process, normalize_key


class VigenereCoreTests(unittest.TestCase):
    def test_encrypt_example(self):
        self.assertEqual(encrypt("HELLO WORLD", "KEY"), "RIJVS UYVJN")

    def test_decrypt_example(self):
        self.assertEqual(decrypt("RIJVS UYVJN", "KEY"), "HELLO WORLD")

    def test_hello_keyke(self):
        self.assertEqual(encrypt("HELLO", "KEYKE"), "RIJVS")

    def test_key_repeats_and_skips_non_letters(self):
        out = generate_process("HELLO, WORLD!", "KEY", "encrypt")
        self.assertEqual(out["effective_key"], "KEYKE, YKEYK!")
        self.assertEqual(out["result"], "RIJVS, UYVJN!")

    def test_preserve_case_digits_punctuation(self):
        self.assertEqual(encrypt("Hello, World! 123", "KEY"), "Rijvs, Uyvjn! 123")
        self.assertEqual(decrypt("Rijvs, Uyvjn! 123", "key"), "Hello, World! 123")

    def test_negative_modulo(self):
        out = generate_process("B", "Z", "decrypt")
        self.assertEqual(out["result"], "C")
        step = out["process"][0]
        self.assertEqual(step["raw_value"], -24)
        self.assertEqual(step["output_value"], 2)

    def test_round_trip(self):
        text = "The Quick Brown Fox, jumps over 13 lazy dogs!"
        self.assertEqual(decrypt(encrypt(text, "Cipher"), "Cipher"), text)

    def test_process_first_row(self):
        step = generate_process("HELLO", "KEY", "encrypt")["process"][0]
        self.assertEqual(step["position"], 1)
        self.assertEqual(step["input"], "H")
        self.assertEqual(step["key"], "K")
        self.assertEqual(step["input_value"], 7)
        self.assertEqual(step["key_value"], 10)
        self.assertEqual(step["operation"], "(7 + 10) % 26")
        self.assertEqual(step["output"], "R")

    def test_key_validation(self):
        with self.assertRaises(VigenereError):
            normalize_key("")
        with self.assertRaises(VigenereError):
            normalize_key("   ")
        with self.assertRaises(VigenereError):
            normalize_key("123!?")
        self.assertEqual(normalize_key("K-E y1"), "KEY")


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_index_page(self):
        self.assertEqual(self.client.get("/").status_code, 200)

    def test_api_encrypt(self):
        res = self.client.post("/api/encrypt", json={"text": "HELLO WORLD", "key": "KEY"})
        data = res.get_json()
        self.assertEqual(res.status_code, 200)
        self.assertTrue(data["success"])
        self.assertEqual(data["result"], "RIJVS UYVJN")
        self.assertEqual(len(data["process"]), 10)

    def test_api_decrypt(self):
        res = self.client.post("/api/decrypt", json={"text": "RIJVS UYVJN", "key": "KEY"})
        self.assertEqual(res.get_json()["result"], "HELLO WORLD")

    def test_api_errors(self):
        for payload in (
            {"text": "HELLO", "key": ""},
            {"text": "HELLO", "key": "123"},
            {"text": "   ", "key": "KEY"},
            {"text": "HELLO"},
        ):
            res = self.client.post("/api/encrypt", json=payload)
            self.assertEqual(res.status_code, 400)
            self.assertFalse(res.get_json()["success"])

    def test_api_invalid_body(self):
        res = self.client.post("/api/encrypt", data="bukan json", content_type="text/plain")
        self.assertEqual(res.status_code, 400)

    def test_api_key_with_symbols_gives_warning(self):
        res = self.client.post("/api/encrypt", json={"text": "HELLO", "key": "K-E-Y"})
        data = res.get_json()
        self.assertEqual(data["key"], "KEY")
        self.assertTrue(data["warnings"])


if __name__ == "__main__":
    unittest.main()