#!/usr/bin/env python3
"""Read-only TM/WW toolbox lookup, lexical search, and provenance validation."""
import argparse
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

ROLES = {"澄清", "证据", "解释", "约束", "参与者", "二阶", "选项", "取舍", "执行", "学习", "复盘"}
STATUSES = {"authored", "source_checked", "sample_trials_recorded", "sample_trials_reviewed"}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def checked_path(root, relative):
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError("Path must be nonempty and relative")
    if ".." in Path(relative).parts:
        raise ValueError("Parent traversal is not allowed")
    root = root.resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Path escapes skill root")
    if not path.is_file():
        raise ValueError("Missing file: " + relative)
    return path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def freshness(root, row):
    errors = []
    for kind in ("source", "card", "runtime"):
        try:
            if digest(checked_path(root, row[kind + "_path"])) != row[kind + "_sha256"]:
                errors.append("stale " + kind + " fingerprint")
        except (ValueError, KeyError, OSError) as exc:
            errors.append(str(exc))
    return errors


def validate(root):
    errors = []
    try:
        index = read_json(root / "references/tool-index.json")
        users = read_json(root / "references/user-index.json")
        state = read_json(root / "references/library-state.json")
        rows = index["tools"]
        user_map = {r["id"]: r for r in users}
        ids = [r["id"] for r in rows]
        if index.get("schema_version") != 2:
            errors.append("Unsupported schema")
        if len(set(ids)) != len(ids):
            errors.append("Duplicate runtime IDs")
        if len(user_map) != len(users):
            errors.append("Duplicate source IDs")
        if index["version"] != state["version"]:
            errors.append("Version mismatch")
        migration = state["tool_migration"]
        if set(ids) != set(migration["migrated_ids"]) or len(ids) != migration["migrated_count"]:
            errors.append("Migration membership/count mismatch")
        if len(users) != migration["total_user_models"] or len(users) - len(ids) != migration["remaining_not_migrated"]:
            errors.append("Migration inventory mismatch")
        for row in rows:
            mid = row["id"]
            if mid not in user_map:
                errors.append(mid + ": unknown model")
                continue
            if row["source_path"] != user_map[mid]["path"] or row["card_path"] != user_map[mid]["card_path"]:
                errors.append(mid + ": source/card association mismatch")
            if row["runtime_path"] != "references/tools/" + mid + ".md":
                errors.append(mid + ": runtime association mismatch")
            errors.extend(mid + ": " + error for error in freshness(root, row))
            if not row.get("task") or not row.get("output") or not row.get("name"):
                errors.append(mid + ": task/name/output required")
            if not row.get("roles") or not set(row["roles"]).issubset(ROLES):
                errors.append(mid + ": invalid roles")
            if not isinstance(row.get("signals"), list) or not row["signals"] or any(not isinstance(x, str) or not x.strip() for x in row["signals"]):
                errors.append(mid + ": signals required")
            status = row.get("runtime_status")
            evidence = row.get("trial_records", [])
            if status not in STATUSES:
                errors.append(mid + ": unknown runtime status")
            if status in {"sample_trials_recorded", "sample_trials_reviewed"} and not evidence:
                errors.append(mid + ": trial evidence required")
            if status == "sample_trials_reviewed" and not row.get("review_records"):
                errors.append(mid + ": review evidence required")
            for ref in evidence + row.get("review_records", []) + row.get("source_review_records", []):
                try:
                    checked_path(root, ref)
                except ValueError as exc:
                    errors.append(mid + ": " + str(exc))
        files = {p.relative_to(root).as_posix() for p in (root / "references/tools").glob("TM-*.md")}
        if files != {r["runtime_path"] for r in rows}:
            errors.append("Runtime file/index mismatch")
        wan = read_json(root / "references/wan-index.json")
        if len(wan) != state["wan_tools"] or len({r["id"] for r in wan}) != len(wan):
            errors.append("WW inventory mismatch")
        for row in wan:
            path = checked_path(root, row["path"])
            if digest(path) != row["content_sha256"]:
                errors.append(row["id"] + ": stale WW fingerprint")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        errors.append("Invalid runtime metadata: " + str(exc))
    return {"ok": not errors, "errors": errors, "scope": "Structural and fingerprint checks only; not behavioral proof"}


