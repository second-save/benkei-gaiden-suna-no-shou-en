"""Release packager for Benkei Gaiden: Suna no Shou (SNES) English translation."""
from __future__ import annotations

import hashlib
import re
import sys
import zipfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import build  # noqa: E402
import bps  # noqa: E402
import check_rom  # noqa: E402

OPEN_CHECKBOX_RE = re.compile(r"^\s*-\s*\[\s\]", re.MULTILINE)


def _hashes(data: bytes) -> tuple[int, str, str]:
    return len(data), f"{zlib.crc32(data) & 0xFFFFFFFF:08x}", hashlib.sha1(data).hexdigest()


def build_release() -> int:
    check_rom.check()
    orig_rom = build.DEFAULT_ROM.read_bytes()

    polish_path = ROOT / "docs" / "polish.md"
    if not polish_path.is_file():
        raise FileNotFoundError(f"Missing {polish_path}")
    polish_text = polish_path.read_text(encoding="utf-8")
    if OPEN_CHECKBOX_RE.search(polish_text):
        raise ValueError("docs/polish.md still contains open '- [ ]' items; clear all QA items before release")

    readme_path = ROOT / "README.md"
    if not readme_path.is_file():
        raise FileNotFoundError(f"Missing {readme_path}")
    readme_text = readme_path.read_text(encoding="utf-8")
    if "<Game title>" in readme_text or "minhnhattonthat" in readme_text or "ko-fi" in readme_text.lower():
        raise ValueError("README.md still contains template placeholders or third-party links")

    raw_built_path = ROOT / "build" / "benkei_suna_en.sfc"
    raw_built, _, total_entries = build.build_expanded(
        mode="translate",
        lang="en",
        rom_path=build.DEFAULT_ROM,
        script_dir=build.DEFAULT_SCRIPT_DIR,
        out_path=raw_built_path,
    )

    release_rom, snes_sum = bps.snes_checksum(raw_built)
    release_sfc_path = ROOT / "build" / "benkei_suna_en_release.sfc"
    release_sfc_path.write_bytes(release_rom)

    bps_name = "benkei-gaiden-suna-no-shou-en.bps"
    release_dir = ROOT / "release"
    release_dir.mkdir(parents=True, exist_ok=True)
    bps_path = release_dir / bps_name
    patch_bytes = bps.make(orig_rom, release_rom)
    bps_path.write_bytes(patch_bytes)

    smoke_patched = bps.apply(orig_rom, patch_bytes)
    smoke_path = ROOT / "build" / "smoke_patched.sfc"
    smoke_path.write_bytes(smoke_patched)
    if smoke_patched != release_rom:
        raise ValueError("BPS roundtrip mismatch: applied patch bytes != release SFC")
    if hashlib.sha1(smoke_patched).hexdigest() != hashlib.sha1(release_rom).hexdigest():
        raise ValueError("BPS roundtrip SHA-1 mismatch against release SFC")

    zip_name = "benkei-gaiden-suna-no-shou-en.zip"
    zip_path = release_dir / zip_name
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.write(bps_path, arcname=bps_name)
        zf.write(readme_path, arcname="README.md")

    with zipfile.ZipFile(zip_path, "r") as zf:
        names = sorted(zf.namelist())
        if names != ["README.md", bps_name]:
            raise ValueError(f"Unexpected zip contents {names}; expected ONLY README.md and {bps_name}")

    zip_bytes = zip_path.read_bytes()
    print(f"Release build OK ({total_entries} entries, SNES checksum=0x{snes_sum:04X}):")
    for label, blob, path in (
        ("Clean JP ROM", orig_rom, build.DEFAULT_ROM),
        ("Release SFC ", release_rom, release_sfc_path),
        ("BPS Patch   ", patch_bytes, bps_path),
        ("Release Zip ", zip_bytes, zip_path),
    ):
        sz, crc, sha = _hashes(blob)
        rel = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
        print(f"  {label}: {sz:>10,d} B  CRC32={crc}  SHA1={sha}  ({rel})")
    return 0


def main() -> int:
    return build_release()


if __name__ == "__main__":
    sys.exit(main())
