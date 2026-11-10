"""Regression suite for tiff_bek128_validator.py.

Run: python -m unittest -v test_tiff_bek128_validator.py
The production OptReport module is stubbed only if it is unavailable.
"""
from __future__ import annotations

import struct
import sys
import tempfile
import types
import unittest
from pathlib import Path

import numpy as np
import tifffile
from PIL import Image

try:
    from avid_validator.common.report import OptReport, fail, ok
except ModuleNotFoundError:
    root = types.ModuleType("avid_validator")
    common = types.ModuleType("avid_validator.common")
    report = types.ModuleType("avid_validator.common.report")
    report.OptReport = tuple
    report.fail = lambda m: ("FAIL", m)
    report.ok = lambda: ("OK",)
    sys.modules.update({"avid_validator": root,
                        "avid_validator.common": common,
                        "avid_validator.common.report": report})

from avid_validator.common.tiff import analyze_tiff_bek128, check_tiff_bek128_bitdepths


def patch_classic_tag(path: Path, code: int, *, field_value: int | None = None,
                      value_type: int | None = None, count: int | None = None) -> None:
    data = bytearray(path.read_bytes())
    fmt = "<" if data[:2] == b"II" else ">"
    offset = struct.unpack_from(fmt + "I", data, 4)[0]
    count_tags = struct.unpack_from(fmt + "H", data, offset)[0]
    for idx in range(count_tags):
        pos = offset + 2 + idx * 12
        tag = struct.unpack_from(fmt + "H", data, pos)[0]
        if tag == code:
            if field_value is not None:
                struct.pack_into(fmt + "I", data, pos + 8, field_value)
            if value_type is not None:
                struct.pack_into(fmt + "H", data, pos + 2, value_type)
            if count is not None:
                struct.pack_into(fmt + "I", data, pos + 4, count)
            path.write_bytes(data)
            return
    raise LookupError(f"Tag {code} was not present")


class ValidateTiffTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "sample.tif"

    def save(self, mode="RGB", compression="tiff_lzw", dpi=(300, 300)):
        picture = Image.new(mode, (24, 32), 0 if mode in ("1", "L", "P") else (30, 40, 50, 60) if mode in ("RGBA", "CMYK") else (30, 40, 50))
        picture.save(self.path, compression=compression, dpi=dpi)

    def inspect(self, aspect=0.75, reviewed=True):
        return analyze_tiff_bek128(self.path,
                                   original_page_aspect_ratios=None if aspect is None else [aspect],
                                   quality_and_readability_reviewed_pages={0} if reviewed else None)

    def assert_violation(self, code):
        found = self.inspect()
        self.assertTrue(any(f.severity == "ERROR" and code in f.section for f in found.findings), [str(f) for f in found.findings])

    def test_valid_layouts(self):
        for mode in ("RGB", "RGBA", "CMYK", "L", "P"):
            with self.subTest(mode=mode):
                self.save(mode)
                found = self.inspect()
                self.assertTrue(found.fully_verified, [str(f) for f in found.findings])

    def test_group4_monochrome(self):
        self.save("1", compression="group4")
        self.assertTrue(self.inspect().fully_verified)

    def test_packbits(self):
        self.save("RGB", compression="packbits")
        self.assertTrue(self.inspect().fully_verified)

    def test_group3_monochrome(self):
        self.save("1", compression="group3")
        self.assertTrue(self.inspect().fully_verified)

    def test_single_sample_cannot_claim_rgb_or_cmyk(self):
        for photo in (2, 5):
            with self.subTest(photo=photo):
                self.save("L")
                patch_classic_tag(self.path, 262, field_value=photo)
                found = self.inspect()
                self.assertTrue(any(f.severity == "ERROR" and
                                    "5.E.3/5.E.4" in f.section for f in found.findings),
                                [str(f) for f in found.findings])

    def test_uncompressed_is_disallowed(self):
        self.save("RGB", compression="raw")
        self.assert_violation("5.E.2")

    def test_big_tiff_not_classic_tiff(self):
        tifffile.imwrite(self.path, np.zeros((10, 10), dtype=np.uint8), bigtiff=True)
        self.assert_violation("5.E.1")

    def test_no_ifd(self):
        self.path.write_bytes(b"II*\0\0\0\0\0")
        self.assert_violation("5.E.1")

    def test_bad_strip_offset(self):
        self.save("RGB")
        patch_classic_tag(self.path, 273, field_value=0xFFFFFF00)
        self.assert_violation("5.E.1")

    def test_bad_palette_colormap_count(self):
        self.save("P")
        patch_classic_tag(self.path, 320, count=3)
        self.assert_violation("5.E.1")

    def test_unspecified_fourth_rgb_channel(self):
        self.save("RGBA")
        patch_classic_tag(self.path, 338, field_value=0)
        self.assert_violation("5.E.3.a")

    def test_wrong_alpha_metadata(self):
        self.save("RGBA")
        patch_classic_tag(self.path, 338, field_value=3)
        self.assert_violation("5.E.3.a")

    def test_invalid_rgb_bit_depth(self):
        self.save("RGB")
        # Change the first BitsPerSample component from 8 to 16 in its array.
        data = bytearray(self.path.read_bytes())
        fmt = "<" if data[:2] == b"II" else ">"
        offset = struct.unpack_from(fmt + "I", data, 4)[0]
        n = struct.unpack_from(fmt + "H", data, offset)[0]
        for j in range(n):
            pos = offset + 2 + j * 12
            if struct.unpack_from(fmt + "H", data, pos)[0] == 258:
                address = struct.unpack_from(fmt + "I", data, pos + 8)[0]
                struct.pack_into(fmt + "H", data, address, 16)
                self.path.write_bytes(data)
                break
        self.assert_violation("5.E.3")

    def test_wrong_original_aspect_ratio(self):
        self.save("RGB")
        result = self.inspect(aspect=2.0)
        self.assertTrue(any(f.section == "5.E.5" and f.severity == "ERROR" for f in result.findings))

    def test_unequal_dpi_is_allowed_when_geometry_correct(self):
        self.save("RGB", dpi=(600, 96))
        true_aspect = (24 / 600) / (32 / 96)
        result = self.inspect(aspect=true_aspect)
        self.assertTrue(result.fully_verified, [str(f) for f in result.findings])

    def test_unverified_original_is_review_not_pass(self):
        self.save("RGB")
        result = self.inspect(aspect=None, reviewed=False)
        self.assertFalse(result.fully_verified)
        self.assertTrue(result.automatic_checks_pass)
        self.assertEqual(len(result.reviews), 2)
        self.assertTrue(len(list(check_tiff_bek128_bitdepths(self.path))) >= 2)

    def test_decode_finds_damaged_image_data(self):
        self.save("RGB")
        with tifffile.TiffFile(self.path) as t:
            off, size = t.pages[0].dataoffsets[0], t.pages[0].databytecounts[0]
        data = bytearray(self.path.read_bytes())
        data[off:off+size] = b"\0" * size
        self.path.write_bytes(data)
        errors = self.inspect().errors
        self.assertTrue(any("decode" in f.message for f in errors), [str(f) for f in errors])

    def test_tiff_without_resolution_fails(self):
        # tifffile writes a minimal noncompressed TIFF with no explicit DPI;
        # it fails 5.E.2 and must also fail 5.E.5.
        tifffile.imwrite(self.path, np.zeros((10, 10), dtype=np.uint8), metadata=None)
        result = self.inspect()
        self.assertTrue(any(f.section == "5.E.5" and f.severity == "ERROR" for f in result.findings))

    def test_original_entry_point_clean_pass_with_evidence(self):
        self.save("RGB")
        reports = list(check_tiff_bek128_bitdepths(
            self.path, original_page_aspect_ratios=[0.75],
            quality_and_readability_reviewed_pages={0}))
        self.assertEqual(len(reports), 1)
