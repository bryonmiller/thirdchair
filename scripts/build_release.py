"""Create reproducible source and handoff archives for the evaluation."""

from __future__ import annotations

import hashlib
import json
import argparse
import shutil
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "deliverables"
SOURCE_NAME = "third-chair-source.zip"
BUNDLE_NAME = "third-chair-complete-bundle.zip"
ARCHIVE_ROOT = "third-chair"
FIXED_TIME = (2026, 8, 12, 12, 0, 0)

ROOT_FILES = [
    ".gitignore",
    "CHANGELOG.md",
    "CITATION.cff",
    "LICENSE",
    "LICENSE-CONTENT.md",
    "README.md",
    "SECURITY.md",
    "eval_data/models.example.json",
    "pyproject.toml",
]
SOURCE_DIRS = [
    ".github",
    "docs",
    "eval_data/scenarios",
    "eval_data/schemas",
    "results",
    "scripts",
    "site",
    "src/third_chair",
    "tests_py",
]
EXCLUDED_NAMES = {
    "__pycache__",
    ".DS_Store",
    SOURCE_NAME,
    BUNDLE_NAME,
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}
EXCLUDED_RELATIVE = {
    "scripts/build-verified.sh",
    "scripts/install-ci.sh",
    "scripts/sites-env.sh",
    "scripts/validate-artifact.sh",
}


def include(path: Path) -> bool:
    try:
        relative = path.relative_to(ROOT).as_posix()
    except ValueError:
        return False
    if path.is_symlink():
        return False
    if relative in EXCLUDED_RELATIVE:
        return False
    if any(part in EXCLUDED_NAMES for part in path.parts):
        return False
    if path.suffix in EXCLUDED_SUFFIXES:
        return False
    if path.name == "models.json" or path.name == ".env" or path.name.startswith(".env."):
        return False
    if relative.startswith("results/") and relative != "results/README.md":
        return False
    return path.is_file()


def source_files() -> list[Path]:
    files = [ROOT / name for name in ROOT_FILES]
    for directory in SOURCE_DIRS:
        files.extend(path for path in (ROOT / directory).rglob("*") if include(path))
    return sorted({path for path in files if include(path)}, key=lambda path: str(path))


def write_member(archive: ZipFile, path: Path, arcname: str) -> None:
    info = ZipInfo(arcname, FIXED_TIME)
    info.compress_type = ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    archive.writestr(info, path.read_bytes())


def build_source() -> Path:
    destination = OUTPUT / SOURCE_NAME
    with ZipFile(destination, "w") as archive:
        for path in source_files():
            relative = path.relative_to(ROOT).as_posix()
            write_member(archive, path, f"{ARCHIVE_ROOT}/{relative}")
    return destination


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_manifest(files: list[Path]) -> Path:
    manifest = {
        "project": "The Third Chair",
        "version": "0.4.2",
        "author": "Bryon Miller",
        "research_status": "Audited descriptive baseline; comparative pilot and RL environment not run",
        "intended_repository": "https://github.com/bryonmiller/thirdchair",
        "intended_microsite": "https://thirdchair.bryonmiller.com",
        "files": [
            {"name": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in sorted(files, key=lambda item: item.name)
        ],
    }
    destination = OUTPUT / "release-manifest.json"
    destination.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return destination


def build_checksums(files: list[Path]) -> Path:
    destination = OUTPUT / "SHA256SUMS.txt"
    lines = [f"{sha256(path)}  {path.name}" for path in sorted(files, key=lambda item: item.name)]
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return destination


def build_bundle(files: list[Path]) -> Path:
    destination = OUTPUT / BUNDLE_NAME
    with ZipFile(destination, "w") as archive:
        for path in sorted(files, key=lambda item: item.name):
            write_member(archive, path, f"third-chair-deliverables/{path.name}")
    return destination


def write_readme() -> Path:
    destination = OUTPUT / "README-FIRST.txt"
    destination.write_text(
        "THE THIRD CHAIR\n"
        "Audited baseline | Bryon Miller | October 2026\n\n"
        "START HERE\n"
        "1. Unzip third-chair-source.zip and read README.md.\n"
        "2. Read docs/audit_repairs.md and docs/preregistration.md for current limits.\n"
        "3. The PDF contest documents are archived August 2026 material.\n\n"
        "STATUS\n"
        "Execution and reporting repairs are tested locally. Research validity remains limited. "
        "Comparative model results require configured provider API access and are not simulated here.\n\n"
        "QUICK RUN\n"
        "python -m pip install -e .\n"
        "cp eval_data/models.example.json eval_data/models.json\n"
        "third-chair plan --models eval_data/models.json --rotation balanced\n"
        "third-chair run --models eval_data/models.json --rotation balanced\n\n"
        "PUBLIC HOSTING\n"
        "The site/ directory is a neutral static build for GitHub Pages or any ordinary static host.\n",
        encoding="utf-8",
    )
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-only", action="store_true", help="Build the site ZIP without document dependencies")
    args = parser.parse_args()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    if args.source_only:
        source = build_source()
        site_zip = ROOT / "site" / "downloads" / SOURCE_NAME
        site_zip.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, site_zip)
        print(f"{site_zip.relative_to(ROOT)}\t{sha256(site_zip)}")
        return
    readme = write_readme()
    source = build_source()
    standalone = [
        readme,
        OUTPUT / "third-chair-brief.docx",
        OUTPUT / "third-chair-brief.pdf",
        OUTPUT / "third-chair-proposal.docx",
        OUTPUT / "third-chair-proposal.pdf",
        OUTPUT / "third-chair-submission.docx",
        OUTPUT / "third-chair-submission.pdf",
        source,
    ]
    missing = [path.name for path in standalone if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing release files: {', '.join(missing)}")
    manifest = build_manifest(standalone)
    checksums = build_checksums([*standalone, manifest])
    bundle = build_bundle([*standalone, manifest, checksums])
    for path in [source, manifest, checksums, bundle]:
        print(f"{path.name}\t{path.stat().st_size}\t{sha256(path)}")


if __name__ == "__main__":
    main()
