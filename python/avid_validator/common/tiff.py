from __future__ import annotations

import math
import struct
from dataclasses import dataclass, field
from pathlib import Path
from PIL import Image
from typing import Generator, Literal, Mapping, Sequence, Union

import tifffile

from avid_validator.common.report import OptReport, fail, ok


PathLike = Union[str, Path]
Severity = Literal["ERROR", "REVIEW"]

# TIFF 6.0 tag numbers
IMAGE_WIDTH = 256
IMAGE_LENGTH = 257
BITS_PER_SAMPLE = 258
COMPRESSION = 259
PHOTOMETRIC = 262
FILL_ORDER = 266
STRIP_OFFSETS = 273
ORIENTATION = 274
SAMPLES_PER_PIXEL = 277
ROWS_PER_STRIP = 278
STRIP_BYTE_COUNTS = 279
X_RESOLUTION = 282
Y_RESOLUTION = 283
PLANAR_CONFIGURATION = 284
T4_OPTIONS = 292
T6_OPTIONS = 293
RESOLUTION_UNIT = 296
PREDICTOR = 317
COLOR_MAP = 320
TILE_WIDTH = 322
TILE_LENGTH = 323
TILE_OFFSETS = 324
TILE_BYTE_COUNTS = 325
INK_SET = 332
NUMBER_OF_INKS = 334
EXTRA_SAMPLES = 338
SAMPLE_FORMAT = 339

WHITE_IS_ZERO = 0
BLACK_IS_ZERO = 1
RGB = 2
PALETTE = 3
CMYK = 5

CCITT_GROUP3 = 3
CCITT_GROUP4 = 4
LZW = 5
PACKBITS = 32773

MONO_COMPRESSIONS = frozenset((CCITT_GROUP3, CCITT_GROUP4, LZW, PACKBITS))
COLOR_COMPRESSIONS = frozenset((LZW, PACKBITS))
ALPHA_TYPES = frozenset((1, 2))  # associated / unassociated alpha

# TIFF 6.0 (classic) tag types and their sizes in bytes.
_TYPE_SIZES = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 6: 1, 7: 1,
               8: 2, 9: 4, 10: 8, 11: 4, 12: 8}

# Tag types and cardinalities that are fixed by TIFF 6.0.  Counts which
# depend on image layout are checked separately below.
_TAG_SCHEMAS: dict[int, tuple[frozenset[int], frozenset[int] | None]] = {
    IMAGE_WIDTH: (frozenset((3, 4)), frozenset((1,))),
    IMAGE_LENGTH: (frozenset((3, 4)), frozenset((1,))),
    BITS_PER_SAMPLE: (frozenset((3,)), None),
    COMPRESSION: (frozenset((3,)), frozenset((1,))),
    PHOTOMETRIC: (frozenset((3,)), frozenset((1,))),
    FILL_ORDER: (frozenset((3,)), frozenset((1,))),
    STRIP_OFFSETS: (frozenset((3, 4)), None),
    ORIENTATION: (frozenset((3,)), frozenset((1,))),
    SAMPLES_PER_PIXEL: (frozenset((3,)), frozenset((1,))),
    ROWS_PER_STRIP: (frozenset((3, 4)), frozenset((1,))),
    STRIP_BYTE_COUNTS: (frozenset((3, 4)), None),
    X_RESOLUTION: (frozenset((5,)), frozenset((1,))),
    Y_RESOLUTION: (frozenset((5,)), frozenset((1,))),
    PLANAR_CONFIGURATION: (frozenset((3,)), frozenset((1,))),
    T4_OPTIONS: (frozenset((4,)), frozenset((1,))),
    T6_OPTIONS: (frozenset((4,)), frozenset((1,))),
    RESOLUTION_UNIT: (frozenset((3,)), frozenset((1,))),
    PREDICTOR: (frozenset((3,)), frozenset((1,))),
    COLOR_MAP: (frozenset((3,)), None),
    INK_SET: (frozenset((3,)), frozenset((1,))),
    NUMBER_OF_INKS: (frozenset((3,)), frozenset((1,))),
    EXTRA_SAMPLES: (frozenset((3,)), None),
    SAMPLE_FORMAT: (frozenset((3,)), None),
}


