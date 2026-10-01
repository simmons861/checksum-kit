import io
import os
import tempfile
import unittest
import zlib

from checksum_kit import crc32_stream, adler32_stream


class TestRoundtrip(unittest.TestCase):
    """Verify the streaming functions match zlib's all-at-once checksums."""

    def test_crc32_known_strings(self):
        self.assertEqual(crc32_stream(io.BytesIO(b"")), 0)
        self.assertEqual(crc32_stream(io.BytesIO(b"a")), zlib.crc32(b"a"))
        self.assertEqual(
            crc32_stream(io.BytesIO(b"The quick brown fox")),
            zlib.crc32(b"The quick brown fox"),
        )

    def test_adler32_known_strings(self):
        self.assertEqual(adler32_stream(io.BytesIO(b"")), 1)
        self.assertEqual(adler32_stream(io.BytesIO(b"a")), zlib.adler32(b"a"))
        self.assertEqual(
            adler32_stream(io.BytesIO(b"The quick brown fox")),
            zlib.adler32(b"The quick brown fox"),
        )


class TestLargeInput(unittest.TestCase):
    """The whole point of the library: large inputs fit in bounded memory."""

    def test_large_file_crc32(self):
        data = os.urandom(5 * 1024 * 1024)  # 5 MB
        self.assertEqual(crc32_stream(io.BytesIO(data)), zlib.crc32(data))

    def test_large_file_adler32(self):
        data = os.urandom(5 * 1024 * 1024)
        self.assertEqual(adler32_stream(io.BytesIO(data)), zlib.adler32(data))

    def test_small_chunk_matches_large_chunk(self):
        """Different chunk sizes must yield the same checksum."""
        data = os.urandom(256 * 1024)
        a = crc32_stream(io.BytesIO(data), chunk_size=1)
        b = crc32_stream(io.BytesIO(data), chunk_size=4096)
        c = crc32_stream(io.BytesIO(data), chunk_size=10 * 1024 * 1024)
        self.assertEqual(a, b)
        self.assertEqual(b, c)

        d = adler32_stream(io.BytesIO(data), chunk_size=1)
        e = adler32_stream(io.BytesIO(data), chunk_size=4096)
        f = adler32_stream(io.BytesIO(data), chunk_size=10 * 1024 * 1024)
        self.assertEqual(d, e)
        self.assertEqual(e, f)


class TestRealFile(unittest.TestCase):
    """Exercise the realistic path: a real file on disk."""

    def test_real_file_matches_bytesio(self):
        data = os.urandom(100_000)
        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(data)
            tmp.flush()
            with open(tmp.name, "rb") as f:
                self.assertEqual(crc32_stream(f), zlib.crc32(data))
            with open(tmp.name, "rb") as f:
                self.assertEqual(adler32_stream(f), zlib.adler32(data))


class TestInvalidChunkSize(unittest.TestCase):
    """Guardrail tests for the explicit validation we added."""

    def test_crc32_zero_chunk_raises(self):
        with self.assertRaises(ValueError):
            crc32_stream(io.BytesIO(b"abc"), chunk_size=0)

    def test_crc32_negative_chunk_raises(self):
        with self.assertRaises(ValueError):
            crc32_stream(io.BytesIO(b"abc"), chunk_size=-1)

    def test_adler32_zero_chunk_raises(self):
        with self.assertRaises(ValueError):
            adler32_stream(io.BytesIO(b"abc"), chunk_size=0)

    def test_adler32_negative_chunk_raises(self):
        with self.assertRaises(ValueError):
            adler32_stream(io.BytesIO(b"abc"), chunk_size=-1)


class TestReturnType(unittest.TestCase):
    """Confirm we return unsigned ints, not signed or wrapped values."""

    def test_return_types(self):
        c = crc32_stream(io.BytesIO(b"hello"))
        a = adler32_stream(io.BytesIO(b"hello"))
        self.assertIsInstance(c, int)
        self.assertIsInstance(a, int)
        self.assertGreaterEqual(c, 0)
        self.assertGreaterEqual(a, 0)
        self.assertLess(c, 2**32)
        self.assertLess(a, 2**32)


if __name__ == "__main__":
    unittest.main()
