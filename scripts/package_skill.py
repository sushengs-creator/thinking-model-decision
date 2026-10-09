#!/usr/bin/env python3
"""Build the standalone Skill ZIP with Python 3.9+ standard library only.

This is a repository maintenance helper, not a runtime dependency of the Skill.
Run from any directory; defaults are resolved from this script's repository.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import tempfile
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


SKILL_NAME = "thinking-model-decision"
REPOSITORY = "https://github.com/sushengs-creator/thinking-model-decision"
EXCLUDED_DIRS = {".git", ".svn", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
EXCLUDED_FILES = {".DS_Store", "Thumbs.db"}


def build(repo_root, out):
    skill = repo_root / "skills" / SKILL_NAME
    entry = (skill / "SKILL.md").read_text(encoding="utf-8")
    match = re.search(r'^  version:\s*[\"\']?([0-9]+(?:\.[0-9]+){2})[\"\']?\s*$', entry, re.MULTILINE)
    if not match:
        raise ValueError("Cannot read metadata.version from SKILL.md")
    version = match.group(1)
    state = json.loads((skill / "references/library-state.json").read_text(encoding="utf-8"))
    if state.get("version") != version:
        raise ValueError("SKILL.md and library-state.json versions differ")
    out = out or repo_root / "dist" / f"{SKILL_NAME}-v{version}.zip"
    out = out.resolve()
    if out == skill.resolve() or skill.resolve() in out.parents:
        raise ValueError("Write the archive outside the Skill directory")

    files = {}
    for path in sorted(skill.rglob("*")):
        relative = path.relative_to(skill)
        if any(part in EXCLUDED_DIRS for part in relative.parts) or path.name in EXCLUDED_FILES:
            continue
        if path.is_symlink():
            raise ValueError(f"Symlinks are not packaged: {relative}")
        if path.is_file():
            if path.suffix in {".pyc", ".pyo"}:
                continue
            files[relative.as_posix()] = path.read_bytes()
    if "README.md" in files or "NOTICE.md" in files:
        raise ValueError("Skill already has README.md or NOTICE.md; review before replacing it")

    notice = (repo_root / "NOTICE.md").read_text(encoding="utf-8")
    notice = notice.replace("skills/thinking-model-decision/references/source-notes.md",
                            "references/source-notes.md")
    files["NOTICE.md"] = notice.encode("utf-8")
    files["README.md"] = (
        f"# 思维模型决策工具\n\n打包版本 **{version}**。\n\n"
        "请保留完整的 `thinking-model-decision` 文件夹。`SKILL.md` 需要和 "
        "`references/` 等配套资源一起使用，不要只复制入口文件。\n\n"
        f"- [开始使用与操作示范]({REPOSITORY}#readme)\n"
        f"- [安装与更新说明]({REPOSITORY}/blob/main/docs/INSTALL.md)\n"
    ).encode("utf-8")

    out.parent.mkdir(parents=True, exist_ok=True)
    # Stable paths, ordering, timestamps and file modes make identical inputs reproducible.
    with tempfile.TemporaryDirectory(prefix="package-skill-", dir=out.parent) as temp:
        staged = Path(temp) / out.name
        with ZipFile(staged, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
            for relative, content in sorted(files.items()):
                info = ZipInfo(f"{SKILL_NAME}/{relative}", date_time=(2020, 1, 1, 0, 0, 0))
                info.compress_type = ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                archive.writestr(info, content, compresslevel=9)
        staged.replace(out)
    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    checksum = out.with_suffix(out.suffix + ".sha256")
    checksum.write_text(f"{digest}  {out.name}\n", encoding="utf-8")
    print(json.dumps({"version": version, "files": len(files), "bytes": out.stat().st_size,
                      "archive": str(out), "sha256": digest,
                      "checksum_file": str(checksum)}, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1],
                        help="Repository containing skills/thinking-model-decision and NOTICE.md")
    parser.add_argument("--out", type=Path, help="Output ZIP path; default: <repo>/dist/<skill>-v<version>.zip")
    args = parser.parse_args()
    try:
        build(args.repo_root.resolve(), args.out)
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, f"package_skill: {exc}\n")


if __name__ == "__main__":
    main()
