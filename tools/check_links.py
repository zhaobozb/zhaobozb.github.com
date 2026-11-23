"""Fail if the published site links to a local file that does not exist.

Checks every HTML and CSS file under the site directory for local references
(href/src attributes, CSS url(), and absolute links to this site's own domain)
and verifies each target exists. Standard library only, so it runs on any CI runner.

Usage:
    python3 tools/check_links.py [site_dir]    # default: site
"""
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

OWN_HOSTS = {"www.zhaobo.me", "zhaobo.me"}


class RefParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if not value:
                continue
            if name in ("href", "src"):
                self.refs.append(value)
            # Social-preview images, e.g. <meta property="og:image" content="https://www.zhaobo.me/...">
            elif name == "content" and value.startswith(("http://", "https://")):
                self.refs.append(value)


def local_target(ref: str, page: Path, site: Path):
    """Return the file a reference points to, or None if it is external/not a file."""
    if ref.startswith(("mailto:", "tel:", "data:", "javascript:", "#")):
        return None
    parts = urlsplit(ref)
    if parts.scheme in ("http", "https") or ref.startswith("//"):
        if parts.netloc not in OWN_HOSTS:
            return None
        path = parts.path.lstrip("/")
        base = site
    else:
        path = parts.path
        base = site if path.startswith("/") else page.parent
        path = path.lstrip("/")
    path = unquote(path)
    target = (base / path) if path else base
    return target / "index.html" if (not path or path.endswith("/")) else target


def main() -> int:
    site = Path(sys.argv[1] if len(sys.argv) > 1 else "site").resolve()
    if not site.is_dir():
        print(f"error: site directory not found: {site}")
        return 2
    missing, checked = [], 0
    for page in sorted(site.rglob("*")):
        if page.suffix == ".html":
            parser = RefParser()
            parser.feed(page.read_text(encoding="utf-8"))
            refs = parser.refs
        elif page.suffix == ".css":
            refs = re.findall(r"url\(\s*['\"]?([^)'\"]+)", page.read_text(encoding="utf-8"))
        else:
            continue
        for ref in refs:
            target = local_target(ref.strip(), page, site)
            if target is None:
                continue
            checked += 1
            if not target.exists():
                missing.append(f"{page.relative_to(site)}: {ref}")
    for m in missing:
        print(f"missing: {m}")
    print(f"checked {checked} local references, {len(missing)} missing")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
