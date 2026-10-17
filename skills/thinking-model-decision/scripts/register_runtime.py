#!/usr/bin/env python3
"""Register one reviewed runtime draft; preview by default, explicit --apply and external backup required."""
import argparse
import datetime as dt
import json
import os
import tempfile
from pathlib import Path
import tool_runtime as runtime


def catalog(index):
    lines = ["# 按难题寻找可运行工具", "", "本目录登记 TM 运行文件，用户不必先选模型。按任务、信号和成果找候选，再读运行文件及模型卡；名称相近不代表机制相同。", "", "WW 是平等候选，见 [100个工具目录](wan-catalog.md)。追问看 [提问工具箱](questioning-toolkit.md)，组合看 [工具箱编排](toolbox-orchestration.md)。脚本 `tool_runtime.py search` 是词面检索；状态和实际试跑范围见 [索引](tool-index.json)。", "", "| 工具 | 要完成的任务 | 工位 | 最小成果 |", "|---|---|---|---|"]
    for row in index["tools"]:
        clean = lambda value: str(value).replace("|", "／").replace("\n", " ")
        lines.append("| [" + clean(row["id"] + " " + row["name"]) + "](tools/" + row["id"] + ".md) | " + clean(row["task"]) + " | " + "、".join(row["roles"]) + " | " + clean(row["output"]) + " |")
    return "\n".join(lines) + "\n"


def prepare(root, metadata):
    root = root.resolve()
    index = runtime.read_json(root / "references/tool-index.json")
    state = runtime.read_json(root / "references/library-state.json")
    users = {r["id"]: r for r in runtime.read_json(root / "references/user-index.json")}
    mid = metadata["id"]
    if mid not in users:
        raise ValueError("Register source and card first: " + mid)
    if not metadata.get("roles") or not set(metadata["roles"]).issubset(runtime.ROLES):
        raise ValueError("Use recognized roles")
    for key in ("name", "task", "output"):
        if not isinstance(metadata.get(key), str) or not metadata[key].strip():
            raise ValueError(key + " is required")
    if not isinstance(metadata.get("signals"), list) or not metadata["signals"] or any(not isinstance(x, str) or not x.strip() for x in metadata["signals"]):
        raise ValueError("signals must be nonempty text list")
    row = {k: metadata[k] for k in ("id", "name", "task", "roles", "signals", "output")}
    row["runtime_status"] = metadata.get("runtime_status", "authored")
    if row["runtime_status"] not in runtime.STATUSES:
        raise ValueError("Unknown runtime status")
    for field in ("trial_records", "review_records", "source_review_records"):
        row[field] = metadata.get(field, [])
        for ref in row[field]:
            runtime.checked_path(root, ref)
    if row["runtime_status"].startswith("sample_trials") and not row["trial_records"]:
        raise ValueError("Trial records required")
    if row["runtime_status"] == "sample_trials_reviewed" and not row["review_records"]:
        raise ValueError("Review records required")
    for kind, rel in (("source", users[mid]["path"]), ("card", users[mid]["card_path"]), ("runtime", "references/tools/" + mid + ".md")):
        row[kind + "_path"] = rel
        row[kind + "_sha256"] = runtime.digest(runtime.checked_path(root, rel))
    rows = index["tools"]
    if len({r["id"] for r in rows}) != len(rows):
        raise ValueError("Resolve duplicate runtime IDs before registration")
    updated = {r["id"]: r for r in rows}
    updated[mid] = row
    index.update(schema_version=2, version=state["version"], tools=sorted(updated.values(), key=lambda r: r["id"]))
    ids = sorted(updated)
    state["tool_migration"] = {"scope": "full" if len(ids) == len(users) else "partial", "migrated_ids": ids, "migrated_count": len(ids), "total_user_models": len(users), "remaining_not_migrated": len(users) - len(ids)}
    state["revision"] = state.get("revision", 0) + 1
    state["updated_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    state["change"] = "Register runtime " + mid + "; release validation must be refreshed"
    state["release_validation"] = {"status": "pending", "version": state["version"], "revision": state["revision"], "valid_for_current_revision": False}
    return index, state, row


def apply(root, index, state, backup_dir):
    root, backup_dir = root.resolve(), backup_dir.resolve()
    if backup_dir.is_relative_to(root):
        raise ValueError("Backup directory must be outside the skill directory and automatic discovery roots")
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup = backup_dir / ("runtime-" + stamp)
    backup.mkdir(parents=True, exist_ok=False)
    content = {"tool-index.json": json.dumps(index, ensure_ascii=False, indent=2) + "\n", "library-state.json": json.dumps(state, ensure_ascii=False, indent=2) + "\n", "tool-catalog.md": catalog(index)}
    old = {}
    temporary = []
    try:
        for name, text in content.items():
            destination = root / "references" / name
            old[name] = destination.read_bytes()
            (backup / name).write_bytes(old[name])
            fd, temp = tempfile.mkstemp(prefix=".runtime-", dir=destination.parent)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(text)
            temporary.append((Path(temp), destination))
        for temp, destination in temporary:
            os.replace(temp, destination)
    except Exception:
        for name, data in old.items():
            (root / "references" / name).write_bytes(data)
        raise
    finally:
        for temp, _ in temporary:
            temp.unlink(missing_ok=True)
    return backup


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata-file", type=Path, required=True)
    parser.add_argument("--skill-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--backup-dir", type=Path)
    args = parser.parse_args()
    try:
        index, state, row = prepare(args.skill_root, runtime.read_json(args.metadata_file))
        backup = None
        if args.apply:
            if not args.backup_dir:
                parser.error("--apply requires --backup-dir outside automatic skill discovery")
            backup = str(apply(args.skill_root, index, state, args.backup_dir))
        print(json.dumps({"applied": args.apply, "row": row, "revision": state["revision"], "backup": backup, "next": "Validate both library and runtime; align release version and fresh behavioral evidence before publishing."}, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"applied": False, "error": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
