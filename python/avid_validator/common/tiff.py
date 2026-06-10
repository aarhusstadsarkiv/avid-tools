from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Generator, Union

import tifffile

from avid_validator.common.report import OptReport, fail, ok


# TIFF PhotometricInterpretation values
WHITE_IS_ZERO = 0
BLACK_IS_ZERO = 1
RGB = 2
PALETTE = 3
CMYK = 5

# TIFF Compression values
CCITT_GROUP3 = 3
CCITT_GROUP4 = 4
LZW = 5
PACKBITS = 32773


@dataclass(frozen=True)
class LayoutRule:
    name: str
    photometric: frozenset[int]
    bits_per_sample: tuple[int, ...]
    samples_per_pixel: int
    allowed_compressions: frozenset[int]


_ALLOWED_LAYOUTS: tuple[LayoutRule, ...] = (
    # 1-bit monochrome
    LayoutRule(
        name="FAX_MONO",
        photometric=frozenset({WHITE_IS_ZERO, BLACK_IS_ZERO}),
        bits_per_sample=(1,),
        samples_per_pixel=1,
        allowed_compressions=frozenset({CCITT_GROUP3, CCITT_GROUP4, LZW, PACKBITS}),
    ),
    # Grayscale
    LayoutRule(
        name="GRAY 2",
        photometric=frozenset({WHITE_IS_ZERO, BLACK_IS_ZERO}),
        bits_per_sample=(2,),
        samples_per_pixel=1,
        allowed_compressions=frozenset({LZW, PACKBITS}),
    ),
    LayoutRule(
        name="GRAY 4",
        photometric=frozenset({WHITE_IS_ZERO, BLACK_IS_ZERO}),
        bits_per_sample=(4,),
        samples_per_pixel=1,
        allowed_compressions=frozenset({LZW, PACKBITS}),
    ),
    LayoutRule(
        name="GRAY 8",
        photometric=frozenset({WHITE_IS_ZERO, BLACK_IS_ZERO}),
        bits_per_sample=(8,),
        samples_per_pixel=1,
        allowed_compressions=frozenset({LZW, PACKBITS}),
    ),
    # Palette
    LayoutRule(
        name="PALETTE 1",
        photometric=frozenset({PALETTE}),
        bits_per_sample=(1,),
        samples_per_pixel=1,
        allowed_compressions=frozenset({LZW, PACKBITS}),
    ),
    LayoutRule(
        name="PALETTE 2",
        photometric=frozenset({PALETTE}),
        bits_per_sample=(2,),
        samples_per_pixel=1,
        allowed_compressions=frozenset({LZW, PACKBITS}),
    ),
    LayoutRule(
        name="PALETTE 4",
        photometric=frozenset({PALETTE}),
        bits_per_sample=(4,),
        samples_per_pixel=1,
        allowed_compressions=frozenset({LZW, PACKBITS}),
    ),
    LayoutRule(
        name="PALETTE 8",
        photometric=frozenset({PALETTE}),
        bits_per_sample=(8,),
        samples_per_pixel=1,
        allowed_compressions=frozenset({LZW, PACKBITS}),
    ),
    # RGB total bit depths allowed by the regulation: 1, 2, 4, 8, 24, 32
    LayoutRule(
        name="RGB 1",
        photometric=frozenset({RGB}),
        bits_per_sample=(1,),
        samples_per_pixel=1,
        allowed_compressions=frozenset({LZW, PACKBITS}),
    ),
    LayoutRule(
        name="RGB 2",
        photometric=frozenset({RGB}),
        bits_per_sample=(2,),
        samples_per_pixel=1,
        allowed_compressions=frozenset({LZW, PACKBITS}),
    ),
    LayoutRule(
        name="RGB 4",
        photometric=frozenset({RGB}),
        bits_per_sample=(4,),
        samples_per_pixel=1,
        allowed_compressions=frozenset({LZW, PACKBITS}),
    ),
    LayoutRule(
        name="RGB 8",
        photometric=frozenset({RGB}),
        bits_per_sample=(8,),
        samples_per_pixel=1,
        allowed_compressions=frozenset({LZW, PACKBITS}),
    ),
    LayoutRule(
        name="RGB 8,8,8",
        photometric=frozenset({RGB}),
        bits_per_sample=(8, 8, 8),
        samples_per_pixel=3,
        allowed_compressions=frozenset({LZW, PACKBITS}),
    ),
    LayoutRule(
        name="RGB 8,8,8,8",
        photometric=frozenset({RGB}),
        bits_per_sample=(8, 8, 8, 8),
        samples_per_pixel=4,
        allowed_compressions=frozenset({LZW, PACKBITS}),
    ),
    # CMYK total bit depths allowed by the regulation: 1, 2, 4, 8, 32, 40
    LayoutRule(
        name="CMYK 1",
        photometric=frozenset({CMYK}),
        bits_per_sample=(1,),
        samples_per_pixel=1,
        allowed_compressions=frozenset({LZW, PACKBITS}),
    ),
    LayoutRule(
        name="CMYK 2",
        photometric=frozenset({CMYK}),
        bits_per_sample=(2,),
        samples_per_pixel=1,
        allowed_compressions=frozenset({LZW, PACKBITS}),
    ),
    LayoutRule(
        name="CMYK 4",
        photometric=frozenset({CMYK}),
        bits_per_sample=(4,),
        samples_per_pixel=1,
        allowed_compressions=frozenset({LZW, PACKBITS}),
    ),
    LayoutRule(
        name="CMYK 8",
        photometric=frozenset({CMYK}),
        bits_per_sample=(8,),
        samples_per_pixel=1,
        allowed_compressions=frozenset({LZW, PACKBITS}),
    ),
    LayoutRule(
        name="CMYK 8,8,8,8",
        photometric=frozenset({CMYK}),
        bits_per_sample=(8, 8, 8, 8),
        samples_per_pixel=4,
        allowed_compressions=frozenset({LZW, PACKBITS}),
    ),
    LayoutRule(
        name="CMYK 8,8,8,8,8",
        photometric=frozenset({CMYK}),
        bits_per_sample=(8, 8, 8, 8, 8),
        samples_per_pixel=5,
        allowed_compressions=frozenset({LZW, PACKBITS}),
    ),
)


