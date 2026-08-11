import hashlib
import json
import struct
import unittest
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "assets/wave1/whisperwood/icons/WHISPERWOOD_RESOURCE_ICON_RECEIPT.json"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decode_rgba_png(path):
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("bad PNG signature")
    offset, width, height, compressed = 8, None, None, bytearray()
    while offset < len(data):
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        kind = data[offset + 4:offset + 8]
        payload = data[offset + 8:offset + 8 + length]
        crc = struct.unpack(">I", data[offset + 8 + length:offset + 12 + length])[0]
        if zlib.crc32(kind + payload) & 0xFFFFFFFF != crc:
            raise ValueError("bad PNG chunk CRC")
        offset += 12 + length
        if kind == b"IHDR":
            width, height, depth, color, compression, filtering, interlace = struct.unpack(">IIBBBBB", payload)
            if (depth, color, compression, filtering, interlace) != (8, 6, 0, 0, 0):
                raise ValueError("expected non-interlaced 8-bit RGBA")
        elif kind == b"IDAT":
            compressed.extend(payload)
        elif kind == b"IEND":
            break
    raw = zlib.decompress(bytes(compressed))
    stride, prior, rows = width * 4, bytearray(width * 4), []
    if len(raw) != height * (stride + 1):
        raise ValueError("decoded row length mismatch")
    cursor = 0
    for _ in range(height):
        filter_type, cursor = raw[cursor], cursor + 1
        scan = bytearray(raw[cursor:cursor + stride])
        cursor += stride
        for index in range(stride):
            left = scan[index - 4] if index >= 4 else 0
            up = prior[index]
            upper_left = prior[index - 4] if index >= 4 else 0
            if filter_type == 1:
                scan[index] = (scan[index] + left) & 255
            elif filter_type == 2:
                scan[index] = (scan[index] + up) & 255
            elif filter_type == 3:
                scan[index] = (scan[index] + ((left + up) // 2)) & 255
            elif filter_type == 4:
                estimate = left + up - upper_left
                distances = abs(estimate - left), abs(estimate - up), abs(estimate - upper_left)
                predictor = left if distances[0] <= distances[1] and distances[0] <= distances[2] else up if distances[1] <= distances[2] else upper_left
                scan[index] = (scan[index] + predictor) & 255
            elif filter_type != 0:
                raise ValueError("unknown PNG filter")
        rows.append(bytes(scan))
        prior = scan
    return width, height, b"".join(rows)


class WhisperwoodResourceIconReceiptTests(unittest.TestCase):
    def test_receipt_is_derived_from_exact_decodable_bytes(self):
        receipt = json.loads(RECEIPT.read_text())
        self.assertEqual(10, len(receipt["icons"]))
        for entry in receipt["icons"]:
            asset = entry["id"]
            source_name = "whisper_bark-chroma.png" if asset == "whisper_bark" else f"{asset}-chroma.png"
            source = ROOT / "assets/wave1/whisperwood/icons/source" / source_name
            shipping = ROOT / "resource_pack/textures/aionbound/whisperwood/items" / f"{asset}.png"
            self.assertEqual(entry["source_sha256"], sha256(source))
            self.assertEqual(entry["shipping_sha256"], sha256(shipping))
            width, height, rgba = decode_rgba_png(shipping)
            self.assertEqual((128, 128), (width, height))
            corner_alpha = [rgba[3], rgba[(width - 1) * 4 + 3], rgba[(height - 1) * width * 4 + 3], rgba[(height * width - 1) * 4 + 3]]
            self.assertEqual([0, 0, 0, 0], corner_alpha)


if __name__ == "__main__":
    unittest.main()