@dataclass(frozen=True)
class Finding:
    section: str
    message: str
    severity: Severity = "ERROR"
    page: int | None = None  # zero-based page index

    def __str__(self) -> str:
        where = f" page {self.page + 1}:" if self.page is not None else ":"
        return f"[{self.severity}] {self.section}{where} {self.message}"


@dataclass
class ValidationResult:
    path: Path
    page_count: int = 0
    findings: list[Finding] = field(default_factory=list)

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == "ERROR"]

    @property
    def automatic_checks_pass(self) -> bool:
        return not self.errors

    @property
    def fully_verified(self) -> bool:
        return not self.findings

    def add(self, section: str, message: str, *, page: int | None = None,
            severity: Severity = "ERROR") -> None:
        self.findings.append(Finding(section, message, severity, page))


def _tag(page: tifffile.TiffPage, code: int):
    return page.tags.get(code)


def _value(page: tifffile.TiffPage, code: int):
    entry = _tag(page, code)
    return entry.value if entry is not None else None


def _one_int(value: object) -> int | None:
    if isinstance(value, (tuple, list)):
        if len(value) != 1:
            return None
        value = value[0]
    try:
        number = int(value)  # TIFF fields may be enum integers
    except (ValueError, TypeError, OverflowError):
        return None
    return number


def _ints(value: object) -> tuple[int, ...] | None:
    if value is None:
        return None
    if isinstance(value, (tuple, list)):
        items = value
    elif hasattr(value, "tolist"):
        items = value.tolist()
        if not isinstance(items, list):
            items = [items]
    else:
        items = [value]
    try:
        if any(isinstance(v, (tuple, list)) for v in items):
            return None
        return tuple(int(v) for v in items)
    except (ValueError, TypeError, OverflowError):
        return None


def _positive_rational(value: object) -> float | None:
    try:
        if isinstance(value, (tuple, list)) and len(value) == 2:
            numerator, denominator = float(value[0]), float(value[1])
            if denominator <= 0:
                return None
            number = numerator / denominator
        else:
            number = float(value)
        if math.isfinite(number) and number > 0:
            return number
    except (ValueError, TypeError, ZeroDivisionError, OverflowError):
        pass
    return None


def _read_classic_ifds(path: Path, result: ValidationResult) -> int | None:
    """Check classic header, IFD chain, tag ordering, tag bounds and types.

    Returns the number of root IFDs if structural walking succeeded, else None.
    This is not a substitute for an independent full TIFF conformance parser.
    """
    size = path.stat().st_size
    if size < 8:
        result.add("5.E.1", "File is smaller than the 8-byte classic TIFF header.")
        return None
    with path.open("rb") as stream:
        header = stream.read(8)
        byteorder = header[:2]
        if byteorder not in (b"II", b"MM"):
            result.add("5.E.1", "Invalid TIFF byte order marker.")
            return None
        endian = "<" if byteorder == b"II" else ">"
        magic, offset = struct.unpack(endian + "HI", header[2:])
        if magic != 42:
            result.add("5.E.1", f"Not classic TIFF (magic={magic}; BigTIFF=43 is not permitted).")
            return None
        if offset == 0:
            result.add("5.E.1", "TIFF header does not reference an image directory.")
            return None

        visited: set[int] = set()
        ifd_count = 0
        while offset:
            if offset in visited:
                result.add("5.E.1", f"Cycle in TIFF IFD chain at byte offset {offset}.")
                return None
            visited.add(offset)
            if offset < 8 or offset + 2 > size:
                result.add("5.E.1", f"IFD offset {offset} lies outside the file.")
                return None
            stream.seek(offset)
            count_raw = stream.read(2)
            count = struct.unpack(endian + "H", count_raw)[0]
            end = offset + 2 + count * 12 + 4
            if end > size:
                result.add("5.E.1", f"IFD at {offset} extends past end of file.")
                return None
            previous_tag = -1
            for i in range(count):
                entry = stream.read(12)
                tag_id, dtype, elements, location = struct.unpack(endian + "HHII", entry)
                if tag_id <= previous_tag:
                    result.add("5.E.1", f"IFD {ifd_count + 1}: tag {tag_id} is duplicate or out of order.")
                previous_tag = tag_id
                if dtype not in _TYPE_SIZES:
                    result.add("5.E.1", f"IFD {ifd_count + 1}: tag {tag_id} uses non-TIFF-6 type {dtype}.")
                    continue
                if elements == 0:
                    result.add("5.E.1", f"IFD {ifd_count + 1}: tag {tag_id} has zero elements.")
                bytecount = _TYPE_SIZES[dtype] * elements
                if bytecount > 4 and (location < 8 or location + bytecount > size):
                    result.add("5.E.1", f"IFD {ifd_count + 1}: tag {tag_id} data lies outside file.")
                schema = _TAG_SCHEMAS.get(tag_id)
                if schema is not None:
                    types, counts = schema
                    if dtype not in types or (counts is not None and elements not in counts):
                        result.add("5.E.1", f"IFD {ifd_count + 1}: tag {tag_id} has invalid TIFF type/count ({dtype}, {elements}).")
            offset = struct.unpack(endian + "I", stream.read(4))[0]
            ifd_count += 1
    return ifd_count


