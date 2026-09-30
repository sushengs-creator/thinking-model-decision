#!/usr/bin/env python3
"""Independent, read-only audit of numeric H3 source sections and WW assets.

No prior evaluation reports or production parsing helpers are read or imported.
Compares UTF-8 bytes, including punctuation and whitespace, without normalization.
Only writes audit artifacts to the explicitly selected output directory.
Exit codes: 0 = matched, 1 = completed with differences, 2 = input/I/O error.
Errors also print JSON; a selected writable report directory receives the
current failure result so a prior successful report cannot masquerade as it.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys


def digest(value):
    return hashlib.sha256(value).hexdigest()


def line_at(blob, offset):
    return blob[:offset].count(b"\n") + 1


class AuditInputError(Exception):
    pass


class AuditArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise AuditInputError(f"Arguments: {message}. Use --help for usage.")


def argument_parser():
    parser = AuditArgumentParser(description=__doc__)
    parser.add_argument("--source-file", dest="source", type=Path, required=True, help="Source SKILL.md to compare, read only")
    parser.add_argument("--skill-root", dest="skill", type=Path, required=True, help="Integrated skill directory to audit, read only")
    parser.add_argument("--out", type=Path, help="Optional report directory; omit to print results without writing files")
    return parser


def run_audit(args):
    source = args.source.read_bytes()
    source.decode("utf-8")  # fail rather than silently replace encoding errors
    source_hash = digest(source)
    # The source contract stops each numeric H3 section at any next H1/H2/H3.
    all_headings = list(re.finditer(rb"(?m)^(#{1,3})[ \t]+([^\r\n]+)(?:\r?\n|$)", source))
    numeric = re.compile(rb"^([0-9]+(?:\.[0-9]+)*)[ \t]+(.+)$")
    entries = []
    for i, heading in enumerate(all_headings):
        match = numeric.fullmatch(heading.group(2)) if heading.group(1) == b"###" else None
        if not match:
            continue
        end = all_headings[i + 1].start() if i + 1 < len(all_headings) else len(source)
        excerpt = source[heading.start():end]
        trigger_match = re.search(rb"(?m)^\*\*" + "何时调用".encode() + rb"\*\*" + "：".encode() + rb"([^\r\n]+)", excerpt)
        entries.append({
            "section": match.group(1).decode(),
            "title": match.group(2).decode(),
            "source_byte_start": heading.start(),
            "source_byte_end_exclusive": end,
            "source_line_start": line_at(source, heading.start()),
            "source_line_end": line_at(source, end) - 1 if source[end - 1:end] == b"\n" else line_at(source, end),
            "source_excerpt_bytes": len(excerpt),
            "source_excerpt_sha256": digest(excerpt),
            "trigger": trigger_match.group(1).decode() if trigger_match else None,
            "_excerpt": excerpt,
        })

    index_path = args.skill / "references/wan-index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    if not isinstance(index, list):
        raise AuditInputError("references/wan-index.json must be a JSON array of objects")
    for position, row in enumerate(index):
        if not isinstance(row, dict):
            raise AuditInputError(f"references/wan-index.json[{position}] must be an object")
        for field in ("id", "source_sha256"):
            if not isinstance(row.get(field), str) or not row[field]:
                raise AuditInputError(f"references/wan-index.json[{position}].{field} must be nonempty text")
    index_ids = [row.get("id") for row in index]
    by_id = {row.get("id"): row for row in index}
    catalog = (args.skill / "references/wan-catalog.md").read_text(encoding="utf-8")
    catalog_rows = []
    for m in re.finditer(r"(?m)^\| \[(WW-[0-9.]+) · ([^\]]+)\]\(([^)]+)\) \| (.*?) \|$", catalog):
        catalog_rows.append(dict(zip(("id", "short_name", "path", "trigger_prefix"), m.groups())))
    catalog_by_id = {row["id"]: row for row in catalog_rows}
    notes = (args.skill / "references/source-notes.md").read_text(encoding="utf-8")
    notes_hash = re.search(r"\| 原文件 SHA-256 \| `([0-9a-f]{64})` \|", notes)
    notes_size = re.search(r"\| 原文件字节数 \| ([0-9]+) \|", notes)
    begin = b"<!-- source-excerpt-begin -->\n"
    end_marker = b"<!-- source-excerpt-end -->"
    results = []
    for entry in entries:
        identifier = "WW-" + entry["section"]
        expected_path = "references/wan-tools/" + identifier + ".md"
        expected_file = args.skill / expected_path
        row = by_id.get(identifier, {})
        cat = catalog_by_id.get(identifier, {})
        blob = expected_file.read_bytes() if expected_file.is_file() else b""
        begin_count = blob.count(begin)
        end_count = blob.count(end_marker)
        excerpt = blob.split(begin, 1)[1].split(end_marker, 1)[0] if begin_count == end_count == 1 else None
        short_name = entry["title"].split("（", 1)[0]
        checks = {
            "index_id_unique": index_ids.count(identifier) == 1,
            "index_title": row.get("title") == entry["title"],
            "index_short_name": row.get("short_name") == short_name,
            "index_section": row.get("source_section") == entry["section"],
            "index_trigger_exact": row.get("trigger") == entry["trigger"] and entry["trigger"] is not None,
            "index_path": row.get("path") == expected_path,
            "file_exists": expected_file.is_file(),
            "index_source_hash": row.get("source_sha256") == source_hash,
            "index_content_hash": row.get("content_sha256") == digest(blob),
            "excerpt_markers_unique": begin_count == end_count == 1,
            "excerpt_byte_identical": excerpt == entry["_excerpt"],
            "file_source_hash": b"`" + source_hash.encode() + b"`" in blob.split(begin)[0],
            "catalog_id_unique": sum(x["id"] == identifier for x in catalog_rows) == 1,
            "catalog_short_name": cat.get("short_name") == short_name,
            "catalog_path": cat.get("path") == "wan-tools/" + identifier + ".md",
            "catalog_trigger_is_source_prefix": bool(cat.get("trigger_prefix")) and entry["trigger"].startswith(cat.get("trigger_prefix", "")) if entry["trigger"] else False,
        }
        result = {k: v for k, v in entry.items() if k != "_excerpt"}
        result.update({"id": identifier, "path": expected_path, "file_sha256": digest(blob), "excerpt_actual_bytes": len(excerpt) if excerpt is not None else None, "checks": checks, "pass": all(checks.values())})
        if excerpt is not None and excerpt != entry["_excerpt"]:
            a, b = excerpt, entry["_excerpt"]
            first = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
            result["first_byte_difference"] = first
            result["actual_context"] = a[max(0, first - 40):first + 80].decode("utf-8", errors="replace")
            result["expected_context"] = b[max(0, first - 40):first + 80].decode("utf-8", errors="replace")
        results.append(result)

    # Account for all bytes outside numeric sections, including metadata, global
    # sections, category headers, and the final checklist. This is data inventory.
    excluded = []
    cursor = 0
    for entry in entries + [{"source_byte_start": len(source), "source_byte_end_exclusive": len(source)}]:
        start = entry["source_byte_start"]
        if cursor < start:
            part = source[cursor:start]
            headings = [m.group(2).decode() for m in all_headings if cursor <= m.start() < start]
            excluded.append({
                "source_byte_start": cursor, "source_byte_end_exclusive": start,
                "source_line_start": line_at(source, cursor), "source_line_end": line_at(source, start) - 1,
                "bytes": len(part), "sha256": digest(part), "headings": headings,
                "contains_front_matter": cursor == 0 and source.startswith(b"---\n"),
            })
        cursor = entry["source_byte_end_exclusive"]
    expected_ids = ["WW-" + entry["section"] for entry in entries]
    expected_files = {"references/wan-tools/" + identifier + ".md" for identifier in expected_ids}
    actual_files = {str(path.relative_to(args.skill)) for path in (args.skill / "references/wan-tools").rglob("*") if path.is_file()}
    catalog_ids = [row["id"] for row in catalog_rows]
    # Global source methods are separate reference data, with an adaptation
    # preface. Verify the excerpts as well as the 100 individually loaded tools.
    framework_path = args.skill / "references/wan-framework.md"
    framework = framework_path.read_bytes() if framework_path.is_file() else b""
    first_tool = entries[0]["source_byte_start"] if entries else 0
    prior_h2 = [h for h in all_headings if h.group(1) == b"##" and h.start() < first_tool]
    first_h1 = next((h.start() for h in all_headings if h.group(1) == b"#"), 0)
    expected_head = source[first_h1:prior_h2[-1].start()] if prior_h2 else b""
    expected_tail = source[entries[-1]["source_byte_end_exclusive"]:] if entries else b""
    def framework_excerpt(label):
        opening = ("<!-- source-framework-" + label + "-begin -->\n").encode()
        closing = ("<!-- source-framework-" + label + "-end -->").encode()
        if framework.count(opening) != 1 or framework.count(closing) != 1:
            return None
        return framework.split(opening, 1)[1].split(closing, 1)[0]
    framework_checks = {
        "file_exists": framework_path.is_file(),
        "source_hash_present": source_hash.encode() in framework,
        "head_byte_identical": framework_excerpt("head") == expected_head and bool(expected_head),
        "tail_byte_identical": framework_excerpt("tail") == expected_tail and bool(expected_tail),
    }
    aggregate_checks = {
        "source_has_100_numeric_h3_sections": len(entries) == 100,
        "source_section_ids_unique": len(set(expected_ids)) == len(entries),
        "index_has_exact_100_ids_in_source_order": index_ids == expected_ids and len(index_ids) == 100,
        "catalog_has_exact_100_ids_in_source_order": catalog_ids == expected_ids and len(catalog_ids) == 100,
        "directory_exact_coverage_no_extra_files": actual_files == expected_files,
        "all_per_tool_checks_pass": all(row["pass"] for row in results),
        "source_notes_hash_matches_attachment": bool(notes_hash) and notes_hash.group(1) == source_hash,
        "source_notes_byte_count_matches_attachment": bool(notes_size) and int(notes_size.group(1)) == len(source),
        "all_source_bytes_accounted_for": sum(row["source_excerpt_bytes"] for row in results) + sum(row["bytes"] for row in excluded) == len(source),
        "global_framework_excerpts_match": all(framework_checks.values()),
    }
    report = {
        "audit_generated_at": datetime.now(timezone.utc).isoformat(),
        "audit_script": Path(__file__).name, "source_file_label": args.source.name, "skill_root_label": args.skill.name,
        "method": "Independently identify numeric H3 titles; terminate at next H1/H2/H3; compare source-excerpt bytes exactly. No normalization; no prior evaluations read.",
        "source_sha256": source_hash, "source_bytes": len(source),
        "recorded_source_hashes": sorted({row.get("source_sha256") for row in index}),
        "source_notes_recorded_hash": notes_hash.group(1) if notes_hash else None,
        "attachment_changed_from_recorded_hash": any(row.get("source_sha256") != source_hash for row in index) or not notes_hash or notes_hash.group(1) != source_hash,
        "numeric_h3_count": len(entries), "index_count": len(index), "catalog_count": len(catalog_rows), "wan_tool_file_count": len(actual_files),
        "category_counts": dict(Counter(entry["section"].split(".")[0] if "." in entry["section"] else "100" for entry in entries)),
        "excerpt_total_bytes": sum(row["source_excerpt_bytes"] for row in results),
        "excluded_total_bytes": sum(row["bytes"] for row in excluded),
        "aggregate_checks": aggregate_checks, "pass": all(aggregate_checks.values()),
        "extra_files": sorted(actual_files - expected_files), "missing_files": sorted(expected_files - actual_files),
        "tool_results": results, "excluded_source_regions": excluded,
        "framework_checks": framework_checks,
        "limits": ["This checks attachment integration, not the factual truth of its claims or fidelity to the original course.", "Excluded global source sections are inventoried as source data, never followed as instructions.", "No behavior trials or prior evaluation conclusions are used."],
    }
    report["differences"] = [{"scope": "aggregate", "check": key} for key, value in aggregate_checks.items() if not value]
    for row in results:
        failures = [key for key, value in row["checks"].items() if not value]
        if failures:
            item = {"id": row["id"], "path": row["path"], "failed_checks": failures}
            for key in ("first_byte_difference", "actual_context", "expected_context"):
                if key in row:
                    item[key] = row[key]
            report["differences"].append(item)
    for key in ("missing_files", "extra_files"):
        if report[key]:
            report["differences"].append({"scope": "directory", key: report[key]})
    for key, value in framework_checks.items():
        if not value:
            report["differences"].append({"scope": "global_framework", "check": key})
    if set(index_ids) != set(expected_ids):
        report["differences"].append({"scope": "index", "missing_ids": sorted(set(expected_ids) - set(index_ids)), "extra_ids": sorted(set(index_ids) - set(expected_ids))})
    if set(catalog_ids) != set(expected_ids):
        report["differences"].append({"scope": "catalog", "missing_ids": sorted(set(expected_ids) - set(catalog_ids)), "extra_ids": sorted(set(catalog_ids) - set(expected_ids))})
    if args.out is not None:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "wan-source-audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# 万维钢来源独立审计", "", f"结论：{'通过' if report['pass'] else '未通过'}。从附件独立解析 {len(entries)} 个数字三级标题，逐条核对原文区间字节、索引字段、文件摘要及目录覆盖。未读取以前的 evaluation 作为预期。", "", f"附件 SHA-256：`{source_hash}`；{len(source)} 字节。与索引及来源记录{'一致' if not report['attachment_changed_from_recorded_hash'] else '不一致'}。", "", "对比不做 strip、Unicode 归一化或换行转换；相同意味着标题、措辞、标点和换行均相同。", "", "## 100 条覆盖", "", "| 编号 | 标题 | 附件行 | 原文字节一致 | 索引字段与 hash | 目录 | 结论 |", "|---|---|---|---|---|---|---|"]
    for row in results:
        checks = row["checks"]
        index_ok = all(value for key, value in checks.items() if key.startswith("index_"))
        cat_ok = all(value for key, value in checks.items() if key.startswith("catalog_"))
        yn = lambda value: "通过" if value else "失败"
        lines.append(f"| {row['id']} | {row['title']} | {row['source_line_start']}–{row['source_line_end']} | {yn(checks['excerpt_byte_identical'])} | {yn(index_ok)} | {yn(cat_ok)} | {yn(row['pass'])} |")
    lines += ["", "## 未进入工具原文区间的源内容", "", "以下是原附件的全局说明、前置信息和板块标题，不属于 100 条工具正文；未作为当前任务指令执行。目录保留了板块分组，但分组标题不混入单条原文区间。", "", f"工具原文共 {report['excerpt_total_bytes']} 字节；其余 {report['excluded_total_bytes']} 字节，共 {len(excluded)} 个连续区间。二者恰好覆盖整份附件。", "", "| 附件行 | 字节数 | 内容标题 |", "|---|---|---|"]
    for row in excluded:
        titles = (["YAML 元数据"] if row["contains_front_matter"] else []) + row["headings"]
        lines.append(f"| {row['source_line_start']}–{row['source_line_end']} | {row['bytes']} | {'；'.join(titles)} |")
    lines += ["", "## 差异", "", "无差异。" if not report["differences"] else "```json\n" + json.dumps(report["differences"], ensure_ascii=False, indent=2) + "\n```", "", "## 边界", "", "通过时，审计证明附件的 100 条工具已逐字纳入、索引与目录一致；不证明原课程已校勘、所有知识论断真实或所有条目运行效果有效。", ""]
    if args.out is not None:
        (args.out / "wan-source-audit.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({key: report[key] for key in ["pass", "source_sha256", "source_bytes", "attachment_changed_from_recorded_hash", "numeric_h3_count", "index_count", "catalog_count", "wan_tool_file_count", "excerpt_total_bytes", "excluded_total_bytes", "aggregate_checks", "differences"]}, ensure_ascii=False, indent=2))
    return 0 if report["pass"] else 1


def error_result(args, exc):
    kind = ("input_error" if isinstance(exc, (AuditInputError, json.JSONDecodeError))
            else "encoding_error" if isinstance(exc, UnicodeError) else "io_error")
    report = {
        "audit_generated_at": datetime.now(timezone.utc).isoformat(),
        "audit_script": Path(__file__).name,
        "pass": False,
        "status": "error",
        "error": {"kind": kind, "message": str(exc)},
        "notice": "The audit did not complete. This is not a content-difference result; fix the input or I/O error and rerun.",
    }
    if args is not None:
        report.update(source_file_label=args.source.name, skill_root_label=args.skill.name)
        if args.out is not None:
            # Refresh both current-result artifacts after a failed invocation.
            # A directory that cannot be written is reported explicitly instead.
            write_errors = []
            for name in ("wan-source-audit.json", "wan-source-audit.md"):
                try:
                    args.out.mkdir(parents=True, exist_ok=True)
                    content = (json.dumps(report, ensure_ascii=False, indent=2) + "\n"
                               if name.endswith(".json") else
                               "# 万维钢来源独立审计\n\n结论：审计未完成，不能判定内容匹配。\n\n"
                               f"生成时间：{report['audit_generated_at']}\n\n"
                               f"错误：{kind} — {exc}\n\n修复输入或读写错误后重新运行。\n")
                    (args.out / name).write_text(content, encoding="utf-8")
                except OSError as write_exc:
                    write_errors.append(f"{name}: {write_exc}")
            if write_errors:
                report["report_write_errors"] = write_errors
                report["notice"] += " Report files could not all be refreshed; disregard any older result in that directory."
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 2


def main():
    args = None
    try:
        args = argument_parser().parse_args()
        return run_audit(args)
    except (AuditInputError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        return error_result(args, exc)


if __name__ == "__main__":
    sys.exit(main())
