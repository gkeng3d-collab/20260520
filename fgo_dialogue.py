#!/usr/bin/env python3
"""Download and extract story dialogue from Fate/Grand Order via Atlas Academy.

Examples:
    # Fuyuki (Singularity F) — full chapter, Japanese
    python fgo_dialogue.py --region JP --war 100

    # Fuyuki in English (NA server)
    python fgo_dialogue.py --region NA --war 100

    # One script only / offline file
    python fgo_dialogue.py --region JP --script 0100000110
    python fgo_dialogue.py --from-file 0100000110.txt

    # Full-text search (same engine as https://apps.atlasacademy.io/db/JP/scripts)
    python fgo_dialogue.py --region JP --search "カルデア" --war-filter 100

Script format rules follow Atlas Academy DB's parser
(apps/packages/db/src/Component/Script.tsx).
"""

import argparse
import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

API_HOST = "https://api.atlasacademy.io"
DB_HOST = "https://apps.atlasacademy.io/db"
USER_AGENT = "fgo-dialogue-extractor/1.0"
REQUEST_DELAY_SEC = 0.15


# ---------------------------------------------------------------- HTTP helpers

def http_get(url: str, retries: int = 3) -> bytes:
    last_error = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read()
            time.sleep(REQUEST_DELAY_SEC)
            return data
        except Exception as exc:  # noqa: BLE001 - retry on any network error
            last_error = exc
            time.sleep(2 ** attempt)
    raise RuntimeError(f"GET {url} failed after {retries} tries: {last_error}")


def api_json(path: str, params: dict | None = None):
    url = f"{API_HOST}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params, doseq=True)
    return json.loads(http_get(url).decode("utf-8"))


# ------------------------------------------------------------- script parsing
# Punctuation is full-width except on the KR server.

def punctuation(region: str):
    if region == "KR":
        return ":", "?", "!"
    return "：", "？", "！"


def split_tokens(line: str) -> list[str]:
    """Split a dialogue line into text runs and [bracket] tokens.

    Nested brackets stay inside one token: 'a[x [y]]b' -> ['a', '[x [y]]', 'b']
    """
    tokens, word, depth = [], "", 0
    for char in line:
        if char == "[":
            if depth == 0:
                if word:
                    tokens.append(word)
                word = "["
            else:
                word += "["
            depth += 1
        elif char == "]":
            depth -= 1
            word += "]"
            if depth == 0:
                tokens.append(word)
                word = ""
        else:
            word += char
    if word:
        tokens.append(word)
    return tokens


def split_outside_brackets(text: str, sep: str) -> list[str]:
    """Split on the first `sep` that is not inside [brackets]."""
    depth = 0
    for i, char in enumerate(text):
        if char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
        elif char == sep and depth == 0:
            return [text[:i], text[i + 1:]]
    return [text]


HEX_COLOR = re.compile(r"^[0-9a-fA-F]{6}$")


class Renderer:
    """Turn raw dialogue markup into plain readable text."""

    def __init__(self, player_name: str, gender: str):
        self.player_name = player_name
        self.gender = gender  # male | female | both

    def render(self, raw: str) -> str:
        parts = [self.render_token(token) for token in split_tokens(raw)]
        text = "".join(parts)
        return "\n".join(seg.rstrip() for seg in text.split("\n")).strip("\n")

    def render_token(self, token: str) -> str:
        if not token.startswith("["):
            return token
        if token.startswith("[#"):  # ruby: [#text:reading]
            body = token[2:-1]
            text, _, ruby = body.partition(":")
            return f"{text}（{ruby}）" if ruby else text
        if token.startswith("[&") and ":" in token:  # gender: [&male:female]
            male, female = (split_outside_brackets(token[2:-1], ":") + [""])[:2]
            male_text = "".join(self.render_token(t) for t in split_tokens(male))
            female_text = "".join(self.render_token(t) for t in split_tokens(female))
            if self.gender == "male":
                return male_text
            if self.gender == "female":
                return female_text
            return male_text if male_text == female_text else f"{male_text}／{female_text}"

        params = token[1:-1].split()
        if not params:
            return ""
        head = params[0]

        if head in ("r", "sr", "csr"):
            return "\n"
        if head == "%1":
            return self.player_name
        if head == "line" or re.fullmatch(r"line[0-9.]+", head):
            return "――"
        if head == "servantName":  # [servantName id:hidden:true]
            body = token[1:-1].replace("servantName ", "", 1)
            fields = body.split(":")
            if len(fields) >= 3:
                hidden, true_name = fields[1], fields[2]
                return hidden if hidden == true_name else f"{hidden}（{true_name}）"
            return body
        if head in ("image", "i"):  # [image name:ruby]
            body = token[1:-1].split(":")
            name = body[0].split()[-1] if body[0].split() else ""
            return body[1] if len(body) > 1 and body[1] else f"〔{name}〕"
        # Formatting / scene / sound tokens carry no dialogue text.
        return ""


