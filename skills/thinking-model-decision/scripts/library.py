#!/usr/bin/env python3
"""Portable, stdlib-only retrieval and explicit maintenance of the model library.

All stored paths are relative to the directory containing this script's parent.
Search reports lexical candidates, never inferred mechanisms. Mutations default
to a read-only preview; --apply is required. Writes are atomic per file, not a
multi-file database transaction. History supports recovery after interruptions.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile
import unicodedata
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
import uuid


ROOT = Path(__file__).resolve().parents[1]
USER_INDEX = "references/user-index.json"
WAN_INDEX = "references/wan-index.json"
STATE = "references/library-state.json"
CATALOG = "references/user-catalog.md"
RELATION_CATALOG = "references/relation-catalog.md"
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
USER_RE = re.compile(r"^TM-(?:00[1-9]|0[1-9][0-9]|[1-9][0-9]{2,})$")
WAN_RE = re.compile(r"^WW-[1-9][0-9]*(?:\.[1-9][0-9]*)?$")
CARD_STATUSES = {"draft", "source_reviewed", "sample_reviewed", "behavior_checked", "needs_review"}


def checked_card_metadata(value, wan_ids):
    """Validate maintained routing data, not the truth of its semantic claims."""
    if not isinstance(value, dict):
        raise LibraryError("card metadata must be an object")
    allowed = {"trigger", "source_sections", "search_terms", "decision_stage", "relations", "warnings"}
    unknown = set(value) - allowed
    if unknown:
        raise LibraryError("Unknown card metadata fields: " + ", ".join(sorted(unknown)))
    for key in ("source_sections", "search_terms", "decision_stage", "warnings"):
        if key in value and (not isinstance(value[key], list) or any(
                not isinstance(item, str) or not item.strip() for item in value[key])):
            raise LibraryError(f"card metadata {key} must be an array of nonempty text")
    if "trigger" in value and (not isinstance(value["trigger"], str) or not value["trigger"].strip()):
        raise LibraryError("card metadata trigger must be nonempty text")
    relations = value.get("relations", [])
    if not isinstance(relations, list):
        raise LibraryError("card metadata relations must be an array")
    for relation in relations:
        if not isinstance(relation, dict) or set(relation) != {"ww_id", "relation", "reason"}:
            raise LibraryError("Each relation requires ww_id, relation and reason")
        if any(not isinstance(v, str) or not v.strip() for v in relation.values()):
            raise LibraryError("Relation fields must be nonempty text")
        if relation["ww_id"] not in wan_ids:
            raise LibraryError(f"Unknown relation target: {relation['ww_id']}")
    return value


class LibraryError(Exception):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def output(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))


def safe_path(value, *, exists=False):
    """Reject absolute, traversal, Windows-style and symlink escape paths."""
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise LibraryError(f"Invalid stored path: {value!r}")
    parts = PurePosixPath(value)
    if parts.is_absolute() or ".." in parts.parts or ":" in value or value in {".", ""}:
        raise LibraryError(f"Unsafe stored path: {value!r}")
    path = ROOT / parts
    try:
        path.resolve().relative_to(ROOT)
    except (ValueError, OSError, RuntimeError) as exc:
        raise LibraryError(f"Path escapes library root: {value}") from exc
    if exists and not path.is_file():
        raise LibraryError(f"Missing file: {value}")
    return path


def read_json(relative):
    try:
        return json.loads(safe_path(relative, exists=True).read_text(encoding="utf-8"))
    except (ValueError, UnicodeError, OSError) as exc:
        raise LibraryError(f"Cannot read {relative}: {exc}") from exc


def load_index(relative):
    data = read_json(relative)
    if not isinstance(data, list) or any(not isinstance(row, dict) for row in data):
        raise LibraryError(f"{relative} must be a JSON array of objects")
    return data


def indexes():
    return load_index(USER_INDEX), load_index(WAN_INDEX)


def require_unique(rows):
    ids = [row.get("id") for row in rows]
    if any(not isinstance(key, str) for key in ids) or len(set(ids)) != len(ids):
        raise LibraryError("Index contains invalid or duplicate IDs")


def find_row(identifier):
    users, wan = indexes()
    rows = users + wan
    require_unique(rows)
    matches = [row for row in rows if row["id"] == identifier]
    if not matches:
        raise LibraryError(f"Unknown ID: {identifier}")
    return matches[0]


def effective_card_status(row):
    if not row.get("card_path"):
        return "not_extracted"
    if row.get("card_source_sha256") and row["card_source_sha256"] != row.get("source_sha256"):
        return "needs_review"
    return row.get("card_status", "unregistered")


def metadata(row):
    result = dict(row)
    result["effective_card_status"] = effective_card_status(row)
    current = bool(row.get("card_path") and row.get("card_source_sha256") == row.get("source_sha256")
                   and effective_card_status(row) != "needs_review")
    result["card_source_is_current"] = current
    result["card_use_notice"] = (
        "当前无卡片，请先读原文。" if not row.get("card_path") else
        "卡片需复核，不应作为当前版本直接调用。" if not current else
        "卡片对应当前来源；仍须按 card_status 判断审核范围，来源一致不代表事实或效果已验证。")
    result["library_root"] = str(ROOT)
    for key in ("path", "html_path", "card_path", "source_path", "validation_note_path"):
        if row.get(key):
            safe_path(row[key], exists=True)
    return result


def normalize(value):
    return unicodedata.normalize("NFKC", value).casefold().strip()


def query_terms(query):
    normalized = normalize(query)
    terms = re.findall(r"[\w.-]+", normalized, flags=re.UNICODE)
    # Bigrams provide a deterministic fallback for unsegmented Chinese sentences.
    bigrams = []
    for run in re.findall(r"[\u3400-\u9fff]+", normalized):
        if len(run) > 2:
            bigrams.extend(run[i:i + 2] for i in range(len(run) - 1))
    return normalized, list(dict.fromkeys(terms)), list(dict.fromkeys(bigrams))


def search(args):
    users, wan = indexes()
    require_unique(users + wan)
    phrase, terms, bigrams = query_terms(args.query)
    if not phrase:
        raise LibraryError("Query cannot be empty")
    matches = []
    for row in users + wan:
        reasons = []
        score = 0
        card_meta = row.get("card_metadata", {}) if effective_card_status(row) != "needs_review" else {}
        fields = [("id", str(row.get("id", "")), 150),
                  ("short_name", str(row.get("short_name", "")), 90),
                  ("title", str(row.get("title", "")), 50),
                  ("search_terms", " ".join(row.get("search_terms", [])), 35),
                  ("trigger", str(row.get("trigger", "")), 20),
                  ("card_trigger", card_meta.get("trigger", ""), 35),
                  ("card_search_terms", " ".join(card_meta.get("search_terms", [])), 35),
                  ("decision_stage", " ".join(card_meta.get("decision_stage", [])), 10)]
        for field, text, weight in fields:
            haystack = normalize(text)
            exact = phrase == haystack
            hits = [term for term in terms if term in haystack]
            # Also recognize a model name embedded in a longer question.
            named = field == "short_name" and len(haystack) >= 2 and haystack in phrase
            if phrase in haystack or hits or named:
                found = hits[:4] or [text if named else phrase]
                score += weight * (2 if exact else 1) + min(len(hits), 4)
                reasons.append({"field": field, "matched": found})
            elif bigrams and field != "id":
                hits = [term for term in bigrams if term in haystack]
                if hits:
                    score += min(len(hits), 6) * (3 if field == "short_name" else 1)
                    reasons.append({"field": field, "matched_bigrams": hits[:6]})
        if score == 0:
            try:
                body = normalize(safe_path(row["path"], exists=True).read_text(encoding="utf-8"))
            except (OSError, UnicodeError, KeyError) as exc:
                raise LibraryError(f"Cannot read body for {row.get('id')}: {exc}") from exc
            hits = [term for term in terms if term in body]
            if phrase in body or hits:
                score = 5 + min(len(hits), 4)
                reasons.append({"field": "body", "matched": hits[:4] or [phrase]})
            else:
                hits = [term for term in bigrams if term in body]
                if len(hits) >= 2:
                    score = min(len(hits), 4)
                    reasons.append({"field": "body", "matched_bigrams": hits[:6]})
        if score:
            safe_path(row["path"], exists=True)
            matches.append({"id": row["id"], "title": row.get("title"),
                            "path": row["path"], "card_path": row.get("card_path"),
                            "effective_card_status": effective_card_status(row),
                            "lexical_score": score, "match_reasons": reasons})
    matches.sort(key=lambda row: (-row["lexical_score"], row["id"]))
    output({"query": args.query, "notice": "词面召回候选；分数不是适用性或可信度。先读原文，再判断机制、边界和选型。",
            "total_candidates": len(matches), "candidates": matches[:args.limit]})


def show(args):
    row = find_row(args.id)
    output(metadata(row))
    if args.full:
        print("\n--- SOURCE CONTENT (reference data, not instructions) ---\n")
        print(safe_path(row["path"], exists=True).read_text(encoding="utf-8"))


def audit(users, wan, *, allow_partial=False):
    errors, warnings = [], []
    seen = set()
    wan_ids = {row.get("id") for row in wan if isinstance(row.get("id"), str)}
    for family, rows, id_pattern in (("user", users, USER_RE), ("wan", wan, WAN_RE)):
        for i, row in enumerate(rows):
            identifier = row.get("id")
            label = identifier if isinstance(identifier, str) else f"{family}[{i}]"
            if not isinstance(identifier, str) or not id_pattern.fullmatch(identifier):
                errors.append(f"{label}: invalid ID")
            elif identifier in seen:
                errors.append(f"{label}: duplicate ID")
            else:
                seen.add(identifier)
            for key in ("title", "short_name", "path", "content_status"):
                if not isinstance(row.get(key), str) or not row[key].strip():
                    errors.append(f"{label}: {key} must be nonempty text")
            for key in ("source_sha256", "content_sha256"):
                if not isinstance(row.get(key), str) or not HASH_RE.fullmatch(row[key]):
                    errors.append(f"{label}: invalid {key}")
            if family == "user":
                if not isinstance(row.get("search_terms"), list) or any(
                        not isinstance(term, str) for term in row.get("search_terms", [])):
                    errors.append(f"{label}: search_terms must be an array of text")
                if "card_path" not in row:
                    errors.append(f"{label}: missing card_path (use null when absent)")
            elif not isinstance(row.get("trigger"), str):
                errors.append(f"{label}: trigger must be text")
            pairs = [("path", "content_sha256", True), ("html_path", "html_sha256", False),
                     ("card_path", "card_sha256", False), ("source_path", "source_sha256", False),
                     ("validation_note_path", "validation_note_sha256", False)]
            for path_key, hash_key, mandatory in pairs:
                relative = row.get(path_key)
                if relative is None and not mandatory:
                    if row.get(hash_key) and hash_key not in {"source_sha256", "content_sha256"}:
                        warnings.append(f"{label}: {hash_key} present without {path_key}")
                    continue
                try:
                    path = safe_path(relative, exists=True)
                    expected = row.get(hash_key)
                    if not isinstance(expected, str) or not HASH_RE.fullmatch(expected):
                        errors.append(f"{label}: invalid or absent {hash_key}")
                    elif digest(path.read_bytes()) != expected:
                        errors.append(f"{label}: {hash_key} mismatch ({relative})")
                except (LibraryError, OSError) as exc:
                    errors.append(f"{label}: {exc}")
            if row.get("card_path"):
                status = row.get("card_status")
                if status not in CARD_STATUSES:
                    errors.append(f"{label}: invalid or absent card_status")
                source_hash = row.get("card_source_sha256")
                if not isinstance(source_hash, str) or not HASH_RE.fullmatch(source_hash):
                    errors.append(f"{label}: invalid or absent card_source_sha256")
                elif source_hash != row.get("source_sha256"):
                    warnings.append(f"{label}: needs_review — card source hash differs from current source")
                if status == "needs_review":
                    warnings.append(f"{label}: card is marked needs_review")
                if status == "behavior_checked" and not row.get("validation_note_path"):
                    errors.append(f"{label}: behavior_checked requires validation_note_path")
                if "card_metadata" in row:
                    try:
                        checked_card_metadata(row["card_metadata"], wan_ids)
                    except LibraryError as exc:
                        errors.append(f"{label}: {exc}")
    if not allow_partial:
        missing = [f"TM-{number:03d}" for number in range(1, 126) if f"TM-{number:03d}" not in seen]
        if missing:
            errors.append("Missing baseline user IDs: " + ", ".join(missing))
        if len(wan) < 100:
            errors.append(f"Baseline requires at least 100 WW entries; found {len(wan)}")
    return errors, warnings


def validate(args):
    users, wan = indexes()
    errors, warnings = audit(users, wan, allow_partial=args.allow_partial)
    state = read_json(STATE)
    if not isinstance(state, dict) or not isinstance(state.get("version"), str):
        errors.append("library-state must contain a text version")
    elif not isinstance(state.get("revision"), int) or isinstance(state.get("revision"), bool) or state["revision"] < 1:
        errors.append("library-state revision must be a positive integer")
    if isinstance(state, dict):
        for key, actual in (("user_models", len(users)), ("wan_tools", len(wan))):
            if key in state and state[key] != actual:
                errors.append(f"library-state {key} is {state[key]}, actual {actual}")
    output({"ok": not errors, "library_root": str(ROOT), "partial_fixture_mode": args.allow_partial,
            "version": state.get("version") if isinstance(state, dict) else None,
            "revision": state.get("revision") if isinstance(state, dict) else None,
            "counts": {"user_models": len(users), "wan_tools": len(wan),
                       "cards": sum(bool(row.get("card_path")) for row in users),
                       "card_statuses": dict(Counter(effective_card_status(row) for row in users)),
                       "content_statuses": dict(Counter(str(row.get("content_status")) for row in users + wan))},
            "needs_review": [row.get("id") for row in users if effective_card_status(row) == "needs_review"],
            "errors": errors, "warnings": warnings,
            "provenance_note": "source_sha256 保存原来源指纹；未提供 source_path 的原始来源不在包内，不能重算验证。可携带正文、HTML、卡片及验证记录按各自哈希核验。"})
    return 0 if not errors else 1


def source_bytes(filename):
    path = Path(filename).expanduser()
    if not path.is_absolute():
        raise LibraryError("Input source/card/note file must use an absolute path")
    try:
        data = path.read_bytes()
        text = data.decode("utf-8")
    except (OSError, UnicodeError) as exc:
        raise LibraryError(f"Cannot read UTF-8 input {path}: {exc}") from exc
    if not text.strip():
        raise LibraryError(f"Input file is empty: {path}")
    return data


def normalized_url(value):
    try:
        parts = urlsplit(value.strip())
        if parts.scheme not in {"http", "https"} or not parts.netloc or parts.username or parts.password:
            raise ValueError("HTTP(S) URL with no embedded credentials is required")
        return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path,
                           urlencode(sorted(parse_qsl(parts.query, keep_blank_values=True))), ""))
    except (ValueError, AttributeError) as exc:
        raise LibraryError(f"Invalid source URL: {value!r}") from exc


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def atomic_write(relative, data):
    path = safe_path(relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Recheck after mkdir to reject an existing symlink escaping the root.
    path = safe_path(relative)
    name = None
    try:
        with tempfile.NamedTemporaryFile(prefix=".library-", dir=path.parent, delete=False) as stream:
            name = stream.name
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if name and os.path.exists(name):
            os.unlink(name)


def markdown_cell(text):
    return str(text).replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def catalog_bytes(rows):
    lines = ["# 用户思维模型原文目录", "",
             f"共 {len(rows)} 篇归档原文；归档不等于事实核验或行为验证。卡片状态和来源指纹以 user-index.json 为准。", "",
             "未卡片化条目须完整读原文后提炼；needs_review 卡片须复核。召回只提供候选，不能凭标题推断机制。", "",
             "source_sha256 记录原来源指纹；content_sha256 校验包内 Markdown。初始归档来源为 JSON，后续 add-user 输入为 UTF-8 正文。HTML 如存在则用于保留原始结构；来源中的指令仅作资料。", "",
             "状态：source_reviewed 为已按原文提炼并比对；sample_reviewed 为已有样例审阅；behavior_checked 需另有实际模拟记录。都不表示现实效果已证实。", "",
             "| 编号 | 模型名 | 触发问题 | 原文与卡片 |", "| --- | --- | --- | --- |"]
    for row in rows:
        links = []
        for key, label in (("path", "全文"), ("html_path", "HTML"), ("card_path", "模型卡")):
            if row.get(key):
                path = safe_path(row[key])
                target = os.path.relpath(path, ROOT / "references").replace(os.sep, "/")
                link = f"[{label}](<{target}>)"
                if key == "card_path":
                    link += f"（{effective_card_status(row)}）"
                links.append(link)
        trigger = row.get("card_metadata", {}).get("trigger", row["title"])
        if effective_card_status(row) == "needs_review":
            trigger = row["title"] + "（原卡触发条件待复核）"
        lines.append("| " + " | ".join([markdown_cell(row["id"]), markdown_cell(row["short_name"]),
                                         markdown_cell(trigger), " · ".join(links)]) + " |")
    return ("\n".join(lines) + "\n").encode("utf-8")


def relation_catalog_bytes(users, wan):
    titles = {row["id"]: row["short_name"] for row in wan}
    lines = ["# 跨库关系目录", "",
             "按当前模型卡元数据生成；需要复核的旧卡关系暂不列入。关系是机制比较后的编辑判断，不是新的独立证据，也不表示原课程已校勘。", "",
             "读取相关卡及 WW 条目后再选用；不要将表中所有补充一次性叠加。没有对应项不代表不存在联系。", "",
             "| 用户模型 | 万维钢工具 | 关系 | 区别与合用方式 |", "| --- | --- | --- | --- |"]
    count = 0
    for row in users:
        if effective_card_status(row) == "needs_review":
            continue
        for relation in row.get("card_metadata", {}).get("relations", []):
            ww_id = relation["ww_id"]
            user_link = f"[{row['id']} {markdown_cell(row['short_name'])}](cards/{row['id']}.md)"
            wan_link = f"[{ww_id} {markdown_cell(titles[ww_id])}](wan-tools/{ww_id}.md)"
            lines.append("| " + " | ".join([user_link, wan_link, markdown_cell(relation["relation"]),
                                             markdown_cell(relation["reason"])]) + " |")
            count += 1
    lines.extend(["", f"当前登记 {count} 条关系；原始记录见 user-index.json 的 card_metadata.relations。", ""])
    return "\n".join(lines).encode("utf-8")


def prepare_state(users, wan, change):
    current = read_json(STATE)
    if not isinstance(current, dict) or not isinstance(current.get("version"), str):
        raise LibraryError("library-state must have a text version")
    revision = current.get("revision")
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 1:
        raise LibraryError("library-state revision must be a positive integer")
    state = dict(current)
    cards = [row for row in users if row.get("card_path")]
    sampled = [row["id"] for row in cards if effective_card_status(row) in {"sample_reviewed", "behavior_checked"}]
    state.update(revision=revision + 1, updated_at=datetime.now(timezone.utc).isoformat(),
                 user_models=len(users), wan_tools=len(wan), total_cards=len(cards),
                 source_reviewed_cards=sum(effective_card_status(row) == "source_reviewed" for row in cards),
                 sample_cards=len(sampled), sample_card_ids=sampled,
                 card_status_counts=dict(Counter(effective_card_status(row) for row in users)),
                 needs_review=[row["id"] for row in cards if effective_card_status(row) == "needs_review"],
                 change=change)
    if isinstance(state.get("release_validation"), dict):
        state["release_validation"] = dict(state["release_validation"], valid_for_current_revision=False)
    return state


def mutation_inputs():
    users, wan = indexes()
    errors, _ = audit(users, wan, allow_partial=True)
    if errors:
        raise LibraryError("Existing library fails integrity checks; repair before mutation: " + "; ".join(errors[:8]))
    return users, wan


def commit_change(args, users, wan, payloads, old_row, change, warnings=None):
    state = prepare_state(users, wan, change)
    payloads[USER_INDEX] = json_bytes(users)
    payloads[CATALOG] = catalog_bytes(users)
    payloads[RELATION_CATALOG] = relation_catalog_bytes(users, wan)
    payloads[STATE] = json_bytes(state)
    history_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ") + "-" + args.command + "-" + uuid.uuid4().hex[:10]
    history_root = ".history/" + history_id
    backups = {USER_INDEX, CATALOG, STATE}
    if old_row:
        backups.update(old_row.get(key) for key in ("path", "html_path", "card_path", "validation_note_path") if old_row.get(key))
    # Include any existing destinations, even an unindexed orphan.
    backups.update(relative for relative in payloads if safe_path(relative).exists())
    snapshots = {}
    for relative in sorted(backups):
        path = safe_path(relative)
        if path.exists():
            if not path.is_file():
                raise LibraryError(f"Not a file: {relative}")
            snapshots[history_root + "/" + relative] = path.read_bytes()
    manifest = {"action": args.command, "id": args.id, "change": change,
                "previous_revision": state["revision"] - 1, "next_revision": state["revision"],
                "old_entry": old_row, "destinations": sorted(payloads),
                "backups": [key.removeprefix(history_root + "/") for key in snapshots]}
    snapshots[history_root + "/change.json"] = json_bytes(manifest)
    for relative in list(payloads) + list(snapshots):
        safe_path(relative)
    preview = {"applied": bool(args.apply), "mode": "apply" if args.apply else "dry_run",
               "id": args.id, "change": change, "writes": sorted(payloads),
               "history_path": history_root, "next_revision": state["revision"],
               "version_unchanged": state["version"], "warnings": warnings or []}
    if not args.apply:
        output(preview)
        return
    # Save complete previous data before changing a live file. File-by-file
    # atomicity avoids partial file contents; recovery may be needed on interruption.
    for relative, data in snapshots.items():
        atomic_write(relative, data)
    for relative, data in payloads.items():
        atomic_write(relative, data)
    output(preview)


def add_user(args):
    if not USER_RE.fullmatch(args.id):
        raise LibraryError("User ID must be TM-001 style (TM-126 and later are allowed)")
    if not args.title.strip() or "\n" in args.title or "\r" in args.title:
        raise LibraryError("Title must be nonempty, single-line text")
    try:
        if date.fromisoformat(args.captured_at).isoformat() != args.captured_at:
            raise ValueError()
    except ValueError as exc:
        raise LibraryError("captured-at must be YYYY-MM-DD") from exc
    source_url = normalized_url(args.source_url) if args.source_url else None
    source_label = args.source_label or Path(args.source_file).name
    if not source_label.strip() or "\n" in source_label or "\r" in source_label:
        raise LibraryError("source-label must be nonempty, single-line text")
    data = source_bytes(args.source_file)
    source_hash = digest(data)
    users, wan = mutation_inputs()
    old = next((row for row in users if row["id"] == args.id), None)
    if old and not args.replace:
        raise LibraryError(f"{args.id} already exists; inspect it before using --replace")
    if args.replace and old is None:
        raise LibraryError("--replace requires an existing ID")
    for row in users:
        if row["id"] == args.id:
            continue
        if source_hash in {row.get("source_sha256"), row.get("content_sha256")}:
            raise LibraryError(f"Duplicate source content already indexed as {row['id']}")
        if source_url and row.get("source_url") and normalized_url(row["source_url"]) == source_url:
            raise LibraryError(f"Duplicate source URL already indexed as {row['id']}")
    entry = {"id": args.id, "title": args.title.strip(), "short_name": args.title.strip(),
             "path": f"references/user-models/{args.id}.md", "html_path": None,
             "source_url": args.source_url.strip() if args.source_url else None,
             "source_label": source_label.strip(), "captured_at": args.captured_at,
             "source_format": "user_provided_utf8", "source_sha256": source_hash,
             "content_sha256": source_hash, "html_sha256": None,
             "content_status": "source_archived", "card_path": None,
             "search_terms": [args.title.strip()]}
    warnings = []
    if old and old.get("card_path"):
        for key, value in old.items():
            if key.startswith("card_") or key.startswith("validation_note_"):
                entry[key] = value
        entry["card_status"] = "needs_review"
        warnings.append("Existing card preserved and marked needs_review; its previous source hash is retained")
    if old and old.get("html_path"):
        warnings.append("Previous HTML retained in history and on disk but removed from current entry; new input supplies Markdown only")
    users = [entry if row["id"] == args.id else row for row in users]
    if old is None:
        users.append(entry)
    users.sort(key=lambda row: int(row["id"].split("-")[1]))
    commit_change(args, users, wan, {entry["path"]: data}, old,
                  ("Replace " if old else "Add ") + args.id + " source; card extraction requires separate review", warnings)


def register_card(args):
    users, wan = mutation_inputs()
    old = next((row for row in users if row["id"] == args.id), None)
    if old is None:
        raise LibraryError(f"register-card supports existing user models only: {args.id}")
    if args.status == "behavior_checked" and not args.validation_note:
        raise LibraryError("behavior_checked requires --validation-note with the actual validation record")
    if args.card_version is not None and (not args.card_version.strip() or "\n" in args.card_version or "\r" in args.card_version):
        raise LibraryError("card-version must be nonempty, single-line text")
    previous_revision = old.get("card_revision", 0)
    if not isinstance(previous_revision, int) or isinstance(previous_revision, bool) or previous_revision < 0:
        raise LibraryError("Existing card_revision must be a nonnegative integer")
    data = source_bytes(args.card_file)
    note = source_bytes(args.validation_note) if args.validation_note else None
    routing = None
    if args.metadata_file:
        routing = checked_card_metadata(json.loads(source_bytes(args.metadata_file)), {row["id"] for row in wan})
    entry = dict(old)
    entry.update(card_path=f"references/cards/{args.id}.md", card_sha256=digest(data),
                 card_source_sha256=old["source_sha256"], card_status=args.status,
                 card_revision=previous_revision + 1,
                 card_registered_at=datetime.now(timezone.utc).isoformat())
    if args.card_version is not None:
        entry["card_version"] = args.card_version.strip()
    elif entry["card_sha256"] != old.get("card_sha256"):
        # A prior semantic version does not identify newly supplied card content.
        entry.pop("card_version", None)
    if routing is not None:
        entry["card_metadata"] = routing
    elif (entry["card_sha256"] != old.get("card_sha256")
          or old.get("card_source_sha256") != old.get("source_sha256")):
        entry.pop("card_metadata", None)
    payloads = {entry["card_path"]: data}
    # A replacement card must not silently inherit a prior validation record.
    for key in list(entry):
        if key.startswith("validation_note_"):
            del entry[key]
    if note is not None:
        relative = f"references/validation-notes/{args.id}.md"
        entry.update(validation_note_path=relative, validation_note_sha256=digest(note))
        payloads[relative] = note
    users = [entry if row["id"] == args.id else row for row in users]
    commit_change(args, users, wan, payloads, old,
                  f"Register {args.id} card as {args.status}; status supplied by maintainer, not inferred by CLI")


def positive_int(value):
    result = int(value)
    if result < 1:
        raise argparse.ArgumentTypeError("must be positive")
    return result


def parser():
    cli = argparse.ArgumentParser(description=__doc__)
    commands = cli.add_subparsers(dest="command", required=True)
    search_parser = commands.add_parser("search", help="Return lexical candidates and match reasons")
    search_parser.add_argument("query")
    search_parser.add_argument("--limit", type=positive_int, default=8)
    search_parser.set_defaults(run=search)
    show_parser = commands.add_parser("show", help="Inspect entry metadata and optionally its source text")
    show_parser.add_argument("id")
    show_parser.add_argument("--full", action="store_true")
    show_parser.set_defaults(run=show)
    validate_parser = commands.add_parser("validate", help="Check structure, paths, hashes and baseline counts")
    validate_parser.add_argument("--allow-partial", action="store_true", help="Allow small test fixtures without 125/100 baseline")
    validate_parser.set_defaults(run=validate)
    add = commands.add_parser("add-user", help="Preview or apply source addition/replacement")
    add.add_argument("--id", required=True)
    add.add_argument("--title", required=True)
    add.add_argument("--source-file", required=True)
    add.add_argument("--source-url", help="Optional published HTTP(S) source; omit for a supplied manuscript")
    add.add_argument("--source-label", help="Optional manuscript label; defaults to input filename without its directory")
    add.add_argument("--captured-at", required=True)
    add.add_argument("--replace", action="store_true")
    add.add_argument("--apply", action="store_true")
    add.set_defaults(run=add_user)
    register = commands.add_parser("register-card", help="Preview or apply card registration")
    register.add_argument("--id", required=True)
    register.add_argument("--card-file", required=True)
    register.add_argument("--status", required=True, choices=sorted(CARD_STATUSES - {"needs_review"}))
    register.add_argument("--card-version", help="Explicit nonempty card version; changed content otherwise clears the old version")
    register.add_argument("--validation-note")
    register.add_argument("--metadata-file", help="Absolute path to routing metadata JSON; changed cards otherwise clear old routing data")
    register.add_argument("--apply", action="store_true")
    register.set_defaults(run=register_card)
    return cli


def main():
    args = parser().parse_args()
    try:
        return args.run(args) or 0
    except (LibraryError, OSError, UnicodeError, ValueError, TypeError, KeyError) as exc:
        print(f"library: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