def _validate_layout(page: tifffile.TiffPage, i: int, result: ValidationResult):
    """Returns (width, height, spp, compression, planar, bps) when usable."""
    width = _one_int(_value(page, IMAGE_WIDTH))
    height = _one_int(_value(page, IMAGE_LENGTH))
    if width is None or height is None or width <= 0 or height <= 0:
        result.add("5.E.1", f"Missing/invalid ImageWidth or ImageLength: {width!r} x {height!r}.", page=i)
        return None

    photo = _one_int(_value(page, PHOTOMETRIC))
    if photo is None:
        result.add("5.E.1", "Missing or invalid PhotometricInterpretation.", page=i)
        return None

    # TIFF 6.0 defaults: Compression=1; SamplesPerPixel=1; BitsPerSample=1.
    # A missing Compression is nevertheless noncompliant with 5.E.2, because
    # the default (uncompressed) is forbidden.
    compression = _one_int(_value(page, COMPRESSION))
    if compression is None:
        compression = 1 if _tag(page, COMPRESSION) is None else None
    spp = _one_int(_value(page, SAMPLES_PER_PIXEL)) if _tag(page, SAMPLES_PER_PIXEL) else 1
    raw_bps = _value(page, BITS_PER_SAMPLE)
    bps = _ints(raw_bps) if raw_bps is not None else (1,)
    if compression is None or spp is None or spp < 1 or bps is None:
        result.add("5.E.1", "Invalid Compression, SamplesPerPixel or BitsPerSample.", page=i)
        return None
    if len(bps) == 1 and spp > 1:
        # TIFF 6.0 BitsPerSample has no multi-channel replication convention.
        result.add("5.E.1", f"BitsPerSample must list all {spp} components; got {bps}.", page=i)
        return None
    if len(bps) != spp or any(b <= 0 for b in bps):
        result.add("5.E.1", f"BitsPerSample {bps} does not describe {spp} component(s).", page=i)
        return None

    planar = _one_int(_value(page, PLANAR_CONFIGURATION))
    if planar is None:
        planar = 1 if _tag(page, PLANAR_CONFIGURATION) is None else None
    if planar not in (1, 2):
        result.add("5.E.1", f"PlanarConfiguration must be 1 or 2; got {planar}.", page=i)
    fill = _one_int(_value(page, FILL_ORDER))
    if _tag(page, FILL_ORDER) is not None and fill not in (1, 2):
        result.add("5.E.1", f"FillOrder must be 1 or 2; got {fill}.", page=i)
    orient = _one_int(_value(page, ORIENTATION))
    if _tag(page, ORIENTATION) is not None and orient not in range(1, 9):
        result.add("5.E.1", f"Orientation must be in [1,8]; got {orient}.", page=i)

    fmt = _ints(_value(page, SAMPLE_FORMAT)) if _tag(page, SAMPLE_FORMAT) else (1,)
    if fmt is None or len(fmt) not in (1, spp) or any(f != 1 for f in fmt):
        result.add("5.E.1", f"Only unsigned-integer raster samples are supported; SampleFormat={fmt}.", page=i)

    # TIFF RGB and CMYK require 3 and 4 component channels, respectively;
    # 1/2/4/8-bit *total* depths are represented by grayscale/palette.
    if photo in (WHITE_IS_ZERO, BLACK_IS_ZERO):
        layout_ok = spp == 1 and bps in ((1,), (2,), (4,), (8,))
    elif photo == PALETTE:
        layout_ok = spp == 1 and bps in ((1,), (2,), (4,), (8,))
    elif photo == RGB:
        layout_ok = (spp, bps) in ((3, (8, 8, 8)), (4, (8, 8, 8, 8)))
    elif photo == CMYK:
        layout_ok = (spp, bps) in ((4, (8, 8, 8, 8)), (5, (8, 8, 8, 8, 8)))
    else:
        layout_ok = False
    if not layout_ok:
        result.add("5.E.3/5.E.4", f"Disallowed image layout: Photometric={photo}, SamplesPerPixel={spp}, BitsPerSample={bps}.", page=i)

    allowed = MONO_COMPRESSIONS if photo in (WHITE_IS_ZERO, BLACK_IS_ZERO) and bps == (1,) and spp == 1 else COLOR_COMPRESSIONS
    if compression not in allowed:
        result.add("5.E.2", f"Compression={compression} is not allowed for Photometric={photo}, BitsPerSample={bps}.", page=i)

    t4 = _one_int(_value(page, T4_OPTIONS)) if _tag(page, T4_OPTIONS) else None
    t6 = _one_int(_value(page, T6_OPTIONS)) if _tag(page, T6_OPTIONS) else None
    if t4 is not None and (compression != CCITT_GROUP3 or t4 & ~0b111):
        result.add("5.E.1", f"Invalid Group 3 T4Options={t4} for compression={compression}.", page=i)
    if t6 is not None and (compression != CCITT_GROUP4 or t6 & ~0b010):
        result.add("5.E.1", f"Invalid Group 4 T6Options={t6} for compression={compression}.", page=i)
    if _tag(page, T4_OPTIONS) and t4 is None:
        result.add("5.E.1", "Invalid T4Options value.", page=i)
    if _tag(page, T6_OPTIONS) and t6 is None:
        result.add("5.E.1", "Invalid T6Options value.", page=i)

    extra = _ints(_value(page, EXTRA_SAMPLES)) if _tag(page, EXTRA_SAMPLES) else ()
    expected_extras = (spp - 3) if photo == RGB else (spp - 4) if photo == CMYK else 0
    if expected_extras not in (0, 1) or extra is None or len(extra) != expected_extras or any(e not in ALPHA_TYPES for e in extra):
        result.add("5.E.3.a/5.E.4.a", f"ExtraSamples={extra} does not declare the allowed {expected_extras} alpha channel(s).", page=i)

    if photo == PALETTE:
        cmap = _tag(page, COLOR_MAP)
        entries = 3 * (1 << bps[0]) if bps[0] in (1, 2, 4, 8) else -1
        if cmap is None or cmap.count != entries or int(cmap.dtype) != 3:
            result.add("5.E.1", f"Palette ColorMap must contain {entries} 16-bit entries; got {None if cmap is None else cmap.count}.", page=i)
    if photo == CMYK:
        ink_set = _one_int(_value(page, INK_SET)) if _tag(page, INK_SET) else 1
        ink_count = _one_int(_value(page, NUMBER_OF_INKS)) if _tag(page, NUMBER_OF_INKS) else 4
        if ink_set != 1 or ink_count != 4:
            result.add("5.E.4.a", f"Separated-color image is not CMYK (InkSet={ink_set}, NumberOfInks={ink_count}).", page=i)

    predictor = _one_int(_value(page, PREDICTOR)) if _tag(page, PREDICTOR) else 1
    if predictor not in (1, 2) or (predictor == 2 and (compression != LZW or any(b != 8 for b in bps))):
        result.add("5.E.1", f"Incompatible Predictor={predictor} for compression={compression} and BitsPerSample={bps}.", page=i)

    return width, height, spp, compression, planar, bps


