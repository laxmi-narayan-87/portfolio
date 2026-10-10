from html.parser import HTMLParser
from pathlib import Path
import re
import sys


class SiteParser(HTMLParser):
    """Collect the small set of HTML facts this static portfolio relies on."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.ids = []
        self.links = []
        self.assets = []
        self.images = []
        self.event_handlers = []
        self.javascript_urls = []
        self.meta = []
        self.mains = []
        self.skip_links = []
        self.scripts = 0
        self.embedded_content = 0
        self.forms = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append((tag, attrs))
        if attrs.get("id"):
            self.ids.append(attrs["id"])
        if tag == "a":
            self.links.append(attrs)
            if "skip" in attrs.get("class", "").split():
                self.skip_links.append(attrs)
            if attrs.get("href", "").strip().lower().startswith("javascript:"):
                self.javascript_urls.append(attrs["href"])
        if tag == "img":
            self.images.append(attrs)
        if tag == "meta":
            self.meta.append(attrs)
        if tag == "main":
            self.mains.append(attrs)
        if tag == "script":
            self.scripts += 1
        if tag in {"iframe", "object", "embed"}:
            self.embedded_content += 1
        if tag == "form":
            self.forms += 1
        if tag == "link":
            rel = set(attrs.get("rel", "").lower().split())
            if rel.intersection({"stylesheet", "preload", "modulepreload", "icon"}):
                self.assets.append(attrs.get("href", ""))
        if tag in {"img", "script", "source", "audio", "video"} and attrs.get("src"):
            self.assets.append(attrs["src"])
        for name in attrs:
            if name.lower().startswith("on"):
                self.event_handlers.append((tag, name))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)


def validate_html(html):
    parser = SiteParser()
    parser.feed(html)
    parser.close()

    csp_match = re.search(
        r'<meta\\s+[^>]*http-equiv=["\\']Content-Security-Policy["\\'][^>]*content=["\\']([^"\\']+)["\\']',
        html,
        re.IGNORECASE,
    )
    # The page currently places http-equiv before content. This fallback also
    # handles the reverse attribute order without relying on attribute order.
    csp = ""
    for item in parser.meta:
        if item.get("http-equiv", "").lower() == "content-security-policy":
            csp = item.get("content", "")
            break
    directives = {}
    for directive in csp.split(";"):
        parts = directive.strip().split()
        if parts:
            directives[parts[0].lower()] = parts[1:]

    ids_are_unique = len(parser.ids) == len(set(parser.ids))
    known_ids = set(parser.ids)
    broken_anchors = [
        link.get("href", "")
        for link in parser.links
        if link.get("href", "").startswith("#")
        and link.get("href", "")[1:] not in known_ids
    ]
    unsafe_blank_links = [
        link.get("href", "")
        for link in parser.links
        if link.get("target", "").lower() == "_blank"
        and not {"noopener", "noreferrer"}.issubset(
            set(link.get("rel", "").lower().split())
        )
    ]
    remote_assets = [
        asset for asset in parser.assets
        if asset.strip().lower().startswith(("http://", "https://", "//"))
    ]
    local_path_pattern = re.compile(
        r"(?:[A-Za-z]:\\\\(?:Users|Documents and Settings)\\\\|/Users/)",
        re.IGNORECASE,
    )
    remote_css_import = re.search(
        r"@import\\s+(?:url\\()?\\s*['\\"]?(?:https?:)?//",
        html,
        re.IGNORECASE,
    )
    inline_style_remote_url = re.search(
        r"url\\(\\s*['\\"]?(?:https?:)?//",
        html,
        re.IGNORECASE,
    )

    return {
        "HTML5 doctype": html.lstrip().lower().startswith("<!doctype html>"),
        "English document language": bool(re.search(r"<html\\b[^>]*\\blang=['\\"]en['\\"]", html, re.I)),
        "responsive viewport": any(m.get("name", "").lower() == "viewport" for m in parser.meta),
        "description metadata": any(m.get("name", "").lower() == "description" and m.get("content", "").strip() for m in parser.meta),
        "restrictive CSP meta policy": bool(csp)
            and directives.get("default-src") == ["'self'"]
            and directives.get("script-src") == ["'none'"]
            and directives.get("object-src") == ["'none'"]
            and directives.get("base-uri") == ["'none'"]
            and directives.get("form-action") == ["'self'"]
            and directives.get("connect-src") == ["'self'"]
            and "upgrade-insecure-requests" in directives,
        "no executable scripts": parser.scripts == 0 and directives.get("script-src") == ["'none'"],
        "no embedded browsing/plugin content": parser.embedded_content == 0 and directives.get("object-src") == ["'none'"],
        "no inline event handlers": not parser.event_handlers,
        "no javascript URLs": not parser.javascript_urls,
        "no external asset dependencies": not remote_assets and not remote_css_import and not inline_style_remote_url,
        "no legacy local file paths": not local_path_pattern.search(html),
        "no placeholder lorem ipsum": "lorem ipsum" not in html.lower(),
        "exactly one main landmark": len(parser.mains) == 1 and parser.mains[0].get("id") == "main",
        "skip link targets main": any(link.get("href") == "#main" for link in parser.skip_links) and "main" in known_ids,
        "reduced-motion support": "prefers-reduced-motion:reduce" in html,
        "quality/security section": bool(re.search(r'<section\\b[^>]*\\bid=["\\']quality["\\']', html)),
        "contact email link": 'href="mailto:laxminarayan955459@gmail.com"' in html,
        "unique element IDs": ids_are_unique,
        "all in-page links resolve": not broken_anchors,
        "new-tab links use noopener and noreferrer": not unsafe_blank_links,
        "all images have alt attributes": all("alt" in img for img in parser.images),
        "no unnecessary contact forms": parser.forms == 0,
    }


def main():
    page = Path("index.html")
    if not page.is_file():
        sys.exit("FAIL: index.html is missing")

    checks = validate_html(page.read_text(encoding="utf-8"))
    failed = [name for name, passed in checks.items() if not passed]
    for name, passed in checks.items():
        print(f'{"PASS" if passed else "FAIL"}: {name}')
    if failed:
        sys.exit(f"{len(failed)} check(s) failed: {', '.join(failed)}")


if __name__ == "__main__":
    main()
