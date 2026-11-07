#!/usr/bin/env python3
"""Xiaohongshu note draft checker for xiaohongshu-publisher skill.

Checks title ≤20 chars, body ≤1000 chars (tags excluded by convention),
tags count 5–10, and scans absolute / medical / finance risk phrases.

Usage:
  python3 scripts/check_note.py sample.json
  python3 scripts/check_note.py note.md
  cat note.json | python3 scripts/check_note.py

JSON shape (any subset):
  {"title": "...", "body": "...", "tags": ["#a", "#b", ...]}

Markdown / plain text: sections headed by 标题 / 正文 / 标签 (or Title / Body / Tags).
Exit 0 = PASS, 1 = FAIL.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

TITLE_MAX = 20
BODY_MAX = 1000
TAGS_MIN = 5
TAGS_MAX = 10

# Proclaim / medical / finance risk phrases (substring match).
ABSOLUTE_WORDS = ["最", "第一", "百分百", "永久", "绝对"]
MEDICAL_BAN = ["根治", "治愈", "疗效保证", "药到病除"]
FINANCE_BAN = ["稳赚", "保本", "零风险", "保证收益", "躺赚"]

# Contexts where 第一 / 最 are often non-claim (order, listing). Soft-skip patterns.
SOFT_OK = [
    re.compile(r"第一[张个条天周月步点]"),
    re.compile(r"第[一二三四五六七八九十\d]+"),
    re.compile(r"最[后近早晚初]"),
]


def char_len(text: str) -> int:
    """Count length: treat each Unicode scalar as 1 (Chinese = 1)."""
    return len(text.strip()) if text else 0


def normalize_tags(tags: Any) -> list[str]:
    if tags is None:
        return []
    if isinstance(tags, str):
        parts = re.split(r"[\s,，、]+", tags.strip())
        return [p for p in parts if p]
    if isinstance(tags, list):
        out: list[str] = []
        for t in tags:
            s = str(t).strip()
            if s:
                out.append(s)
        return out
    return []


def soft_ok(text: str, word: str) -> bool:
    if word not in ("最", "第一"):
        return False
    for pat in SOFT_OK:
        for m in pat.finditer(text):
            if word in m.group(0):
                return True
    return False


def scan_banned(text: str) -> list[str]:
    hits: list[str] = []
    if not text:
        return hits
    for w in ABSOLUTE_WORDS:
        if w in text and not soft_ok(text, w):
            # Still flag; soft_ok only suppresses obvious order uses when pattern matches
            # Re-check: if every occurrence is inside a soft pattern, skip
            if w in ("最", "第一"):
                # Find all occurrences; if all covered by soft patterns, skip
                idxs = [m.start() for m in re.finditer(re.escape(w), text)]
                all_soft = True
                for i in idxs:
                    window = text[max(0, i - 1) : i + 4]
                    covered = any(p.search(window) for p in SOFT_OK)
                    if not covered:
                        all_soft = False
                        break
                if all_soft and idxs:
                    continue
            hits.append(w)
    for w in MEDICAL_BAN + FINANCE_BAN:
        if w in text:
            hits.append(w)
    # dedupe preserve order
    seen = set()
    uniq = []
    for h in hits:
        if h not in seen:
            seen.add(h)
            uniq.append(h)
    return uniq


def parse_json(raw: str) -> dict[str, Any]:
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("JSON root must be an object")
    return {
        "title": str(data.get("title") or ""),
        "body": str(data.get("body") or data.get("content") or ""),
        "tags": normalize_tags(data.get("tags")),
    }


def parse_markdown(raw: str) -> dict[str, Any]:
    title, body, tags_raw = "", "", ""
    # Split by headings
    sections: dict[str, list[str]] = {"title": [], "body": [], "tags": []}
    current = None
    for line in raw.splitlines():
        h = line.strip()
        key = None
        if re.match(r"^#{1,3}\s*(标题|Title)\s*$", h, re.I):
            key = "title"
        elif re.match(r"^#{1,3}\s*(正文|Body|内容)\s*$", h, re.I):
            key = "body"
        elif re.match(r"^#{1,3}\s*(标签|Tags|话题)\s*$", h, re.I):
            key = "tags"
        elif re.match(r"^(标题|Title)\s*[:：]", h, re.I):
            sections["title"].append(re.split(r"[:：]", h, 1)[1].strip())
            current = None
            continue
        elif re.match(r"^(正文|Body)\s*[:：]", h, re.I):
            sections["body"].append(re.split(r"[:：]", h, 1)[1].strip())
            current = "body"
            continue
        elif re.match(r"^(标签|Tags)\s*[:：]", h, re.I):
            sections["tags"].append(re.split(r"[:：]", h, 1)[1].strip())
            current = "tags"
            continue
        if key:
            current = key
            continue
        if current:
            sections[current].append(line)
    title = "\n".join(sections["title"]).strip()
    body = "\n".join(sections["body"]).strip()
    tags_raw = "\n".join(sections["tags"]).strip()
    # Fallback: whole file as body if nothing parsed
    if not title and not body and not tags_raw:
        body = raw.strip()
    return {"title": title, "body": body, "tags": normalize_tags(tags_raw)}


def load_input(argv: list[str]) -> dict[str, Any]:
    if len(argv) >= 2:
        path = Path(argv[1])
        raw = path.read_text(encoding="utf-8")
    else:
        raw = sys.stdin.read()
    raw_strip = raw.strip()
    if not raw_strip:
        raise SystemExit("empty input")
    if raw_strip.startswith("{"):
        return parse_json(raw_strip)
    return parse_markdown(raw)


def check(note: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    title = note.get("title") or ""
    body = note.get("body") or ""
    tags = note.get("tags") or []

    tl = char_len(title)
    if title and tl > TITLE_MAX:
        errors.append(f"标题超长: {tl} > {TITLE_MAX}")
    elif not title:
        errors.append("缺少标题")

    bl = char_len(body)
    if body and bl > BODY_MAX:
        errors.append(f"正文超长: {bl} > {BODY_MAX}（按不含标签计）")
    elif not body:
        errors.append("缺少正文")

    ntags = len(tags)
    if ntags < TAGS_MIN or ntags > TAGS_MAX:
        errors.append(f"标签数量应在 {TAGS_MIN}–{TAGS_MAX}，当前 {ntags}")

    for label, text in (("标题", title), ("正文", body)):
        banned = scan_banned(text)
        if banned:
            errors.append(f"{label}含风险/禁用表述: {', '.join(banned)}")

    return errors


def main() -> int:
    try:
        note = load_input(sys.argv)
    except json.JSONDecodeError as e:
        print(f"FAIL\n无效 JSON: {e}")
        return 1
    except Exception as e:
        print(f"FAIL\n读取失败: {e}")
        return 1

    errors = check(note)
    title = note.get("title") or ""
    body = note.get("body") or ""
    tags = note.get("tags") or []
    print(f"title_len={char_len(title)} body_len={char_len(body)} tags={len(tags)}")
    if errors:
        print("FAIL")
        for e in errors:
            print(f"- {e}")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