def _validate_storage(page: tifffile.TiffPage, i: int, result: ValidationResult,
                      layout: tuple[int, int, int, int, int | None, tuple[int, ...]], file_size: int) -> bool:
    _, height, spp, _, planar, _ = layout
    if any(_tag(page, t) is not None for t in (TILE_WIDTH, TILE_LENGTH, TILE_OFFSETS, TILE_BYTE_COUNTS)):
        result.add("5.E.1", "Tiled storage is a TIFF 6 extension, not baseline stripped-image storage.", page=i)
        return False
    rows = _one_int(_value(page, ROWS_PER_STRIP))
    offsets = _ints(_value(page, STRIP_OFFSETS))
    bytecounts = _ints(_value(page, STRIP_BYTE_COUNTS))
    if rows is None or rows <= 0 or offsets is None or bytecounts is None:
        result.add("5.E.1", "Missing/invalid RowsPerStrip, StripOffsets, or StripByteCounts.", page=i)
        return False
    needed = math.ceil(height / rows) * (spp if planar == 2 else 1)
    if len(offsets) != needed or len(bytecounts) != needed:
        result.add("5.E.1", f"Expected {needed} strip offsets/counts, found {len(offsets)}/{len(bytecounts)}.", page=i)
        return False
    for k, (offset, length) in enumerate(zip(offsets, bytecounts)):
        if offset < 8 or length <= 0 or offset + length > file_size:
            result.add("5.E.1", f"Strip {k + 1} offset/length ({offset}, {length}) is invalid or outside file.", page=i)
            return False
    return True


