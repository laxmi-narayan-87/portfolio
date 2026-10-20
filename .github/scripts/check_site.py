from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(".")
BASE_URL = "https://laxmi-narayan-87.github.io/portfolio/"
HOME = ROOT / "index.html"
SITEMAP = ROOT / "sitemap.xml"

if not HOME.is_file():
    sys.exit("FAIL: index.html is missing")

html = HOME.read_text(encoding="utf-8")
checks = {
    "HTML5 doctype": html.lstrip().lower().startswith("<!doctype html>"),
    "language attribute": '<html lang="en">' in html,
    "responsive viewport": 'name="viewport"' in html,
    "page title": bool(re.search(r"<title>[^<]{10,}</title>", html, re.I)),
    "description metadata": bool(re.search(r'<meta name="description" content="[^"]{40,}"', html)),
    "robots allow indexing": 'name="robots" content="index, follow"' in html,
    "canonical URL": f'<link rel="canonical" href="{BASE_URL}">' in html,
    "Open Graph title": 'property="og:title"' in html,
    "Open Graph description": 'property="og:description"' in html,
    "Twitter card metadata": 'name="twitter:card"' in html,
    "CSP meta policy": 'http-equiv="Content-Security-Policy"' in html,
    "scripts disabled by default": "script-src 'none'" in html,
    "objects disabled": "object-src 'none'" in html,
    "no legacy local Windows paths": not re.search(r"[A-Za-z]:\\Users\\", html),
    "no lorem ipsum placeholder": "lorem ipsum" not in html.lower(),
    "main landmark": '<main id="main">' in html,
    "skip link": 'class="skip" href="#main"' in html,
    "reduced-motion support": "prefers-reduced-motion:reduce" in html,
    "quality/security section": 'id="quality"' in html,
    "contact email link": 'href="mailto:laxminarayan955459@gmail.com"' in html,
    "DarkSense links to its actual source": 'href="https://github.com/laxmi-narayan-87/CL-PORT/tree/main/darksense"' in html,
    "LeetCode generic homepage link removed": 'href="https://leetcode.com/"' not in html,
}

placeholder_phrases = (
    "Evidence to publish",
    "Evidence to explore",
    "Add individual certificates and verified outcomes",
    "Use this section for verified achievements",
    "Link to a public profile and keep counts current",
)
for phrase in placeholder_phrases:
    checks[f"no editorial placeholder: {phrase}"] = phrase.lower() not in html.lower()

required_pages = [
    "projects/darksense-ai/index.html",
    "projects/skillforge-academy/index.html",
    "projects/agrovalue/index.html",
    "projects/q-learning-frozenlake/index.html",
    "projects/qa-automation/index.html",
]
for page in required_pages:
    checks[f"case study exists: {page}"] = (ROOT / page).is_file()

try:
    tree = ET.parse(SITEMAP)
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locs = [node.text for node in tree.findall(".//sm:loc", ns)]
    checks["sitemap XML is well formed"] = True
    checks["sitemap includes canonical homepage"] = BASE_URL in locs
    checks["sitemap includes every case study"] = all(
        BASE_URL + page.removesuffix("index.html") in locs
        for page in required_pages
    )
    checks["sitemap URLs are HTTPS and on canonical host"] = all(
        url and url.startswith(BASE_URL) and url.startswith("https://")
        for url in locs
    )
    checks["sitemap has no duplicate URLs"] = len(locs) == len(set(locs))
except (ET.ParseError, OSError) as exc:
    checks["sitemap XML is well formed"] = False
    print(f"Could not parse sitemap: {exc}")

failed = [name for name, passed in checks.items() if not passed]
for name, passed in checks.items():
    print(f'{"PASS" if passed else "FAIL"}: {name}')
if failed:
    sys.exit(f"{len(failed)} check(s) failed: {', '.join(failed)}")
