from __future__ import annotations

import unittest

from tools.merge_ir import _normalized_type, merge_sources


class MergeIrTests(unittest.TestCase):
    def test_merge_python_cpp_and_docs(self) -> None:
        python_symbols = [
            {
                "id": "adsk.core.Application.get",
                "kind": "method",
                "name": "get",
                "owner": "adsk.core.Application",
                "namespace": "adsk.core",
                "display_name": "Application.get",
                "python_path": "adsk.core.Application.get",
                "parameters": [],
                "return_annotation": "Application",
                "flags": {"staticmethod": True, "classmethod": False, "property": False},
                "source_path": "adsk/core.py",
            },
            {
                "id": "adsk.core.Application",
                "kind": "class",
                "name": "Application",
                "owner": "adsk.core",
                "namespace": "adsk.core",
                "display_name": "Application",
                "python_path": "adsk.core.Application",
                "parameters": [],
                "return_annotation": None,
                "flags": {},
                "source_path": "adsk/core.py",
            },
        ]
        cpp_symbols = [
            {
                "id": "adsk.core.Application.get",
                "kind": "method",
                "name": "get",
                "owner": "adsk.core.Application",
                "namespace": "adsk.core",
                "display_name": "Application.get",
                "cpp_qualified_name": "adsk::core::Application::get",
                "parameters": [],
                "return_type": "core::Ptr<Application>",
                "flags": {"static": True},
                "source_path": "Core/Application/Application.h",
            }
        ]
        cpp_enums = []
        doc_pages = [
            {
                "symbol_id": "adsk.core.Application.get",
                "symbol_key": "Application.get",
                "page_kind": "method",
                "title": "Application.get Method",
                "description": "Access to the root Application object.",
                "parameters": [],
                "return_value": {"Type": "Application", "Description": "Returns the root Application object."},
                "samples": [],
                "version": "August 2014",
                "headings": ["Description", "Return Value", "Version"],
                "related_links": [],
                "header_file": "Core/Application/Application.h",
                "source_path": "Application_get.htm",
            }
        ]

        merged = merge_sources(python_symbols, cpp_symbols, cpp_enums, doc_pages)
        by_id = {symbol["id"]: symbol for symbol in merged["symbols"]}

        self.assertIn("adsk.core.Application.get", by_id)
        symbol = by_id["adsk.core.Application.get"]
        self.assertEqual(symbol["doc"]["introduced_in"], "August 2014")
        self.assertEqual(len(symbol["signatures"]), 2)
        self.assertTrue(symbol["traits"]["is_static_constructor"])
        self.assertEqual(merged["conflicts"], [])

    def test_property_prefers_cpp_getter_over_setter(self) -> None:
        python_symbols = [
            {
                "id": "adsk.cam.Example.value",
                "kind": "property",
                "name": "value",
                "owner": "adsk.cam.Example",
                "namespace": "adsk.cam",
                "display_name": "Example.value",
                "python_path": "adsk.cam.Example.value",
                "parameters": [{"name": "self", "kind": "positional_or_keyword", "annotation": None, "default": None}],
                "return_annotation": "float",
                "flags": {"property": True},
                "source_path": "adsk/cam.py",
            }
        ]
        cpp_symbols = [
            {
                "id": "adsk.cam.Example.value",
                "kind": "method",
                "name": "value",
                "owner": "adsk.cam.Example",
                "namespace": "adsk.cam",
                "display_name": "Example.value",
                "cpp_qualified_name": "adsk::cam::Example::value",
                "parameters": [],
                "return_type": "double",
                "flags": {},
                "source_path": "Cam/Example.h",
            },
            {
                "id": "adsk.cam.Example.value",
                "kind": "method",
                "name": "value",
                "owner": "adsk.cam.Example",
                "namespace": "adsk.cam",
                "display_name": "Example.value",
                "cpp_qualified_name": "adsk::cam::Example::value",
                "parameters": [{"name": "value", "type": "double", "raw": "double value"}],
                "return_type": "bool",
                "flags": {},
                "source_path": "Cam/Example.h",
            },
        ]

        merged = merge_sources(python_symbols, cpp_symbols, [], [])
        symbol = {record["id"]: record for record in merged["symbols"]}["adsk.cam.Example.value"]

        cpp_signatures = [signature for signature in symbol["signatures"] if signature["language"] == "cpp"]
        self.assertEqual(len(cpp_signatures), 1)
        self.assertEqual(cpp_signatures[0]["returns"], "double")
        self.assertEqual(merged["conflicts"], [])

    def test_normalized_type_handles_nested_generic_types(self) -> None:
        self.assertEqual(_normalized_type("std::vector<core::Ptr<URL>>"), "URL")
        self.assertEqual(_normalized_type("list[adsk.core.URL]"), "URL")
        self.assertEqual(_normalized_type("core::Ptr<adsk::fusion::Product>"), "Product")
        self.assertEqual(_normalized_type("str"), "string")
        self.assertEqual(_normalized_type("None"), "void")

    def test_object_type_doc_property_bridge_does_not_report_conflict(self) -> None:
        python_symbols = [
            {
                "id": "adsk.core.Application.objectType",
                "kind": "method",
                "name": "objectType",
                "owner": "adsk.core.Application",
                "namespace": "adsk.core",
                "display_name": "Application.objectType",
                "python_path": "adsk.core.Application.objectType",
                "parameters": [],
                "return_annotation": "str",
                "flags": {"staticmethod": False, "classmethod": False, "property": False},
                "source_path": "adsk/core.py",
            }
        ]
        doc_pages = [
            {
                "symbol_id": "adsk.core.Application.objectType",
                "symbol_key": "Application.objectType",
                "page_kind": "property",
                "title": "Application.objectType Property",
                "description": "Returns the object type string.",
                "parameters": [],
                "return_value": {"Type": "string", "Description": "The object type."},
                "samples": [],
                "version": "August 2014",
                "headings": ["Description", "Return Value", "Version"],
                "related_links": [],
                "header_file": "Core/Application/Application.h",
                "source_path": "Application_objectType.htm",
            }
        ]

        merged = merge_sources(python_symbols, [], [], doc_pages)
        self.assertEqual(merged["conflicts"], [])


if __name__ == "__main__":
    unittest.main()
