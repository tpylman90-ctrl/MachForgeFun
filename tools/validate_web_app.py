"""Check the single-file web app structure and parse its inline JavaScript."""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import re
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "index.html"
REQUIRED_IDS = {
    "profile",
    "range",
    "velocity-chart",
    "altitude-chart",
    "fire",
    "impact-result",
}


class AppParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.local_assets: list[str] = []
        self.scripts: list[str] = []
        self._script_parts: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        element_id = values.get("id")
        if element_id:
            self.ids.append(element_id)
        if tag == "img" and values.get("src"):
            self.local_assets.append(values["src"] or "")
        if tag == "script":
            src = values.get("src")
            if src and not src.startswith(("http://", "https://", "//")):
                self.local_assets.append(src)
            self._script_parts = [] if not src else None

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._script_parts is not None:
            self.scripts.append("".join(self._script_parts))
            self._script_parts = None

    def handle_data(self, data: str) -> None:
        if self._script_parts is not None:
            self._script_parts.append(data)


def main() -> None:
    parser = AppParser()
    source = HTML.read_text(encoding="utf-8")
    parser.feed(source)
    duplicates = sorted({item for item in parser.ids if parser.ids.count(item) > 1})
    missing = sorted(REQUIRED_IDS - set(parser.ids))
    if missing:
        raise SystemExit(f"Missing required app elements: {', '.join(missing)}")
    if duplicates:
        raise SystemExit(f"Duplicate element IDs: {', '.join(duplicates)}")
    if not parser.scripts or not any("requestAnimationFrame" in script for script in parser.scripts):
        raise SystemExit("The app's inline simulation script was not found")

    parser.local_assets.extend(re.findall(r"\.src\s*=\s*['\"]([^'\"]+)['\"]", source))
    for asset in sorted(set(parser.local_assets)):
        path = (ROOT / asset).resolve()
        if ROOT not in path.parents or not path.is_file():
            raise SystemExit(f"Missing or unsafe local app asset: {asset}")
        if path.suffix.lower() == ".png" and not path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
            raise SystemExit(f"Invalid PNG app asset: {asset}")

    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8") as script_file:
        script_file.write("\n".join(parser.scripts))
        script_file.flush()
        subprocess.run(["node", "--check", script_file.name], check=True)
    print(f"Valid browser app: {HTML.name} | {len(parser.ids)} elements | {len(parser.local_assets)} local assets")


if __name__ == "__main__":
    main()
