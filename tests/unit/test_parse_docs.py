from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from tools.parse_docs import parse_doc_page, parse_docs


METHOD_HTML = """
<html>
  <head>
    <meta name="contextid" content="Application_get">
    <title>Application.get Method</title>
  </head>
  <body>
    <h1 class="api">Application.get Method</h1>
    Parent Object: <a href="Application.htm">Application</a><br>Defined in namespace "adsk::core" and the header file is &lt;Core/Application/Application.h&gt;
    <h2 class="api">Description</h2>
    <p class="api">Access to the root Application object.</p>
    <h2 class="api">Parameters</h2>
    <Table class="api-list">
      <tr class="header"><td>Name</td><td>Type</td><td>Description</td></tr>
      <tr><td>flag</td><td>boolean</td><td>A test parameter.</td></tr>
    </Table>
    <h2 class="api">Return Value</h2>
    <Table class="api-list">
      <tr class="header"><td>Type</td><td>Description</td></tr>
      <tr><td><a href="Application.htm">Application</a></td><td>Return the root Application object.</td></tr>
    </Table>
    <h2 class="api">Samples</h2>
    <Table class="api-list">
      <tr class="header"><td>Name</td><td>Description</td></tr>
      <tr><td><a href="Example_Sample.htm">Example Sample</a></td><td>Shows something.</td></tr>
    </Table>
    <h2 class="api">Version</h2>
    Introduced in version August 2014
  </body>
</html>
"""


SAMPLE_HTML = """
<html>
  <head>
    <title>Extrude Feature API Sample</title>
  </head>
  <body>
    <h1 class="api">Extrude Feature API Sample</h1>
    <h2 class="api">Description</h2>
    Demonstrates creating a new extrude feature.
    <h2 class="api">Code Samples</h2>
    <div id="tabs">
      <div id="Python" class="api-code">
        <pre class="api-code" id="Python_code">import adsk.core\n\ndef run(context):\n    return 1\n</pre>
      </div>
    </div>
  </body>
</html>
"""


class ParseDocsTests(unittest.TestCase):
    def test_parse_method_page_and_symbol_link(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            file_path = root / "Application_get.htm"
            file_path.write_text(METHOD_HTML, encoding="utf-8")

            page = parse_doc_page(file_path, root)

            self.assertEqual(page["page_kind"], "method")
            self.assertEqual(page["symbol_key"], "Application.get")
            self.assertEqual(page["symbol_id"], "adsk.core.Application.get")
            self.assertEqual(page["namespace"], "adsk::core")
            self.assertEqual(page["header_file"], "Core/Application/Application.h")
            self.assertEqual(page["parameters"][0]["Name"], "flag")
            self.assertEqual(page["return_value"]["Type"], "Application")
            self.assertEqual(page["samples"][0]["file_stem"], "Example_Sample")
            self.assertEqual(page["version"], "August 2014")

    def test_parse_sample_page_code_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "ExtrudeFeatureSample_Sample.htm").write_text(SAMPLE_HTML, encoding="utf-8")

            parsed = parse_docs(root)

            self.assertEqual(len(parsed["pages"]), 1)
            page = parsed["pages"][0]
            self.assertEqual(page["page_kind"], "sample")
            self.assertIsNone(page["symbol_id"])
            self.assertEqual(page["code_blocks"][0]["language_hint"], "Python")
            self.assertIn("def run(context):", page["code_blocks"][0]["content"])
            self.assertEqual(parsed["symbol_links"], [])


if __name__ == "__main__":
    unittest.main()