class Block:
    def __init__(self, kind: str, speaker: str | None, text: str, choice_id: int | None = None):
        self.kind = kind  # dialogue | choice
        self.speaker = speaker
        self.text = text
        self.choice_id = choice_id


def parse_script(raw: str, region: str, renderer: Renderer) -> list[Block]:
    """Mirror Atlas Academy's parseScript() but keep only spoken/readable text."""
    colon, qmark, emark = punctuation(region)
    blocks: list[Block] = []
    speaker: str | None = None
    lines: list[str] = []
    in_dialogue = False

    def finalize():
        nonlocal speaker, lines, in_dialogue
        text = renderer.render("".join(lines))
        if text:
            blocks.append(Block("dialogue", speaker, text))
        speaker, lines, in_dialogue = None, [], False

    for line in raw.replace("\r\n", "\n").split("\n"):
        if line.startswith("//"):
            continue
        if not line:
            continue
        first = line[0]

        if first == "＄":  # script info header, e.g. ＄01-00-08-19-2-2
            continue
        if first == "[":
            head = line[1:-1].split()[0] if len(line) > 2 else ""
            if line in ("[k]", "[page]", "[q]") or head in ("k", "page", "q"):
                finalize()
            elif head in ("tVoice", "tVoiceUser"):
                continue  # voice clip reference for the pending dialogue
            elif in_dialogue:
                lines.append(line)
                if line.endswith("[k]") or line.endswith("[q]"):
                    finalize()
            # otherwise: scene command (charaSet, bgm, se, ...) — no text
            continue
        if first == "＠":
            in_dialogue = True
            name = line[1:]
            if colon in name:
                name = name.split(colon, 1)[1]  # drop speaker code "A："
            if "=spot" in name:
                name = name.split("=spot")[0]
            speaker = renderer.render(name) or None
            continue
        if first == qmark:
            if len(line) > 1 and line[1] == emark:  # ？！ = end of choice branches
                continue
            detail_and_text = split_outside_brackets(line[1:], colon)
            if len(detail_and_text) == 2:
                detail, option_text = detail_and_text
                head = detail.split(",")[0]
                digits = "".join(chr(ord(c) - 0xFEE0) if "０" <= c <= "９" else c for c in head)
                digits = re.sub(r"[^0-9]", "", digits)
                choice_id = int(digits) if digits else None
                blocks.append(Block("choice", None, renderer.render(option_text), choice_id))
            continue
        # plain text: dialogue or narration content
        lines.append(line)
        if line.endswith("[k]") or line.endswith("[q]"):
            finalize()

    finalize()  # flush trailing block without [k]
    return blocks


def format_blocks(blocks: list[Block]) -> str:
    out = []
    for block in blocks:
        if block.kind == "choice":
            number = f"{block.choice_id}" if block.choice_id is not None else "-"
            out.append(f"▼ 選択肢{number}： {block.text}")
        elif block.speaker:
            out.append(f"【{block.speaker}】\n{block.text}")
        else:
            out.append(block.text)
    return "\n\n".join(out) + "\n"


# -------------------------------------------------------------- lorebook mode
# SillyTavern "World Info" (V2) JSON. Each downloaded script becomes one entry
# keyed by its quest name and the speakers appearing in it.

ST_ENTRY_DEFAULTS = {
    "keysecondary": [], "constant": False, "vectorized": False,
    "selective": True, "selectiveLogic": 0, "addMemo": True, "order": 100,
    "position": 0, "disable": False, "excludeRecursion": False,
    "preventRecursion": False, "delayUntilRecursion": False,
    "probability": 100, "useProbability": True, "depth": 4, "group": "",
    "groupOverride": False, "groupWeight": 100, "scanDepth": None,
    "caseSensitive": None, "matchWholeWords": None, "useGroupScoring": None,
    "automationId": "", "role": None, "sticky": 0, "cooldown": 0, "delay": 0,
}


def speaker_keys(speaker: str) -> list[str]:
    """'？？？（マシュ・キリエライト）' → both hidden and true names."""
    match = re.match(r"^(.*?)（(.+?)）$", speaker)
    names = [match.group(1), match.group(2)] if match else [speaker]
    return [n for n in names if n and n != "？？？"]


def section_speakers(blocks: list[Block]) -> list[str]:
    seen: list[str] = []
    for block in blocks:
        if block.kind == "dialogue" and block.speaker:
            for name in speaker_keys(block.speaker):
                if name not in seen:
                    seen.append(name)
    return seen


