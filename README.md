# Checksum Kit

Computes CRC-32 and Adler-32 over any file-like object without loading the whole file into memory. Reads in fixed-size chunks and threads the running checksum through zlib's incremental API.

## Usage

```python
from checksum_kit import crc32_stream, adler32_stream

with open(__file__, "rb") as f:
    print(hex(crc32_stream(f)))
    print(hex(adler32_stream(f)))
```

Both functions accept any binary object with a `read(n)` method returning `bytes` (real files, `io.BytesIO`, pipes opened in binary mode). They return an unsigned 32-bit integer. You can override the chunk size via `chunk_size=`, which defaults to one megabyte.

## Why

The standard `zlib.crc32(data)` requires the entire input as a single `bytes` object. For files of multiple gigabytes that means holding the whole thing in RAM. This library keeps peak memory bounded by `chunk_size` while producing the identical checksum. The trade-off is throughput: a single C-level call is marginally faster than a Python loop over chunks, but the difference is negligible compared to the cost of reading the data from disk.

## Edge cases

- Empty input yields `0` for CRC-32 and `1` for Adler-32 — these are the canonical initial values, not bugs.
- `chunk_size` must be a positive integer; anything else raises `ValueError`.
- The source is never seeked; it must be a forward-readable binary stream.
