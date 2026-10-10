from html.parser import HTMLParser
from pathlib import Path
import sys


class SiteParser(HTMLParser):
    """Collect the HTML facts this static portfolio relies on."""

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

    meta_by_name = {
        item.get("name", "").lower(): item
        for item in parser.meta
        if item.get("name")
    }
    csp = next(
        (
            item.get("content", "")
            for item in parser.meta
            if item.get("http-equiv", "").lower() == "content-security-policy"
        ),
        "",
    )
    directives = {}
    for directive in csp.split(";"):
        parts = directive.strip().split()
        if parts:
            directives[parts[0].lower()] = parts[1:]

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
    backslash = chr(92)
    local_windows_path = any(
        f"{drive}:{backslash}Users{backslash}" in html
        or f"{drive}:{backslash}Documents and Settings{backslash}" in html
        for drive in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    )
    lower_html = html.lower()
    remote_css_import = False
    if "@import" in lower_html:
        for statement in lower_html.split("@import")[1:]:
            fragment = statement.split(";", 1)[0]
            if "http://" in fragment or "https://" in fragment or "url(//" in fragment:
                remote_css_import = True
                break
    remote_css_url = any(
        marker in lower_html
        for marker in ('url("http://', 'url("https://', "url('http://", "url('https://",
                       "url(http://", "url(https://", 'url("//', "url('//", "url(//")
    )
    html_attrs = next((attrs for tag, attrs in parser.tags if tag == "html"), {})
    has_quality_section = any(
        tag == "section" and attrs.get("id") == "quality"
        for tag, attrs in parser.tags
    )

    return {
        "HTML5 doctype": html.lstrip().lower().startswith("<!doctype html>"),
        "English document language": html_attrs.get("lang", "").lower() == "en",
        "responsive viewport": "viewport" in meta_by_name,
        "description metadata": bool(meta_by_name.get("description", {}).get("content", "").strip()),
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
        "no external asset dependencies": not remote_assets and not remote_css_import and not remote_css_url,
        "no legacy local file paths": not local_windows_path and "/Users/" not in html,
        "no placeholder lorem ipsum": "lorem ipsum" not in lower_html,
        "exactly one main landmark": len(parser.mains) == 1 and parser.mains[0].get("id") == "main",
        "skip link targets main": any(link.get("href") == "#main" for link in parser.skip_links) and "main" in known_ids,
        "reduced-motion support": "prefers-reduced-motion:reduce" in lower_html,
        "quality/security section": has_quality_section,
        "contact email link": 'href="mailto:laxminarayan955459@gmail.com"' in html,
        "unique element IDs": len(parser.ids) == len(set(parser.ids)),
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
