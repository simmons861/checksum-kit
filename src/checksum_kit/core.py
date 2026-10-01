"""Streaming CRC-32 and Adler-32 for files too large to read whole.

Both implementations read the input in fixed-size chunks and feed each chunk
to the corresponding zlib incremental function. zlib already knows how to
compute these checksums; our only job is to stream the bytes in. Doing it
ourselves rather than using ``zlib.crc32(data)`` on the full buffer keeps
peak memory bounded by ``chunk_size``, regardless of how large the file is.
"""

import os
import zlib

# A million bytes is a reasonable default: small enough for constrained
# environments and large enough to keep Python-level loop overhead low.
_DEFAULT_CHUNK = 1024 * 1024


def _iter_chunks(fileobj, chunk_size):
    """Yield successive byte blocks from ``fileobj``.

    We never seek — many stream sources (pipes, sockets, stdin) are
    non-seekable. We read until EOF only.
    """
    while True:
        block = fileobj.read(chunk_size)
        if not block:
            break
        yield block


def crc32_stream(source, chunk_size=_DEFAULT_CHUNK):
    """Compute the CRC-32 (polynomial used by zlib/PNG) of ``source``.

    ``source`` is any binary file object opened in ``'rb'`` mode: a real file,
    a ``io.BytesIO``, or anything that has a ``read(n)`` returning ``bytes``.

    Returns an unsigned 32-bit integer in the range ``[0, 2**32-1]``.

    The state is carried through zlib's incremental API by passing the
    previous value as the second argument on each call; this is the idiomatic
    and fastest way to compute CRC-32 over a long stream in CPython.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    value = 0
    for block in _iter_chunks(source, chunk_size):
        value = zlib.crc32(block, value)
    return value & 0xFFFFFFFF


def adler32_stream(source, chunk_size=_DEFAULT_CHUNK):
    """Compute the Adler-32 checksum of ``source``.

    ``source`` is any binary file object: a real file, a ``io.BytesIO``, or
    anything exposing ``read(n)`` -> ``bytes``.

    Returns an unsigned 32-bit integer in the range ``[0, 2**32-1]``.

    Like ``crc32_stream``, we thread the running value through zlib's
    incremental API to avoid buffering the entire stream in memory.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    value = 1
    for block in _iter_chunks(source, chunk_size):
        value = zlib.adler32(block, value)
    return value & 0xFFFFFFFF
