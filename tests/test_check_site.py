import importlib.util
from pathlib import Path
import unittest


CHECKER_PATH = Path(".github/scripts/check_site.py")
spec = importlib.util.spec_from_file_location("check_site", CHECKER_PATH)
check_site = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_site)


class PortfolioQualityTests(unittest.TestCase):
    def test_current_portfolio_passes_all_checks(self):
        html = Path("index.html").read_text(encoding="utf-8")
        failed = [name for name, passed in check_site.validate_html(html).items() if not passed]
        self.assertEqual(failed, [], f"Portfolio checks failed: {failed}")

    def test_rejects_inline_script(self):
        html = Path("index.html").read_text(encoding="utf-8").replace(
            "</body>", "<script>alert(1)</script></body>"
        )
        self.assertFalse(check_site.validate_html(html)["no executable scripts"])

    def test_rejects_broken_internal_anchor(self):
        html = Path("index.html").read_text(encoding="utf-8").replace(
            'href="#main"', 'href="#missing-target"', 1
        )
        self.assertFalse(check_site.validate_html(html)["all in-page links resolve"])

    def test_rejects_unsafe_new_tab_link(self):
        html = Path("index.html").read_text(encoding="utf-8").replace(
            'rel="noopener noreferrer"', 'rel="nofollow"', 1
        )
        self.assertFalse(
            check_site.validate_html(html)["new-tab links use noopener and noreferrer"]
        )

    def test_rejects_duplicate_ids(self):
        html = Path("index.html").read_text(encoding="utf-8").replace(
            'id="main"', 'id="top"', 1
        )
        self.assertFalse(check_site.validate_html(html)["unique element IDs"])


if __name__ == "__main__":
    unittest.main()
