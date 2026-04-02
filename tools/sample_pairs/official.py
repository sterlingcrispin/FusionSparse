from __future__ import annotations

import ast
from pathlib import Path

from tools.parse_docs import parse_doc_page

from .errors import SampleConversionError


def resolve_official_script(root: Path, docs_root: Path, official_dir: Path, pair: dict[str, object]) -> Path:
    official_script = pair.get("official_script")
    if isinstance(official_script, str) and official_script:
        return root / official_script

    generation = pair["official_generation"]
    path = official_dir / f"{pair['id']}.py"
    path.write_text(generate_official_from_doc(docs_root, pair["source_page"], generation), encoding="utf-8")
    return path


def generate_official_from_doc(docs_root: Path, source_page: str, generation: dict[str, object]) -> str:
    page = parse_doc_page(docs_root / source_page, docs_root)
    block = next((item for item in page.get("code_blocks", []) if item.get("language_hint") == "Python"), None)
    if block is None:
        raise SampleConversionError(f"No Python code block found in sample page: {source_page}")
    content = str(block["content"]).strip() + "\n"
    mode = generation["mode"]
    if mode == "doc_run":
        return wrap_doc_run_script(content)
    if mode == "doc_demo_sketch":
        return wrap_doc_demo_sketch(content)
    raise SampleConversionError(f"Unsupported official generation mode: {mode}")


def wrap_doc_run_script(content: str) -> str:
    module = ast.parse(content)
    if not any(
        isinstance(node, ast.ImportFrom) and node.module == "tests.integration.sample_pairs.common"
        for node in module.body
    ):
        module.body.insert(
            0,
            ast.ImportFrom(
                module="tests.integration.sample_pairs.common",
                names=[ast.alias(name="print_design_signature")],
                level=0,
            ),
        )
    run_fn = next((node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == "run"), None)
    if run_fn is None:
        raise SampleConversionError("doc_run sample must define run(context).")
    target_body = run_fn.body
    for statement in run_fn.body:
        if isinstance(statement, ast.Try):
            target_body = statement.body
            break
    target_body.append(
        ast.Expr(
            ast.Call(
                func=ast.Name(id="print_design_signature", ctx=ast.Load()),
                args=[ast.Name(id="design", ctx=ast.Load())],
                keywords=[],
            )
        )
    )
    module = ast.fix_missing_locations(module)
    return ast.unparse(module) + "\n"


def wrap_doc_demo_sketch(content: str) -> str:
    module = ast.parse(content)
    demo_fn = next((node for node in module.body if isinstance(node, ast.FunctionDef)), None)
    if demo_fn is None:
        raise SampleConversionError("Generated sketch demo sample must define a function.")
    run_body: list[ast.stmt] = [
        ast.Assign(
            targets=[ast.Name(id="app", ctx=ast.Store())],
            value=ast.Call(
                func=ast.Attribute(
                    value=ast.Attribute(value=ast.Name(id="adsk", ctx=ast.Load()), attr="core", ctx=ast.Load()),
                    attr="Application",
                    ctx=ast.Load(),
                ),
                args=[],
                keywords=[],
            ),
        ),
    ]
    run_body[0].value = ast.Call(
        func=ast.Attribute(value=run_body[0].value.func, attr="get", ctx=ast.Load()),
        args=[],
        keywords=[],
    )
    run_body.extend(
        [
            ast.Expr(
                ast.Call(
                    func=ast.Attribute(
                        value=ast.Attribute(
                            value=ast.Name(id="app", ctx=ast.Load()),
                            attr="documents",
                            ctx=ast.Load(),
                        ),
                        attr="add",
                        ctx=ast.Load(),
                    ),
                    args=[
                        ast.Attribute(
                            value=ast.Attribute(
                                value=ast.Attribute(
                                    value=ast.Name(id="adsk", ctx=ast.Load()),
                                    attr="core",
                                    ctx=ast.Load(),
                                ),
                                attr="DocumentTypes",
                                ctx=ast.Load(),
                            ),
                            attr="FusionDesignDocumentType",
                            ctx=ast.Load(),
                        )
                    ],
                    keywords=[],
                )
            ),
            ast.Assign(
                targets=[ast.Name(id="design", ctx=ast.Store())],
                value=ast.Call(
                    func=ast.Attribute(
                        value=ast.Attribute(
                            value=ast.Attribute(
                                value=ast.Name(id="adsk", ctx=ast.Load()),
                                attr="fusion",
                                ctx=ast.Load(),
                            ),
                            attr="Design",
                            ctx=ast.Load(),
                        ),
                        attr="cast",
                        ctx=ast.Load(),
                    ),
                    args=[ast.Attribute(value=ast.Name(id="app", ctx=ast.Load()), attr="activeProduct", ctx=ast.Load())],
                    keywords=[],
                ),
            ),
            ast.Assign(
                targets=[ast.Name(id="root_comp", ctx=ast.Store())],
                value=ast.Attribute(value=ast.Name(id="design", ctx=ast.Load()), attr="rootComponent", ctx=ast.Load()),
            ),
            ast.Assign(
                targets=[ast.Name(id="sketch", ctx=ast.Store())],
                value=ast.Call(
                    func=ast.Attribute(
                        value=ast.Attribute(value=ast.Name(id="root_comp", ctx=ast.Load()), attr="sketches", ctx=ast.Load()),
                        attr="add",
                        ctx=ast.Load(),
                    ),
                    args=[
                        ast.Attribute(
                            value=ast.Name(id="root_comp", ctx=ast.Load()),
                            attr="xYConstructionPlane",
                            ctx=ast.Load(),
                        )
                    ],
                    keywords=[],
                ),
            ),
        ]
    )
    run_body.extend(demo_fn.body)
    run_body.append(
        ast.Expr(
            ast.Call(
                func=ast.Name(id="print_design_signature", ctx=ast.Load()),
                args=[ast.Name(id="design", ctx=ast.Load())],
                keywords=[],
            )
        )
    )
    wrapped = ast.Module(
        body=[
            ast.Import(names=[ast.alias(name="adsk.core"), ast.alias(name="adsk.fusion")]),
            ast.ImportFrom(
                module="tests.integration.sample_pairs.common",
                names=[ast.alias(name="print_design_signature")],
                level=0,
            ),
            ast.FunctionDef(
                name="run",
                args=ast.arguments(
                    posonlyargs=[],
                    args=[ast.arg(arg="context")],
                    kwonlyargs=[],
                    kw_defaults=[],
                    defaults=[],
                ),
                body=run_body,
                decorator_list=[],
            ),
        ],
        type_ignores=[],
    )
    wrapped = ast.fix_missing_locations(wrapped)
    return ast.unparse(wrapped) + "\n"