def _validate_resolution(page: tifffile.TiffPage, i: int, result: ValidationResult,
                         width: int, height: int,
                         expected_aspect: float | None, tolerance: float) -> None:
    x = _positive_rational(_value(page, X_RESOLUTION))
    y = _positive_rational(_value(page, Y_RESOLUTION))
    unit = _one_int(_value(page, RESOLUTION_UNIT)) if _tag(page, RESOLUTION_UNIT) else 2
    if x is None or y is None or unit not in (1, 2, 3):
        result.add("5.E.5", f"Missing/invalid XResolution, YResolution or ResolutionUnit: {x}, {y}, {unit}.", page=i)
        return
    # A ratio of physical dimensions, not the raw pixel aspect ratio.
    physical_aspect = (width / x) / (height / y)
    orientation = _one_int(_value(page, ORIENTATION)) if _tag(page, ORIENTATION) else 1
    if orientation in (5, 6, 7, 8):
        physical_aspect = 1 / physical_aspect
    if not math.isfinite(physical_aspect) or physical_aspect <= 0:
        result.add("5.E.5", "Scaled page has an invalid physical aspect ratio.", page=i)
    elif expected_aspect is None:
        result.add("5.E.5", f"Scaled aspect ratio is {physical_aspect:.6g}; original aspect ratio must be compared externally.", page=i, severity="REVIEW")
    elif not math.isfinite(expected_aspect) or expected_aspect <= 0:
        result.add("5.E.5", f"Invalid expected original aspect ratio {expected_aspect!r}.", page=i)
    elif not math.isclose(physical_aspect, expected_aspect, rel_tol=tolerance, abs_tol=0.0):
        result.add("5.E.5", f"Scaled aspect {physical_aspect:.6g} differs from original {expected_aspect:.6g} (relative tolerance={tolerance}).", page=i)


def _decode_page(path: Path, page: tifffile.TiffPage, i: int, result: ValidationResult,
                 *, max_pixels: int | None) -> None:
    pixels = page.imagewidth * page.imagelength
    if max_pixels is not None and pixels > max_pixels:
        result.add("5.E.1", f"Pixel decoding skipped: {pixels:,} pixels exceed configured safety limit {max_pixels:,}; increase max_pixels to check.", page=i, severity="REVIEW")
        return
    # tifffile.segments() decodes strip-by-strip instead of allocating an
    # entire potentially huge page as page.asarray() would.
    try:
        count = 0
        for data, *_ in page.segments(maxworkers=1):
            if data is None:
                raise ValueError("Decoded strip returned no raster data")
            count += 1
        expected_segments = len(page.dataoffsets)
        if count != expected_segments:
            raise ValueError(f"Decoded {count} segments, expected {expected_segments}")
        return
    except Exception as primary:
        # CCITT and LZW commonly require imagecodecs with tifffile.
        # Pillow can decode them via its libtiff build, if installed.
        try:
            with Image.open(path) as img:
                if img.format != "TIFF":
                    raise ValueError("Pillow did not identify a TIFF image")
                img.seek(i)
                img.load()
                if img.size != (page.imagewidth, page.imagelength):
                    raise ValueError("Decoded image dimensions differ from TIFF tags")
            return
        except Exception as fallback:
            result.add("5.E.1", "Unable to decode all image pixels; image may be damaged or a codec is unavailable "
                       f"(tifffile: {primary!s}; Pillow: {fallback!s}).", page=i)


