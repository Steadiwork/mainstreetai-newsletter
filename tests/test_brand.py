import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bd_brand import brand, NAVY, OR, LOGO

SAMPLE = ('<p><i>Opener.</i></p><h3>DO THIS TODAY: Example task</h3>'
          '<blockquote>Copy-paste prompt<br>line two</blockquote>'
          '<table border="1" cellpadding="4" style="border-collapse:collapse"><tr><th>A</th></tr><tr><td>b</td></tr></table>'
          '<p><a href="https://example.com/">link</a></p>')

class BrandTests(unittest.TestCase):
    def test_header_first_and_logo(self):
        out = brand(SAMPLE)
        self.assertIn(LOGO, out.split("<p")[0])
        self.assertIn(NAVY, out)

    def test_links_orange_bold(self):
        self.assertIn(f'<a style="color:{OR};font-weight:700" href="https://example.com/">', brand(SAMPLE))

    def test_blockquote_becomes_box(self):
        out = brand(SAMPLE)
        self.assertNotIn("<blockquote>", out)
        self.assertIn("Copy-paste prompt", out)

    def test_no_template_tokens_added(self):
        out = brand(SAMPLE)
        for t in ("{{", "{%", "{#"):
            self.assertNotIn(t, out)

if __name__ == "__main__":
    unittest.main()