def build_lorebook(title: str, sections: list[dict]) -> dict:
    entries = {}
    toc = "\n".join(f"- {section['title']}" for section in sections)
    entries["0"] = {
        **ST_ENTRY_DEFAULTS, "uid": 0, "key": [], "selective": False,
        "constant": True, "displayIndex": 0,
        "comment": f"{title} — overview",
        "content": f"[Story reference: {title}]\nSections in order:\n{toc}",
    }
    for index, section in enumerate(sections, start=1):
        keys: list[str] = []
        for key in [section["quest_name"], *section["speakers"]]:
            if key and key not in keys:
                keys.append(key)
        entries[str(index)] = {
            **ST_ENTRY_DEFAULTS, "uid": index, "key": keys[:10],
            "displayIndex": index,
            "comment": f"{section['title']} (script {section['script_id']})",
            "content": f"[{title} — {section['title']} — transcript]\n{section['text']}",
        }
    return {"entries": entries}


def write_lorebook(path: Path, title: str, sections: list[dict]):
    path.write_text(
        json.dumps(build_lorebook(title, sections), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"lorebook → {path}  ({len(sections)} section entries)")


SECTION_HEADER = re.compile(
    r"Quest (?P<quest>\d+) — (?P<name>.*) \(phase (?P<phase>\d+)\)\n"
    r"Script (?P<script>\S+)"
)


def lorebook_from_dir(directory: Path, title: str | None):
    """Rebuild a lorebook from per-script .txt files written by this tool."""
    sections = []
    for file in sorted(directory.glob("*.txt")):
        if file.name.startswith("_") or file.name.endswith(".raw.txt"):
            continue
        text = file.read_text(encoding="utf-8")
        match = SECTION_HEADER.search(text)
        if not match:
            continue
        body = text.split("=" * 60)[-1].strip("\n")
        speakers: list[str] = []
        for speaker in re.findall(r"^【(.+?)】", body, re.M):
            for name in speaker_keys(speaker):
                if name not in speakers:
                    speakers.append(name)
        sections.append({
            "title": f"{match['name']} (phase {match['phase']})",
            "quest_name": match["name"],
            "script_id": match["script"],
            "speakers": speakers,
            "text": body,
        })
    if not sections:
        print(f"No section files found in {directory}")
        return
    write_lorebook(directory / "lorebook.json", title or directory.name, sections)


def merge_lorebooks(paths: list[Path], out_path: Path):
    """Concatenate several lorebook JSONs, renumbering uid/displayIndex."""
    merged: dict[str, dict] = {}
    uid = 0
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        for _, entry in sorted(data.get("entries", {}).items(), key=lambda kv: int(kv[0])):
            merged[str(uid)] = {**entry, "uid": uid, "displayIndex": uid}
            uid += 1
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({"entries": merged}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"merged {len(paths)} lorebooks → {out_path}  ({uid} entries)")


# ------------------------------------------------------------------ API flows

def iter_war_scripts(region: str, war_id: int):
    """Yield (quest, phase, script_link) for every script in a war, in order."""
    war = api_json(f"/nice/{region}/war/{war_id}")
    quests = [q for spot in war.get("spots", []) for q in spot.get("quests", [])]
    quests.sort(key=lambda q: q["id"])
    for quest in quests:
        for phase_scripts in sorted(quest.get("phaseScripts", []), key=lambda p: p["phase"]):
            for script in phase_scripts.get("scripts", []):
                yield war, quest, phase_scripts["phase"], script


def download_war(region: str, war_id: int, out_dir: Path, renderer: Renderer,
                 keep_raw: bool, lorebook: bool = False):
    out_dir.mkdir(parents=True, exist_ok=True)
    merged: list[str] = []
    sections: list[dict] = []
    war_name = ""
    for war, quest, phase, script in iter_war_scripts(region, war_id):
        war_name = war.get("longName") or war.get("name") or str(war_id)
        script_id = script["scriptId"]
        raw = http_get(script["script"]).decode("utf-8-sig")
        if keep_raw:
            (out_dir / f"{script_id}.raw.txt").write_text(raw, encoding="utf-8")
        header = (
            f"{'=' * 60}\n"
            f"Quest {quest['id']} — {quest['name']} (phase {phase})\n"
            f"Script {script_id}  |  {DB_HOST}/{region}/script/{script_id}\n"
            f"{'=' * 60}\n\n"
        )
        blocks = parse_script(raw, region, renderer)
        body = format_blocks(blocks)
        file_path = out_dir / f"{quest['id']}_{phase}_{script_id}.txt"
        file_path.write_text(header + body, encoding="utf-8")
        merged.append(header + body)
        sections.append({
            "title": f"{quest['name']} (phase {phase})",
            "quest_name": quest["name"],
            "script_id": script_id,
            "speakers": section_speakers(blocks),
            "text": body.strip("\n"),
        })
        print(f"  {file_path}")
    if merged:
        title = f"{war_name} (war {war_id}, {region})\n\n"
        (out_dir / "_all_dialogue.txt").write_text(title + "\n".join(merged), encoding="utf-8")
        print(f"\n{len(merged)} scripts → {out_dir}/_all_dialogue.txt")
        if lorebook:
            write_lorebook(out_dir / "lorebook.json", f"{war_name} ({region})", sections)
    else:
        print("No scripts found for this war.")


def download_single(region: str, script_id: str, out_dir: Path, renderer: Renderer, keep_raw: bool):
    info = api_json(f"/nice/{region}/script/{script_id}")
    raw = http_get(info["script"]).decode("utf-8-sig")
    out_dir.mkdir(parents=True, exist_ok=True)
    if keep_raw:
        (out_dir / f"{script_id}.raw.txt").write_text(raw, encoding="utf-8")
    path = out_dir / f"{script_id}.txt"
    path.write_text(format_blocks(parse_script(raw, region, renderer)), encoding="utf-8")
    print(f"→ {path}")


TAG = re.compile(r"<[^>]+>")


def search_scripts(region: str, query: str, war_id: int | None, limit: int):
    params = {"query": query, "limit": limit}
    if war_id is not None:
        params["warId"] = war_id
    results = api_json(f"/nice/{region}/script/search", params)
    for result in sorted(results, key=lambda r: -r["score"]):
        snippet = html.unescape(TAG.sub("", result["snippets"][0])) if result["snippets"] else ""
        print(f"{result['scriptId']}  (score {result['score']})")
        print(f"  {snippet}")
        print(f"  {DB_HOST}/{region}/script/{result['scriptId']}\n")
    print(f"{len(results)} result(s)")


# ------------------------------------------------------------------------ CLI

def main() -> int:
    parser = argparse.ArgumentParser(description="Extract FGO story dialogue via Atlas Academy")
    parser.add_argument("--region", default="JP", choices=["JP", "NA", "CN", "TW", "KR"])
    parser.add_argument("--war", type=int, help="war id, e.g. 100 = Singularity F (Fuyuki)")
    parser.add_argument("--script", help="single script id, e.g. 0100000110")
    parser.add_argument("--from-file", help="parse an already-downloaded raw script file")
    parser.add_argument("--search", help="full-text search query")
    parser.add_argument("--war-filter", type=int, help="restrict --search to one war id")
    parser.add_argument("--limit", type=int, default=50, help="max search results")
    parser.add_argument("--out", default="output", help="output directory")
    parser.add_argument("--raw", action="store_true", help="also keep raw script files")
    parser.add_argument("--lorebook", action="store_true",
                        help="with --war: also write a SillyTavern lorebook.json")
    parser.add_argument("--lorebook-from", metavar="DIR",
                        help="build lorebook.json from an existing output directory")
    parser.add_argument("--lorebook-title", help="title used inside the lorebook")
    parser.add_argument("--merge-lorebooks", metavar="FILE", nargs="+",
                        help="merge lorebook JSON files into one")
    parser.add_argument("--lorebook-out", default="lorebook_merged.json",
                        help="output file for --merge-lorebooks")
    parser.add_argument("--gender", default="both", choices=["male", "female", "both"],
                        help="which protagonist-gender text variant to keep")
    parser.add_argument("--player-name", default=None, help="text used for the [%%1] placeholder")
    args = parser.parse_args()

    player = args.player_name or ("藤丸立香" if args.region == "JP" else "Ritsuka")
    renderer = Renderer(player, args.gender)

    if args.merge_lorebooks:
        merge_lorebooks([Path(p) for p in args.merge_lorebooks], Path(args.lorebook_out))
        return 0
    if args.lorebook_from:
        lorebook_from_dir(Path(args.lorebook_from), args.lorebook_title)
        return 0
    if args.from_file:
        raw = Path(args.from_file).read_text(encoding="utf-8-sig")
        print(format_blocks(parse_script(raw, args.region, renderer)), end="")
        return 0
    if args.search:
        search_scripts(args.region, args.search, args.war_filter, args.limit)
        return 0
    if args.script:
        download_single(args.region, args.script, Path(args.out) / args.region, renderer, args.raw)
        return 0
    if args.war is not None:
        out_dir = Path(args.out) / args.region / f"war{args.war}"
        download_war(args.region, args.war, out_dir, renderer, args.raw, args.lorebook)
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
