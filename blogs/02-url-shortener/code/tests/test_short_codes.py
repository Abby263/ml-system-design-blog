import unittest

from app.short_codes import (
    encode_base62,
    normalize_target_url,
    validate_custom_alias,
)


class Base62Tests(unittest.TestCase):
    def test_known_boundaries(self) -> None:
        self.assertEqual(encode_base62(0), "0")
        self.assertEqual(encode_base62(61), "Z")
        self.assertEqual(encode_base62(62), "10")
        self.assertEqual(encode_base62(62**6), "1000000")

    def test_rejects_negative_values(self) -> None:
        with self.assertRaises(ValueError):
            encode_base62(-1)


class ValidationTests(unittest.TestCase):
    def test_normalizes_scheme_and_hostname(self) -> None:
        self.assertEqual(
            normalize_target_url(" HTTPS://Example.COM/docs?q=1#intro "),
            "https://example.com/docs?q=1#intro",
        )

    def test_adds_root_path(self) -> None:
        self.assertEqual(normalize_target_url("https://example.com"), "https://example.com/")

    def test_rejects_non_http_scheme(self) -> None:
        with self.assertRaisesRegex(ValueError, "only http and https"):
            normalize_target_url("javascript:alert(1)")

    def test_rejects_credentials(self) -> None:
        with self.assertRaisesRegex(ValueError, "credentials"):
            normalize_target_url("https://user:secret@example.com/")

    def test_custom_alias_contract(self) -> None:
        self.assertEqual(validate_custom_alias("launch_2026"), "launch_2026")
        with self.assertRaises(ValueError):
            validate_custom_alias("no spaces")

    def test_rejects_reserved_alias(self) -> None:
        with self.assertRaisesRegex(ValueError, "reserved"):
            validate_custom_alias("metrics")

    def test_rejects_invalid_port(self) -> None:
        with self.assertRaisesRegex(ValueError, "invalid port"):
            normalize_target_url("https://example.com:not-a-port/")

    def test_preserves_ipv6_brackets(self) -> None:
        self.assertEqual(normalize_target_url("http://[::1]:8080/a"), "http://[::1]:8080/a")


if __name__ == "__main__":
    unittest.main()