def show(root, mid):
    if mid.startswith("WW-"):
        for row in read_json(root / "references/wan-index.json"):
            if row["id"] == mid:
                result = dict(row)
                result["family"] = "WW"
                try:
                    current = digest(checked_path(root, row["path"])) == row["content_sha256"]
                except (OSError, ValueError):
                    current = False
                result["fingerprints_current"] = current
                result["note"] = "Peer candidate; read full tool text. Snapshot coverage is not outcome validation."
                return result
        raise ValueError("Unknown WW tool ID: " + mid)
    users = {r["id"]: r for r in read_json(root / "references/user-index.json")}
    if mid not in users:
        raise ValueError("Unknown user model ID: " + mid)
    for row in read_json(root / "references/tool-index.json")["tools"]:
        if row["id"] == mid:
            result = dict(row)
            issues = freshness(root, row)
            result.update(family="TM", fingerprints_current=not issues, freshness_issues=issues)
            if issues:
                result["note"] = "Content changed since registration; recorded trial status does not validate current text."
            return result
    row = users[mid]
    return {"id": mid, "name": row["short_name"], "runtime_status": "not_migrated",
            "card_path": row["card_path"], "source_path": row["path"],
            "note": "Use the existing card with disclosed scope; no registered runtime yet."}


def normalize(text):
    return unicodedata.normalize("NFKC", str(text)).casefold()


def terms(query):
    chunks = re.findall(r"[a-z0-9]+(?:[-.][a-z0-9]+)*|[\u4e00-\u9fff]+", normalize(query))
    result = set(chunks)
    for chunk in chunks:
        if re.fullmatch(r"[\u4e00-\u9fff]{3,}", chunk):
            result.update(chunk[i:i + 2] for i in range(len(chunk) - 1))
    return result


def contains(text, term):
    if re.fullmatch(r"[a-z0-9.-]+", term):
        return re.search(r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])", text) is not None
    return term in text


def search(root, query, limit=12, role=None):
    if role and role not in ROLES:
        raise ValueError("Unknown role: " + role)
    needles = terms(query)
    if not needles:
        raise ValueError("Search query must contain words or a tool ID")
    candidates = []
    for row in read_json(root / "references/tool-index.json")["tools"]:
        if role and role not in row["roles"]:
            continue
        candidates.append({"id": row["id"], "name": row["name"], "family": "TM", "task": row["task"],
                           "roles": row["roles"], "signals": row["signals"], "output": row["output"], "path": row["runtime_path"]})
    # Role tags are curated only for TM. Do not silently infer WW roles.
    if not role:
        for row in read_json(root / "references/wan-index.json"):
            candidates.append({"id": row["id"], "name": row["short_name"], "family": "WW", "task": row.get("trigger", ""), "roles": [], "signals": [], "path": row["path"]})
    ranked = []
    for row in candidates:
        identity = normalize(row["id"] + " " + row["name"])
        signal_text = normalize(" ".join(row["signals"]))
        body = normalize(row["task"] + " " + row.get("output", ""))
        matched = sorted(t for t in needles if any(contains(text, t) for text in (identity, signal_text, body)))
        score = sum((8 if contains(identity, t) else 0) + (5 if contains(signal_text, t) else 0) + (2 if contains(body, t) else 0) for t in matched)
        if normalize(query).strip() == normalize(row["id"]):
            score += 1000
        if score:
            ranked.append(dict(row, lexical_score=score, matched_terms=matched))
    ranked.sort(key=lambda row: (-row["lexical_score"], row["id"]))
    return {"query": query, "scope": "Lexical candidate retrieval, not suitability or confidence; read mechanisms and boundaries.",
            "role_filter": role, "role_scope": "TM only" if role else "TM and WW", "total_matches": len(ranked), "results": ranked[:limit]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("list", "show", "search", "validate"))
    parser.add_argument("query", nargs="?")
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--role", choices=sorted(ROLES))
    parser.add_argument("--skill-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        if args.limit < 1:
            parser.error("--limit must be positive")
        if args.command == "validate":
            result = validate(args.skill_root)
        elif args.command == "show":
            if not args.query:
                parser.error("show requires a TM or WW ID")
            result = show(args.skill_root, args.query)
        elif args.command == "search":
            if not args.query:
                parser.error("search requires a query")
            result = search(args.skill_root, args.query, args.limit, args.role)
        else:
            result = read_json(args.skill_root / "references/tool-index.json")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if args.command == "validate" and not result["ok"] else 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