def _page_aspect(index: int, values: Mapping[int, float] | Sequence[float] | None) -> float | None:
    if values is None:
        return None
    if isinstance(values, Mapping):
        return values.get(index)
    return values[index] if index < len(values) else None


def analyze_tiff_bek128(
    path: PathLike,
    *,
    original_page_aspect_ratios: Mapping[int, float] | Sequence[float] | None = None,
    aspect_ratio_relative_tolerance: float = 0.01,
    decode_pixels: bool = True,
    max_pixels: int | None = 250_000_000,
) -> ValidationResult:
    """Inspect a TIFF document against archival rules 5.E.1--5.E.5.

    ``original_page_aspect_ratios``: original page width/height for each page,
    indexed from 0.  Because 5.E.5 requires preservation of ORIGINAL geometry,
    passing resolution values alone cannot prove it.

    Missing external evidence creates REVIEW findings (not silent passes).
    The 1% aspect tolerance is a *configurable engineering policy*, not a limit
    stated by BEK128. Use a stricter value where original dimensions are exact.
    ``max_pixels=None`` disables the anti-resource-exhaustion safety cap.
    """
    if aspect_ratio_relative_tolerance < 0 or not math.isfinite(aspect_ratio_relative_tolerance):
        raise ValueError("aspect_ratio_relative_tolerance must be finite and nonnegative")
    if max_pixels is not None and max_pixels <= 0:
        raise ValueError("max_pixels must be positive or None")
    p = Path(path)
    result = ValidationResult(p)
    if not p.is_file():
        result.add("5.E.1", f"TIFF file does not exist: {p}")
        return result

    try:
        ifd_count = _read_classic_ifds(p, result)
        if ifd_count is None:
            return result
        if ifd_count == 0:
            result.add("5.E.1", "TIFF contains no image directories.")
            return result

        with tifffile.TiffFile(str(p)) as tif:
            count = len(tif.pages)
            result.page_count = count
            if count != ifd_count:
                result.add("5.E.1", f"IFD chain has {ifd_count} entries but TIFF reader sees {count} pages.")
            if count == 0:
                result.add("5.E.1", "TIFF document has no image pages.")
            for i, page in enumerate(tif.pages):
                layout = _validate_layout(page, i, result)
                if layout is None:
                    continue
                width, height, *_ = layout
                storage_ok = _validate_storage(page, i, result, layout, p.stat().st_size)
                _validate_resolution(page, i, result, width, height,
                                     _page_aspect(i, original_page_aspect_ratios),
                                     aspect_ratio_relative_tolerance)
                if decode_pixels and storage_ok:
                    _decode_page(p, page, i, result, max_pixels=max_pixels)
                elif not decode_pixels:
                    result.add("5.E.1", "Pixel decoding was explicitly disabled; pixel integrity has not been tested.", page=i, severity="REVIEW")
    except (OSError, ValueError, tifffile.TiffFileError) as exc:
        result.add("5.E.1", f"Could not parse TIFF: {exc}")
    except Exception as exc:
        # Return a failure report instead of crashing an archive-validation batch.
        result.add("5.E.1", f"Unexpected TIFF parser error: {type(exc).__name__}: {exc}")
    return result


def check_tiff_bek128_bitdepths(
    path: PathLike,
    *,
    original_page_aspect_ratios: Mapping[int, float] | Sequence[float] | None = None,
    aspect_ratio_relative_tolerance: float = 0.01,
    decode_pixels: bool = True,
    max_pixels: int | None = 250_000_000,
    require_full_compliance: bool = True,
) -> Generator[OptReport, None, None]:
    """Compatibility entry point returning the project's OptReport objects.

    By default REVIEW findings are returned as failures, deliberately avoiding
    a false claim of full archival compliance. Set ``require_full_compliance=False``
    only if a machine-only TIFF validation result is sufficient for the caller.
    For distinguishing ERROR from REVIEW, use ``analyze_tiff_bek128``.
    """
    result = analyze_tiff_bek128(
        path,
        original_page_aspect_ratios=original_page_aspect_ratios,
        aspect_ratio_relative_tolerance=aspect_ratio_relative_tolerance,
        decode_pixels=decode_pixels,
        max_pixels=max_pixels,
    )
    reportable = [f for f in result.findings if f.severity == "ERROR" or require_full_compliance]
    if reportable:
        for finding in reportable:
            yield fail(f"{path}: {finding}")
    else:
        yield ok()