def _get_tag_value(page: tifffile.TiffPage, tag_name: str) -> Any | None:
    tag = page.tags.get(tag_name)
    return None if tag is None else tag.value


def _normalize_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _normalize_bps(value: Any) -> tuple[int, ...] | None:
    if value is None:
        return None
    if isinstance(value, int):
        return (value,)
    if isinstance(value, (tuple, list)):
        try:
            return tuple(int(x) for x in value)
        except (TypeError, ValueError):
            return None
    return None


def _match_layout(
    photometric: int, samples_per_pixel: int, bits_per_sample: tuple[int, ...], compression: int
) -> LayoutRule | None:
    for rule in _ALLOWED_LAYOUTS:
        if (
            photometric in rule.photometric
            and samples_per_pixel == rule.samples_per_pixel
            and bits_per_sample == rule.bits_per_sample
            and compression in rule.allowed_compressions
        ):
            return rule
    return None


def check_tiff_bek128_bitdepths(path: Union[str, Path]) -> Generator[OptReport, None, None]:
    """
    Validate TIFF pages against allowed bit-depth / color-model / compression combinations.

    This checks only the combinations encoded in _ALLOWED_LAYOUTS.
    It does not validate other archival constraints such as resolution,
    ICC profiles, strip/tile organization, etc.
    """
    p = Path(path)

    if not p.exists():
        yield fail(f"File not found: {p}")
        return

    had_failures = False

    def _fail(message):
        return fail(f"{path}: {message}")

    try:
        with tifffile.TiffFile(str(p)) as tif:
            for page_index, page in enumerate(tif.pages):
                photometric_raw = _get_tag_value(page, "PhotometricInterpretation")
                compression_raw = _get_tag_value(page, "Compression")
                spp_raw = _get_tag_value(page, "SamplesPerPixel")
                bps_raw = _get_tag_value(page, "BitsPerSample")

                photometric = _normalize_int(photometric_raw)
                compression = _normalize_int(compression_raw)
                samples_per_pixel = _normalize_int(spp_raw)
                bits_per_sample = _normalize_bps(bps_raw)

                missing = [
                    name
                    for name, value in (
                        ("PhotometricInterpretation", photometric_raw),
                        ("Compression", compression_raw),
                        ("SamplesPerPixel", spp_raw),
                        ("BitsPerSample", bps_raw),
                    )
                    if value is None
                ]
                if missing:
                    had_failures = True
                    yield _fail(f"Page {page_index}: missing required TIFF tags: {', '.join(missing)}.")
                    continue

                if photometric is None:
                    had_failures = True
                    yield _fail(f"Page {page_index}: invalid PhotometricInterpretation value: {photometric_raw!r}.")
                    continue

                if compression is None:
                    had_failures = True
                    yield _fail(f"Page {page_index}: invalid Compression value: {compression_raw!r}.")
                    continue

                if samples_per_pixel is None:
                    had_failures = True
                    yield _fail(f"Page {page_index}: invalid SamplesPerPixel value: {spp_raw!r}.")
                    continue

                if bits_per_sample is None:
                    had_failures = True
                    yield _fail(f"Page {page_index}: invalid BitsPerSample value: {bps_raw!r}.")
                    continue

                rule = _match_layout(
                    photometric=photometric,
                    samples_per_pixel=samples_per_pixel,
                    bits_per_sample=bits_per_sample,
                    compression=compression,
                )

                if rule is None:
                    had_failures = True
                    yield _fail(
                        f"Page {page_index}: disallowed layout "
                        f"(PhotometricInterpretation={photometric}, "
                        f"SamplesPerPixel={samples_per_pixel}, "
                        f"BitsPerSample={bits_per_sample})."
                    )
                    continue

                if photometric == PALETTE:
                    colormap = _get_tag_value(page, "ColorMap")
                    if colormap is None:
                        had_failures = True
                        yield _fail(f"Page {page_index}: palette image missing ColorMap tag.")
                        continue

    except tifffile.TiffFileError as e:
        yield fail(f"Not a valid TIFF or could not read TIFF: {e}")
        return
    except Exception as e:
        yield fail(f"Unexpected error reading TIFF: {e}")
        return

    if not had_failures:
        yield ok()
