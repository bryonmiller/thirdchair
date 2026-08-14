"""Check that the plain static site is self-contained and provider-neutral."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


class LinkCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag not in {"a", "link"}:
            return
        values = dict(attrs)
        attribute = "href"
        if values.get(attribute):
            self.links.append(str(values[attribute]))


def main() -> None:
    index = SITE / "index.html"
    source = index.read_text(encoding="utf-8")
    for required in (
        "The Third Chair",
        "Bryon Miller",
        "The board is empty until real models take the seats",
        "This walkthrough explains the protocol. It is not a model run",
    ):
        if required not in source:
            raise AssertionError(f"Static site is missing required copy: {required}")

    parser = LinkCollector()
    parser.feed(source)
    missing: list[str] = []
    for link in parser.links:
        parsed = urlparse(link)
        if parsed.scheme or parsed.netloc or link.startswith("#"):
            continue
        target = SITE / parsed.path
        if not target.exists():
            missing.append(link)
    if missing:
        raise AssertionError(f"Static site has missing local links: {', '.join(missing)}")
    print(f"Static site validation passed for {len(parser.links)} links")


if __name__ == "__main__":
    main()
