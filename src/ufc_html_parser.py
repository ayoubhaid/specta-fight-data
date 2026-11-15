"""Parse locally saved athlete-page HTML for learning; performs no network requests."""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional


class Node:
    def __init__(self, tag: str, attrs: dict[str, Optional[str]]):
        self.tag = tag
        self.attrs = attrs
        self.children: list[Node | str] = []

    def text(self) -> str:
        return " ".join(
            part for child in self.children
            for part in ([child] if isinstance(child, str) else [child.text()])
            if part
        ).strip()


class TreeParser(HTMLParser):
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
            "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("document", {})
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, dict(attrs))
        self.stack[-1].children.append(node)
        if tag not in self.VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.stack[-1].children.append(Node(tag, dict(attrs)))

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        if data.strip():
            self.stack[-1].children.append(data.strip())


def walk(node: Node):
    for child in node.children:
        if isinstance(child, Node):
            yield child
            yield from walk(child)


def by_class(root: Node, class_name: str) -> Optional[Node]:
    for node in walk(root):
        if class_name in (node.attrs.get("class") or "").split():
            return node
    return None


def clean(node: Optional[Node]) -> Optional[str]:
    if node is None:
        return None
    value = re.sub(r"\\s+", " ", node.text()).strip()
    return value or None


def slug_from_path(path: Path) -> str:
    return re.sub(r"[^a-z0-9]+", "-", path.stem.lower()).strip("-")


def parse_athlete_html(html: str, source_file: str = "unknown.html") -> dict:
    parser = TreeParser()
    parser.feed(html)
    root = parser.root

    name = clean(by_class(root, "hero__title"))
    nickname = clean(by_class(root, "hero__nickname"))
    record_display = clean(by_class(root, "hero__record"))
    if not name:
        raise ValueError(f"No .hero__title found in {source_file}; check the saved HTML/selectors.")

    return {
        "schema_version": 1,
        "provider": "ufc_html_local_sample",
        "provider_id": slug_from_path(Path(source_file)),
        "slug": slug_from_path(Path(source_file)),
        "name": name,
        "nickname": nickname,
        "record": {
            "wins": None, "losses": None, "draws": None,
            "no_contests": None, "display": record_display
        } if record_display else None,
        "career_stats": None,
        "history": [],
        "source_provenance": {
            "type": "user_supplied_local_html",
            "file_name": Path(source_file).name,
            "selector_map": {
                "name": ".hero__title",
                "nickname": ".hero__nickname",
                "record": ".hero__record"
            }
        },
        "retrieved_at": datetime.now(timezone.utc).isoformat()
    }


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("input", help="Saved HTML file or directory of .html files")
    cli.add_argument("--output", "-o", default="fighters.local.json")
    args = cli.parse_args()

    source = Path(args.input)
    files = sorted(source.glob("*.html")) if source.is_dir() else [source]
    if not files:
        cli.error("No .html files found.")

    fighters = []
    for file in files:
        try:
            fighters.append(parse_athlete_html(file.read_text(encoding="utf-8"), str(file)))
        except (OSError, UnicodeError, ValueError) as exc:
            print(f"SKIP {file}: {exc}")

    Path(args.output).write_text(
        json.dumps({"schema_version": 1, "fighters": fighters}, indent=2, ensure_ascii=False) + "\\n",
        encoding="utf-8"
    )
    print(f"Wrote {len(fighters)} fighter profile(s) to {args.output}")


if __name__ == "__main__":
    main()
