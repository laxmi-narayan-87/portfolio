from pathlib import Path
import re
import sys

page = Path("index.html")
if not page.is_file():
    sys.exit("FAIL: index.html is missing")

html = page.read_text(encoding="utf-8")
checks = {
    "HTML5 doctype": html.lstrip().lower().startswith("<!doctype html>"),
    "language attribute": '<html lang="en">' in html,
    "responsive viewport": 'name="viewport"' in html,
    "description metadata": 'name="description"' in html,
    "CSP meta policy": 'http-equiv="Content-Security-Policy"' in html,
    "scripts disabled by default": "script-src 'none'" in html,
    "objects disabled": "object-src 'none'" in html,
    "no legacy local Windows paths": not re.search(r"[A-Za-z]:\\Users\\", html),
    "no placeholder lorem ipsum": "lorem ipsum" not in html.lower(),
    "main landmark": '<main id="main">' in html,
    "skip link": 'class="skip" href="#main"' in html,
    "reduced-motion support": "prefers-reduced-motion:reduce" in html,
    "quality/security section": 'id="quality"' in html,
    "contact email link": 'href="mailto:laxminarayan955459@gmail.com"' in html,
}
failed = [name for name, passed in checks.items() if not passed]
for name, passed in checks.items():
    print(f'{"PASS" if passed else "FAIL"}: {name}')
if failed:
    sys.exit(f"{len(failed)} check(s) failed: {', '.join(failed)}")
