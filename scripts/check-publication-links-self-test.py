#!/usr/bin/env python3
"""Hostile-fixture tests for the staged publication-link portability gate."""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import tempfile
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn

import pypdf
from pypdf import PdfWriter
from pypdf.generic import (
    ArrayObject,
    BooleanObject,
    DecodedStreamObject,
    DictionaryObject,
    NameObject,
    NullObject,
    NumberObject,
    TextStringObject,
)

EXPECTED_PYPDF_VERSION = "6.15.0"
ROOT = Path(__file__).resolve(strict=True).parent.parent
CHECKER = ROOT / "scripts/check-publication-links.py"
CHECK_NAME = "publication link portability self-test"
Mutation = Callable[[Path], None]


@dataclass(frozen=True)
class Hostile:
    name: str
    mutate: Mutation
    diagnostics: tuple[str, ...]


def fail(message: str) -> NoReturn:
    raise SystemExit(f"{CHECK_NAME}: FAILED: {message}")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def git(repo: Path, args: Sequence[str], *, input_text: str | None = None) -> str:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(
        {
            "GIT_ATTR_NOSYSTEM": "1",
            "GIT_CONFIG_COUNT": "0",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_LITERAL_PATHSPECS": "1",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_OPTIONAL_LOCKS": "0",
        }
    )
    result = subprocess.run(
        ["/usr/bin/git", "--no-replace-objects", "-c", "core.quotepath=false", *args],
        cwd=repo,
        env=env,
        input=input_text,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=20,
        check=False,
    )
    if result.returncode:
        fail(f"git {' '.join(args)!r} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def add(repo: Path, *paths: str) -> None:
    git(repo, ["add", "--", *paths])


def action(name: str, **values: object) -> DictionaryObject:
    value = DictionaryObject(
        {NameObject("/Type"): NameObject("/Action"), NameObject("/S"): NameObject(name)}
    )
    for key, item in values.items():
        value[NameObject("/" + key)] = item
    return value


def stream_dictionary(values: DictionaryObject) -> DecodedStreamObject:
    """Return a stream carrying dictionary keys that a typed slot must reject."""

    stream = DecodedStreamObject()
    stream.set_data(b"")
    for key, value in values.items():
        stream[key] = value
    return stream


def destination(reference: object) -> ArrayObject:
    return ArrayObject([reference, NameObject("/Fit")])


def write_pdf(
    path: Path,
    configure: Callable[[PdfWriter, object], None] | None = None,
    *,
    baseline: bool = False,
    encrypt: bool = False,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    writer = PdfWriter()
    page = writer.add_blank_page(width=144, height=144)
    reference = page.indirect_reference
    if reference is None:
        fail("pypdf did not allocate a page reference")
    if baseline:
        writer.add_named_destination("named-start", 0)
        writer.root_object[NameObject("/OpenAction")] = TextStringObject("named-start")
        uri = action("/URI", URI=TextStringObject("https://example.com/reference"))
        go = action("/GoTo", D=destination(reference), Next=uri)
        writer.root_object[NameObject("/AA")] = DictionaryObject(
            {NameObject("/WC"): go}
        )
        writer.root_object[NameObject("/FixtureDest")] = DictionaryObject(
            {NameObject("/Dest"): destination(reference)}
        )
    if configure:
        configure(writer, reference)
    if encrypt:
        writer.encrypt("secret")
    with path.open("wb") as stream:
        writer.write(stream)


BASE = """# Publication fixture

[Unicode](target.md#überblick)
[Duplicate heading](target.md#repeat-1)
[Multiline GFM
link](docs/guide.md#api-code)
[Blob](https://github.com/sepahead/pid-rs/blob/main/docs/guide.md#api-code)
[Tree](https://github.com/sepahead/pid-rs/tree/main/docs)
[Raw](https://raw.githubusercontent.com/sepahead/pid-rs/main/docs/data.txt)
[External GitHub dot path](https://github.com/other/project/blob/main/a/../b)

`[code](missing-code.md)` and \\[escaped](missing-escaped.md) and foo] are not links.
"""
TARGET = """Überblick
=========

## API `code`
## Repeat
## Repeat
"""
ROOT_PUBLICATION_PDF = "PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.pdf"


def configure_root_publication_navigation(
    writer: PdfWriter, _reference: object
) -> None:
    writer.root_object[NameObject("/A")] = action(
        "/URI",
        URI=TextStringObject(
            "https://github.com/sepahead/pid-rs/blob/main/claims/status.md#current-status"
        ),
    )


def initialize(repo: Path) -> None:
    repo.mkdir(parents=True)
    git(repo, ["init", "--quiet"])
    write_text(repo / "README.md", BASE)
    write_text(repo / "target.md", TARGET)
    write_text(repo / "docs/guide.md", "# API `code`\n")
    write_text(repo / "docs/data.txt", "fixture\n")
    write_text(repo / "claims/status.md", "# Current status\n")
    write_pdf(repo / "output/pdf/guide.pdf", baseline=True)
    write_pdf(
        repo / ROOT_PUBLICATION_PDF,
        configure_root_publication_navigation,
        baseline=True,
    )
    add(
        repo,
        "README.md",
        "target.md",
        "docs/guide.md",
        "docs/data.txt",
        "claims/status.md",
        "output/pdf/guide.pdf",
        ROOT_PUBLICATION_PDF,
    )


def run(repo: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update({"PYTHONDONTWRITEBYTECODE": "1", "PYTHONHASHSEED": "0"})
    command = [sys.executable]
    if sys.flags.optimize:
        command.append("-" + "O" * sys.flags.optimize)
    command.append(str(CHECKER))
    return subprocess.run(
        command,
        cwd=repo,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=40,
        check=False,
    )


def success(repo: Path, label: str) -> None:
    result = run(repo)
    if result.returncode or "OK: publication links are portable" not in result.stdout:
        fail(
            f"{label} failed: {result.returncode}; {result.stdout!r}; {result.stderr!r}"
        )


def rejection(repo: Path, case: Hostile) -> None:
    result = run(repo)
    if (
        result.returncode != 1
        or "publication link portability check: FAILED" not in result.stderr
    ):
        fail(f"{case.name} did not fail closed: {result.returncode}; {result.stderr!r}")
    if not all(part in result.stderr for part in case.diagnostics):
        fail(f"{case.name} lacked {case.diagnostics!r}: {result.stderr!r}")


def readme(repo: Path, text: str, stage: bool = True) -> None:
    write_text(repo / "README.md", text)
    if stage:
        add(repo, "README.md")


def target(value: str, html: bool = False) -> Mutation:
    return lambda repo: readme(
        repo,
        "# Hostile\n\n"
        + (f'<a href="{value}">x</a>' if html else f"[x]({value})")
        + "\n",
    )


def autolink(value: str) -> Mutation:
    return lambda repo: readme(repo, f"# Hostile\n\n<{value}>\n")


def staged_bad(repo: Path) -> None:
    readme(repo, "# Staged\n\n[x](missing.md)\n")
    write_text(repo / "README.md", BASE)


def divergent(repo: Path) -> None:
    write_text(repo / "README.md", BASE + "\nchanged\n")


def ita(text: str) -> Mutation:
    def mutate(repo: Path) -> None:
        write_text(repo / "intent.md", text)
        git(repo, ["add", "--intent-to-add", "--", "intent.md"])

    return mutate


def hidden_ita(flag: str) -> Mutation:
    def mutate(repo: Path) -> None:
        readme(repo, "# Hostile\n\n[vanishing target](intent.md)\n")
        write_text(repo / "intent.md", "")
        git(repo, ["add", "--intent-to-add", "--", "intent.md"])
        git(repo, ["update-index", flag, "--", "intent.md"])

    return mutate


def unmerged(repo: Path) -> None:
    blob = git(repo, ["hash-object", "-w", "--stdin"], input_text="# conflict\n")
    git(
        repo,
        ["update-index", "--index-info"],
        input_text=f"100644 {blob} 1\tconflict.md\n100644 {blob} 2\tconflict.md\n",
    )


def symlink(repo: Path) -> None:
    (repo / "linked.md").symlink_to("target.md")
    add(repo, "linked.md")


def gitlink(repo: Path) -> None:
    tree = git(repo, ["mktree"], input_text="")
    # The isolated fixture has no ambient Git identity.  Bind one only for the
    # synthetic commit instead of configuring the runner or weakening isolation.
    commit = git(
        repo,
        [
            "-c",
            "user.name=pid-rs publication fixture",
            "-c",
            "user.email=publication-fixture@example.invalid",
            "commit-tree",
            tree,
        ],
        input_text="fixture\n",
    )
    git(repo, ["update-index", "--add", "--cacheinfo", "160000", commit, "nested"])


def extra(name: str) -> Mutation:
    return lambda repo: write_pdf(repo / f"output/pdf/{name}", baseline=True)


def malformed(repo: Path) -> None:
    (repo / "output/pdf/guide.pdf").write_bytes(b"%PDF-1.7\ninvalid\n")
    add(repo, "output/pdf/guide.pdf")


def encrypted(repo: Path) -> None:
    write_pdf(repo / "output/pdf/guide.pdf", encrypt=True)
    add(repo, "output/pdf/guide.pdf")


def pdf(config: Callable[[PdfWriter, object], None]) -> Mutation:
    def mutate(repo: Path) -> None:
        write_pdf(repo / "output/pdf/guide.pdf", config)
        add(repo, "output/pdf/guide.pdf")

    return mutate


def root_publication_pdf(config: Callable[[PdfWriter, object], None]) -> Mutation:
    def mutate(repo: Path) -> None:
        write_pdf(repo / ROOT_PUBLICATION_PDF, config, baseline=True)
        add(repo, ROOT_PUBLICATION_PDF)

    return mutate


def root_publication_unindexed(repo: Path) -> None:
    git(repo, ["rm", "--cached", "--", ROOT_PUBLICATION_PDF])


def root_publication_relative_uri(repo: Path) -> None:
    root_publication_pdf(
        lambda writer, _reference: writer.root_object.__setitem__(
            NameObject("/A"),
            action("/URI", URI=TextStringObject("claims/status.md#current-status")),
        )
    )(repo)


def root_item(key: str, value: object) -> Mutation:
    return pdf(lambda writer, _: writer.root_object.__setitem__(NameObject(key), value))


def pdf_action(value: object) -> Mutation:
    return root_item("/A", value)


def uri_base(repo: Path) -> None:
    root_item(
        "/URI",
        DictionaryObject(
            {NameObject("/Base"): TextStringObject("https://example.com/")}
        ),
    )(repo)


def direct_absent(repo: Path) -> None:
    root_item(
        "/Fixture", DictionaryObject({NameObject("/Dest"): TextStringObject("absent")})
    )(repo)


def stream_open_action(repo: Path) -> None:
    def configure(writer: PdfWriter, _: object) -> None:
        hostile = stream_dictionary(
            action("/URI", URI=TextStringObject("https://example.com/reference"))
        )
        writer.root_object[NameObject("/OpenAction")] = writer._add_object(hostile)

    pdf(configure)(repo)


def stream_additional_actions(repo: Path) -> None:
    def configure(writer: PdfWriter, _: object) -> None:
        hostile = stream_dictionary(
            DictionaryObject(
                {
                    NameObject("/WC"): action(
                        "/URI",
                        URI=TextStringObject("https://example.com/reference"),
                    )
                }
            )
        )
        writer.root_object[NameObject("/AA")] = writer._add_object(hostile)

    pdf(configure)(repo)


def stream_catalog_names(repo: Path) -> None:
    def configure(writer: PdfWriter, reference: object) -> None:
        leaf = DictionaryObject(
            {
                NameObject("/Names"): ArrayObject(
                    [TextStringObject("a"), _destination_wrapper(reference)]
                )
            }
        )
        hostile = stream_dictionary(DictionaryObject({NameObject("/Dests"): leaf}))
        writer.root_object[NameObject("/Names")] = writer._add_object(hostile)
        writer.root_object[NameObject("/OpenAction")] = TextStringObject("a")

    pdf(configure)(repo)


def stream_name_tree_node(repo: Path) -> None:
    def configure(writer: PdfWriter, reference: object) -> None:
        hostile = stream_dictionary(
            DictionaryObject(
                {
                    NameObject("/Names"): ArrayObject(
                        [TextStringObject("a"), _destination_wrapper(reference)]
                    )
                }
            )
        )
        _install_destination_tree(writer, writer._add_object(hostile), "a")

    pdf(configure)(repo)


def stream_name_tree_wrapper(repo: Path) -> None:
    def configure(writer: PdfWriter, reference: object) -> None:
        hostile = stream_dictionary(_destination_wrapper(reference))
        leaf = DictionaryObject(
            {
                NameObject("/Names"): ArrayObject(
                    [TextStringObject("a"), writer._add_object(hostile)]
                )
            }
        )
        _install_destination_tree(writer, leaf, "a")

    pdf(configure)(repo)


def stream_structure_root(repo: Path) -> None:
    def configure(writer: PdfWriter, reference: object) -> None:
        element = DictionaryObject({NameObject("/Type"): NameObject("/StructElem")})
        element_reference = writer._add_object(element)
        hostile = stream_dictionary(
            DictionaryObject(
                {
                    NameObject("/Type"): NameObject("/StructTreeRoot"),
                    NameObject("/K"): ArrayObject([element_reference]),
                }
            )
        )
        writer.root_object[NameObject("/StructTreeRoot")] = writer._add_object(hostile)
        writer.root_object[NameObject("/OpenAction")] = action(
            "/GoTo",
            D=destination(reference),
            SD=ArrayObject([element_reference, NameObject("/Fit")]),
        )

    pdf(configure)(repo)


def stream_structure_element(repo: Path) -> None:
    def configure(writer: PdfWriter, reference: object) -> None:
        hostile = stream_dictionary(
            DictionaryObject({NameObject("/Type"): NameObject("/StructElem")})
        )
        element_reference = writer._add_object(hostile)
        structure_root = DictionaryObject(
            {
                NameObject("/Type"): NameObject("/StructTreeRoot"),
                NameObject("/K"): ArrayObject([element_reference]),
            }
        )
        writer.root_object[NameObject("/StructTreeRoot")] = writer._add_object(
            structure_root
        )
        writer.root_object[NameObject("/OpenAction")] = action(
            "/GoTo",
            D=destination(reference),
            SD=ArrayObject([element_reference, NameObject("/Fit")]),
        )

    pdf(configure)(repo)


def stream_catalog_uri(repo: Path) -> None:
    def configure(writer: PdfWriter, _: object) -> None:
        hostile = stream_dictionary(
            DictionaryObject(
                {NameObject("/Base"): TextStringObject("https://example.com/")}
            )
        )
        writer.root_object[NameObject("/URI")] = writer._add_object(hostile)

    pdf(configure)(repo)


def non_utf8_markdown(repo: Path) -> None:
    (repo / "README.md").write_bytes(b"# Caf\xe9\n")
    add(repo, "README.md")


def nbsp_wrong_anchor(repo: Path) -> None:
    readme(repo, "# A\u00a0B\n\n[x](#a-b)\n")


def entity_target(*, html_target: bool, correct_file: bool) -> Mutation:
    def mutate(repo: Path) -> None:
        filename = "a&amp;b.md" if correct_file else "a&b.md"
        write_text(repo / filename, "# Entity target\n")
        add(repo, filename)
        rendered_target = "a&amp;amp;b.md"
        markup = (
            f'<a href="{rendered_target}">x</a>'
            if html_target
            else f"[x]({rendered_target})"
        )
        readme(repo, f"# Entity target fixture\n\n{markup}\n")

    return mutate


def entity_heading_wrong_anchor(repo: Path) -> None:
    readme(repo, "# &amp;amp;amp;\n\n[x](#amp)\n")


def rendered_space_wrong_anchor(position: str) -> Mutation:
    def mutate(repo: Path) -> None:
        if position == "leading":
            heading = "&#x20;a"
        elif position == "trailing":
            heading = "a&#x20;"
        else:
            fail(f"unsupported rendered-space position: {position}")
        readme(repo, f"# {heading}\n\n[x](#a)\n")

    return mutate


def stripped_raw_html_anchor(repo: Path) -> None:
    readme(repo, '# Raw anchor\n\n[x](#ghost)\n\n<script id="ghost"></script>\n')


def footnoted_heading_anchor(repo: Path) -> None:
    readme(
        repo,
        "# Heading[^1]\n\n[x](#headingfootnote)\n\n[^1]: footnote\n",
    )


def unicode_number_anchor(repo: Path) -> None:
    readme(repo, "# ¼\n\n[x](#¼)\n")


def resource_target(value: str, *, html_target: bool = False) -> Mutation:
    def mutate(repo: Path) -> None:
        markup = (
            f'<img src="{value}" alt="fixture">'
            if html_target
            else f"![fixture]({value})"
        )
        readme(repo, f"# Resource fixture\n\n{markup}\n")

    return mutate


def catalog_javascript(repo: Path) -> None:
    script = action("/JavaScript", JS=TextStringObject("app.alert('hostile fixture')"))
    root_item(
        "/Names",
        DictionaryObject(
            {
                NameObject("/JavaScript"): DictionaryObject(
                    {
                        NameObject("/Names"): ArrayObject(
                            [TextStringObject("startup"), script]
                        )
                    }
                )
            }
        ),
    )(repo)


def malformed_structure_destination(repo: Path) -> None:
    def configure(writer: PdfWriter, reference: object) -> None:
        writer.root_object[NameObject("/OpenAction")] = action(
            "/GoTo",
            D=destination(reference),
            SD=TextStringObject("not-a-structure-destination"),
        )

    pdf(configure)(repo)


def boolean_xyz_destination(repo: Path) -> None:
    def configure(writer: PdfWriter, reference: object) -> None:
        writer.root_object[NameObject("/OpenAction")] = action(
            "/GoTo",
            D=ArrayObject(
                [
                    reference,
                    NameObject("/XYZ"),
                    BooleanObject(True),
                    NullObject(),
                    NullObject(),
                ]
            ),
        )

    pdf(configure)(repo)


def null_fitr_destination(repo: Path) -> None:
    def configure(writer: PdfWriter, reference: object) -> None:
        writer.root_object[NameObject("/OpenAction")] = action(
            "/GoTo",
            D=ArrayObject(
                [
                    reference,
                    NameObject("/FitR"),
                    NullObject(),
                    NullObject(),
                    NullObject(),
                    NullObject(),
                ]
            ),
        )

    pdf(configure)(repo)


def non_boolean_is_map(repo: Path) -> None:
    pdf_action(
        action(
            "/URI",
            URI=TextStringObject("https://example.com/reference"),
            IsMap=TextStringObject("not-a-boolean"),
        )
    )(repo)


def action_destination_conflict(owner: str) -> Mutation:
    def mutate(repo: Path) -> None:
        def configure(writer: PdfWriter, reference: object) -> None:
            conflicting = DictionaryObject(
                {
                    NameObject("/A"): action(
                        "/URI", URI=TextStringObject("https://example.com/reference")
                    ),
                    NameObject("/Dest"): destination(reference),
                }
            )
            if owner == "link":
                conflicting.update(
                    {
                        NameObject("/Type"): NameObject("/Annot"),
                        NameObject("/Subtype"): NameObject("/Link"),
                        NameObject("/Rect"): ArrayObject(
                            [
                                NumberObject(0),
                                NumberObject(0),
                                NumberObject(10),
                                NumberObject(10),
                            ]
                        ),
                    }
                )
                annotation_reference = writer._add_object(conflicting)
                writer.pages[0][NameObject("/Annots")] = ArrayObject(
                    [annotation_reference]
                )
            elif owner == "outline":
                outline_root = DictionaryObject(
                    {NameObject("/Type"): NameObject("/Outlines")}
                )
                outline_root_reference = writer._add_object(outline_root)
                conflicting.update(
                    {
                        NameObject("/Title"): TextStringObject("conflict"),
                        NameObject("/Parent"): outline_root_reference,
                    }
                )
                item_reference = writer._add_object(conflicting)
                outline_root[NameObject("/First")] = item_reference
                outline_root[NameObject("/Last")] = item_reference
                outline_root[NameObject("/Count")] = NumberObject(1)
                writer.root_object[NameObject("/Outlines")] = outline_root_reference
            else:
                fail(f"unsupported navigation owner: {owner}")

        pdf(configure)(repo)

    return mutate


def incomplete_structure_element(missing: str) -> Mutation:
    def mutate(repo: Path) -> None:
        def configure(writer: PdfWriter, reference: object) -> None:
            element = DictionaryObject(
                {
                    NameObject("/Type"): NameObject("/StructElem"),
                    NameObject("/S"): NameObject("/Document"),
                }
            )
            if missing == "S":
                del element[NameObject("/S")]
            element_reference = writer._add_object(element)
            structure_root = DictionaryObject(
                {
                    NameObject("/Type"): NameObject("/StructTreeRoot"),
                    NameObject("/K"): ArrayObject([element_reference]),
                }
            )
            structure_root_reference = writer._add_object(structure_root)
            if missing == "wrong-P":
                wrong_parent = writer._add_object(
                    DictionaryObject(
                        {NameObject("/Type"): NameObject("/StructTreeRoot")}
                    )
                )
                element[NameObject("/P")] = wrong_parent
            elif missing != "P":
                element[NameObject("/P")] = structure_root_reference
            writer.root_object[NameObject("/StructTreeRoot")] = structure_root_reference
            writer.root_object[NameObject("/OpenAction")] = action(
                "/GoTo",
                D=destination(reference),
                SD=ArrayObject([element_reference, NameObject("/Fit")]),
            )

        pdf(configure)(repo)

    return mutate


def shared_structure_element(repo: Path) -> None:
    def configure(writer: PdfWriter, reference: object) -> None:
        element = DictionaryObject(
            {
                NameObject("/Type"): NameObject("/StructElem"),
                NameObject("/S"): NameObject("/Document"),
            }
        )
        element_reference = writer._add_object(element)
        structure_root = DictionaryObject(
            {
                NameObject("/Type"): NameObject("/StructTreeRoot"),
                NameObject("/K"): ArrayObject([element_reference, element_reference]),
            }
        )
        structure_root_reference = writer._add_object(structure_root)
        element[NameObject("/P")] = structure_root_reference
        writer.root_object[NameObject("/StructTreeRoot")] = structure_root_reference
        writer.root_object[NameObject("/OpenAction")] = action(
            "/GoTo",
            D=destination(reference),
            SD=ArrayObject([element_reference, NameObject("/Fit")]),
        )

    pdf(configure)(repo)


def duplicate_named_destination(repo: Path) -> None:
    def configure(writer: PdfWriter, reference: object) -> None:
        invalid = DictionaryObject(
            {NameObject("/D"): ArrayObject([NumberObject(999), NameObject("/Fit")])}
        )
        valid = DictionaryObject(
            {NameObject("/D"): ArrayObject([reference, NameObject("/Fit")])}
        )
        destination_tree = DictionaryObject(
            {
                NameObject("/Names"): ArrayObject(
                    [
                        TextStringObject("duplicate"),
                        invalid,
                        TextStringObject("duplicate"),
                        valid,
                    ]
                )
            }
        )
        writer.root_object[NameObject("/Names")] = DictionaryObject(
            {NameObject("/Dests"): destination_tree}
        )
        writer.root_object[NameObject("/OpenAction")] = TextStringObject("duplicate")

    pdf(configure)(repo)


def wrong_name_tree_limits(repo: Path) -> None:
    def configure(writer: PdfWriter, reference: object) -> None:
        destination_tree = DictionaryObject(
            {
                NameObject("/Names"): ArrayObject(
                    [TextStringObject("a"), _destination_wrapper(reference)]
                ),
                NameObject("/Limits"): ArrayObject(
                    [TextStringObject("z"), TextStringObject("z")]
                ),
            }
        )
        _install_destination_tree(writer, destination_tree, "a")

    pdf(configure)(repo)


def odd_name_tree_array(repo: Path) -> None:
    def configure(writer: PdfWriter, reference: object) -> None:
        destination_tree = DictionaryObject(
            {
                NameObject("/Names"): ArrayObject(
                    [
                        TextStringObject("a"),
                        _destination_wrapper(reference),
                        TextStringObject("dangling"),
                    ]
                )
            }
        )
        _install_destination_tree(writer, destination_tree, "a")

    pdf(configure)(repo)


def unsorted_name_tree_keys(repo: Path) -> None:
    def configure(writer: PdfWriter, reference: object) -> None:
        destination_tree = DictionaryObject(
            {
                NameObject("/Names"): ArrayObject(
                    [
                        TextStringObject("b"),
                        _destination_wrapper(reference),
                        TextStringObject("a"),
                        _destination_wrapper(reference),
                    ]
                )
            }
        )
        _install_destination_tree(writer, destination_tree, "a")

    pdf(configure)(repo)


def mixed_name_tree_node(repo: Path) -> None:
    def configure(writer: PdfWriter, reference: object) -> None:
        child = DictionaryObject(
            {
                NameObject("/Names"): ArrayObject(
                    [TextStringObject("a"), _destination_wrapper(reference)]
                ),
                NameObject("/Limits"): ArrayObject(
                    [TextStringObject("a"), TextStringObject("a")]
                ),
            }
        )
        child_reference = writer._add_object(child)
        destination_tree = DictionaryObject(
            {
                NameObject("/Kids"): ArrayObject([child_reference]),
                NameObject("/Names"): ArrayObject(
                    [TextStringObject("z"), _destination_wrapper(reference)]
                ),
            }
        )
        _install_destination_tree(writer, destination_tree, "a")

    pdf(configure)(repo)


def cyclic_name_tree(repo: Path) -> None:
    def configure(writer: PdfWriter, reference: object) -> None:
        child = DictionaryObject(
            {
                NameObject("/Names"): ArrayObject(
                    [TextStringObject("a"), _destination_wrapper(reference)]
                ),
                NameObject("/Limits"): ArrayObject(
                    [TextStringObject("a"), TextStringObject("a")]
                ),
            }
        )
        child_reference = writer._add_object(child)
        destination_tree = DictionaryObject()
        destination_tree_reference = writer._add_object(destination_tree)
        destination_tree[NameObject("/Kids")] = ArrayObject(
            [child_reference, destination_tree_reference]
        )
        destination_tree[NameObject("/Limits")] = ArrayObject(
            [TextStringObject("a"), TextStringObject("a")]
        )
        _install_destination_tree(writer, destination_tree_reference, "a")

    pdf(configure)(repo)


def reversed_name_tree_children(repo: Path) -> None:
    def configure(writer: PdfWriter, reference: object) -> None:
        children = []
        for key in ("b", "a"):
            child = DictionaryObject(
                {
                    NameObject("/Names"): ArrayObject(
                        [TextStringObject(key), _destination_wrapper(reference)]
                    ),
                    NameObject("/Limits"): ArrayObject(
                        [TextStringObject(key), TextStringObject(key)]
                    ),
                }
            )
            children.append(writer._add_object(child))
        destination_tree = DictionaryObject(
            {
                NameObject("/Kids"): ArrayObject(children),
                NameObject("/Limits"): ArrayObject(
                    [TextStringObject("a"), TextStringObject("b")]
                ),
            }
        )
        _install_destination_tree(writer, destination_tree, "a")

    pdf(configure)(repo)


def legacy_catalog_destinations(repo: Path) -> None:
    def configure(writer: PdfWriter, reference: object) -> None:
        writer.root_object[NameObject("/Dests")] = DictionaryObject(
            {NameObject("/legacy"): _destination_wrapper(reference)}
        )
        writer.root_object[NameObject("/OpenAction")] = NameObject("/legacy")

    pdf(configure)(repo)


def _destination_wrapper(reference: object) -> DictionaryObject:
    return DictionaryObject(
        {NameObject("/D"): ArrayObject([reference, NameObject("/Fit")])}
    )


def _install_destination_tree(
    writer: PdfWriter, destination_tree: object, open_name: str
) -> None:
    writer.root_object[NameObject("/Names")] = DictionaryObject(
        {NameObject("/Dests"): destination_tree}
    )
    writer.root_object[NameObject("/OpenAction")] = TextStringObject(open_name)


def next_action_cycle(length: int) -> Mutation:
    def mutate(repo: Path) -> None:
        def configure(writer: PdfWriter, _: object) -> None:
            first = action("/URI", URI=TextStringObject("https://example.com/first"))
            first_reference = writer._add_object(first)
            if length == 1:
                first[NameObject("/Next")] = first_reference
            elif length == 2:
                second = action(
                    "/URI", URI=TextStringObject("https://example.com/second")
                )
                second_reference = writer._add_object(second)
                first[NameObject("/Next")] = second_reference
                second[NameObject("/Next")] = first_reference
            else:
                fail(f"unsupported action-cycle length: {length}")
            writer.root_object[NameObject("/OpenAction")] = first_reference

        pdf(configure)(repo)

    return mutate


def configure_valid_pdf_edges(writer: PdfWriter, reference: object) -> None:
    structure_element = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/StructElem"),
            NameObject("/S"): NameObject("/Document"),
        }
    )
    structure_element_reference = writer._add_object(structure_element)
    structure_root = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/StructTreeRoot"),
            NameObject("/K"): ArrayObject([structure_element_reference]),
        }
    )
    structure_root_reference = writer._add_object(structure_root)
    structure_element[NameObject("/P")] = structure_root_reference
    writer.root_object[NameObject("/StructTreeRoot")] = structure_root_reference
    writer.root_object[NameObject("/OpenAction")] = action(
        "/GoTo",
        D=destination(reference),
        SD=ArrayObject([structure_element_reference, NameObject("/Fit")]),
    )
    writer.root_object[NameObject("/FixtureXyz")] = DictionaryObject(
        {
            NameObject("/A"): action(
                "/GoTo",
                D=ArrayObject(
                    [
                        reference,
                        NameObject("/XYZ"),
                        NumberObject(0),
                        NullObject(),
                        NumberObject(1),
                    ]
                ),
            )
        }
    )
    writer.root_object[NameObject("/FixtureUri")] = DictionaryObject(
        {
            NameObject("/A"): action(
                "/URI",
                URI=TextStringObject("https://example.com/reference"),
                IsMap=BooleanObject(False),
            )
        }
    )
    writer.root_object[NameObject("/FixtureFitR")] = DictionaryObject(
        {
            NameObject("/A"): action(
                "/GoTo",
                D=ArrayObject(
                    [
                        reference,
                        NameObject("/FitR"),
                        NumberObject(0),
                        NumberObject(0),
                        NumberObject(144),
                        NumberObject(144),
                    ]
                ),
            )
        }
    )


def semantic_controls(repo: Path) -> None:
    write_text(repo / "a&amp;b.md", "# Entity target\n")
    add(repo, "a&amp;b.md")
    readme(
        repo,
        """# A\u00a0B

[NBSP anchor](#ab)

# &amp;amp;

[Entity heading](#amp)

# &#x20;Lead

[Leading rendered space](#-lead)

# Trail&#x20;

[Trailing rendered space](#trail-)
[Markdown entity target](a&amp;amp;b.md)
<a href="a&amp;amp;b.md">Raw HTML entity target</a>
""",
    )


def valid_pdf_edge_control(repo: Path) -> None:
    write_pdf(repo / "output/pdf/guide.pdf", configure_valid_pdf_edges)
    add(repo, "output/pdf/guide.pdf")


def configure_fsmonitor_control(repo: Path) -> Path:
    hook = repo / "fsmonitor-hook"
    write_text(
        hook,
        "#!/bin/sh\ntouch \"$0.executed\"\nprintf '0\\n'\n",
    )
    hook.chmod(0o755)
    git(repo, ["config", "core.fsmonitor", str(hook)])
    return Path(f"{hook}.executed")


H = (
    Hostile(
        "staged bad/worktree good",
        staged_bad,
        ("worktree/index byte divergence", "missing.md"),
    ),
    Hostile("unstaged divergence", divergent, ("worktree/index byte divergence",)),
    Hostile("nonempty intent-to-add", ita("# x\n"), ("intent-to-add entries",)),
    Hostile("empty intent-to-add", ita(""), ("intent-to-add entries",)),
    Hostile(
        "assume-unchanged intent-to-add",
        hidden_ita("--assume-unchanged"),
        ("index",),
    ),
    Hostile(
        "skip-worktree intent-to-add",
        hidden_ita("--skip-worktree"),
        ("index",),
    ),
    Hostile("unmerged stage", unmerged, ("unmerged index entry",)),
    Hostile("symlink mode", symlink, ("unsupported index mode 120000",)),
    Hostile("gitlink mode", gitlink, ("unsupported index mode 160000",)),
    Hostile("HTML file", target("file:///tmp/x", True), ("forbidden file: URI",)),
    Hostile(
        "HTML javascript",
        target("javascript:alert(1)", True),
        ("forbidden javascript: URI",),
    ),
    Hostile("HTML data", target("data:text/plain,x", True), ("forbidden data: URI",)),
    Hostile("autolink file", autolink("file:///tmp/x"), ("forbidden file: URI",)),
    Hostile(
        "autolink javascript",
        autolink("javascript:alert(1)"),
        ("forbidden javascript: URI",),
    ),
    Hostile("autolink data", autolink("data:text/plain,x"), ("forbidden data: URI",)),
    Hostile("missing path", target("missing.md"), ("not present in the staged index",)),
    Hostile("missing anchor", target("target.md#absent"), ("missing Markdown anchor",)),
    Hostile("wrong case", target("Target.md"), ("case mismatch",)),
    Hostile(
        "wrong directory kind",
        target("docs#anchor"),
        ("directory target cannot validate fragment",),
    ),
    Hostile(
        "blob missing",
        target("https://github.com/sepahead/pid-rs/blob/main/missing.md"),
        ("not present in the staged index",),
    ),
    Hostile(
        "blob untracked",
        target("https://github.com/sepahead/pid-rs/blob/main/untracked.md"),
        ("not present in the staged index",),
    ),
    Hostile(
        "blob case",
        target("https://github.com/sepahead/pid-rs/blob/main/Docs/guide.md"),
        ("case mismatch",),
    ),
    Hostile(
        "blob directory",
        target("https://github.com/sepahead/pid-rs/blob/main/docs"),
        ("targets a directory, not a file",),
    ),
    Hostile(
        "tree file",
        target("https://github.com/sepahead/pid-rs/tree/main/docs/guide.md"),
        ("targets a file, not a directory",),
    ),
    Hostile(
        "main anchor",
        target("https://github.com/sepahead/pid-rs/blob/main/docs/guide.md#absent"),
        ("missing Markdown anchor",),
    ),
    Hostile(
        "main http",
        target("http://github.com/sepahead/pid-rs/blob/main/docs/guide.md"),
        ("not in canonical HTTPS form",),
    ),
    Hostile(
        "main host",
        target("https://www.github.com/sepahead/pid-rs/blob/main/docs/guide.md"),
        ("not in canonical HTTPS form",),
    ),
    Hostile(
        "main path case",
        target("https://github.com/Sepahead/pid-rs/blob/main/docs/guide.md"),
        ("not in canonical HTTPS form",),
    ),
    Hostile(
        "main refs-heads alias",
        target("https://github.com/sepahead/pid-rs/blob/refs/heads/main/missing.md"),
        ("canonical",),
    ),
    Hostile(
        "main trailing-dot host alias",
        target("https://github.com./sepahead/pid-rs/blob/main/missing.md"),
        ("canonical",),
    ),
    Hostile(
        "main inserted dot-segment alias",
        target("https://github.com/sepahead/pid-rs/./blob/main/docs/guide.md"),
        ("dot-segment alias",),
    ),
    Hostile(
        "main parent dot-segment alias",
        target(
            "https://github.com/sepahead/pid-rs/blob/not-main/../main/docs/guide.md"
        ),
        ("dot-segment alias",),
    ),
    Hostile(
        "main leading dot-segment alias",
        target("https://github.com/./sepahead/pid-rs/blob/main/docs/guide.md"),
        ("dot-segment alias",),
    ),
    Hostile(
        "main repeated-slash alias",
        target("https://github.com/sepahead/pid-rs//blob/main/docs/guide.md"),
        ("repeated-slash",),
    ),
    Hostile(
        "GitHub raw-main route alias",
        target("https://github.com/sepahead/pid-rs/raw/main/missing.md"),
        ("canonical",),
    ),
    Hostile(
        "GitHub raw refs-heads-main route alias",
        target("https://github.com/sepahead/pid-rs/raw/refs/heads/main/missing.md"),
        ("canonical",),
    ),
    Hostile(
        "raw main branch root",
        target("https://raw.githubusercontent.com/sepahead/pid-rs/main"),
        ("no target path",),
    ),
    Hostile(
        "raw file terminal-directory marker",
        target("https://raw.githubusercontent.com/sepahead/pid-rs/main/README.md/"),
        ("terminal directory marker",),
    ),
    Hostile(
        "legacy raw GitHub hostname",
        target("https://raw.github.com/sepahead/pid-rs/main/missing.md"),
        ("canonical",),
    ),
    Hostile(
        "raw heads-main alias",
        target(
            "https://raw.githubusercontent.com/sepahead/pid-rs/heads/main/missing.md"
        ),
        ("canonical",),
    ),
    Hostile(
        "GitHub HEAD revision alias",
        target("https://github.com/sepahead/pid-rs/blob/HEAD/missing.md"),
        ("canonical",),
    ),
    Hostile(
        "GitHub at-sign revision alias",
        target("https://github.com/sepahead/pid-rs/blob/%40/missing.md"),
        ("canonical",),
    ),
    Hostile(
        "GitHub main ancestor revision alias",
        target("https://github.com/sepahead/pid-rs/blob/main~0/missing.md"),
        ("canonical",),
    ),
    Hostile(
        "GitHub main typed revision alias",
        target(
            "https://github.com/sepahead/pid-rs/blob/main%5E%7Bcommit%7D/missing.md"
        ),
        ("canonical",),
    ),
    Hostile(
        "raw HEAD revision alias",
        target("https://raw.githubusercontent.com/sepahead/pid-rs/HEAD/missing.md"),
        ("canonical",),
    ),
    Hostile(
        "raw main parent revision alias",
        target("https://raw.githubusercontent.com/sepahead/pid-rs/main^0/missing.md"),
        ("canonical",),
    ),
    Hostile(
        "main percent",
        target("https://github.com/sepahead/pid-rs/blob/main/docs%2Fguide.md"),
        ("structural or control percent alias",),
    ),
    Hostile(
        "main backslash",
        target("https://github.com/sepahead/pid-rs/blob/main/docs\\guide.md", True),
        ("contains a backslash",),
    ),
    Hostile(
        "main control",
        target("https://github.com/sepahead/pid-rs/blob/main/docs/%0Aguide.md"),
        ("structural or control percent alias",),
    ),
    Hostile(
        "malformed percent", target("target.md%ZZ"), ("malformed percent encoding",)
    ),
    Hostile(
        "NBSP heading wrong anchor",
        nbsp_wrong_anchor,
        ("missing Markdown anchor #a-b",),
    ),
    Hostile(
        "Markdown double-entity target",
        entity_target(html_target=False, correct_file=False),
        ("not present in the staged index",),
    ),
    Hostile(
        "raw HTML double-entity target",
        entity_target(html_target=True, correct_file=False),
        ("not present in the staged index",),
    ),
    Hostile(
        "double-entity heading wrong anchor",
        entity_heading_wrong_anchor,
        ("missing Markdown anchor #amp",),
    ),
    Hostile(
        "leading rendered-space wrong anchor",
        rendered_space_wrong_anchor("leading"),
        ("missing Markdown anchor #a",),
    ),
    Hostile(
        "trailing rendered-space wrong anchor",
        rendered_space_wrong_anchor("trailing"),
        ("missing Markdown anchor #a",),
    ),
    Hostile(
        "stripped raw-HTML anchor",
        stripped_raw_html_anchor,
        ("missing Markdown anchor #ghost",),
    ),
    Hostile(
        "footnoted heading anchor",
        footnoted_heading_anchor,
        ("footnoted heading anchor semantics",),
    ),
    Hostile(
        "Unicode other-number heading anchor",
        unicode_number_anchor,
        ("missing Markdown anchor #¼",),
    ),
    Hostile(
        "Markdown image directory",
        resource_target("docs"),
        ("image/resource target is not an indexed file",),
    ),
    Hostile(
        "raw HTML image directory",
        resource_target("docs", html_target=True),
        ("image/resource target is not an indexed file",),
    ),
    Hostile(
        "same-repository tree used as image",
        resource_target("https://github.com/sepahead/pid-rs/tree/main/docs"),
        ("image/resource target is not an indexed file",),
    ),
    Hostile(
        "empty Markdown image",
        resource_target(""),
        ("image/resource target has no file path",),
    ),
    Hostile(
        "mailto Markdown image",
        resource_target("mailto:user@example.com"),
        ("requires a local file or HTTP(S) URL",),
    ),
    Hostile(
        "mailto raw HTML image",
        resource_target("mailto:user@example.com", html_target=True),
        ("requires a local file or HTTP(S) URL",),
    ),
    Hostile("non-UTF-8 Markdown", non_utf8_markdown, ("UTF-8",)),
    Hostile("extra pdf", extra("extra.pdf"), ("not present in the staged index",)),
    Hostile("extra PDF", extra("extra.PDF"), ("not present in the staged index",)),
    Hostile(
        "declared root PDF absent from index",
        root_publication_unindexed,
        ("declared root publication PDF is absent from the staged index",),
    ),
    Hostile(
        "relative URI in declared root PDF",
        root_publication_relative_uri,
        ("relative PDF URI is not portable",),
    ),
    Hostile("malformed PDF", malformed, ("cannot parse indexed PDF strictly",)),
    Hostile(
        "encrypted PDF", encrypted, ("encrypted publication PDFs are not admitted",)
    ),
    Hostile(
        "GoTo no D", pdf_action(action("/GoTo")), ("GoTo action has no /D destination",)
    ),
    Hostile(
        "unknown action",
        pdf_action(action("/Launch")),
        ("PDF action /Launch is not admitted",),
    ),
    Hostile(
        "GoToR",
        pdf_action(action("/GoToR", F=TextStringObject("guide.pdf"))),
        ("PDF action /GoToR is not admitted",),
    ),
    Hostile(
        "relative URI",
        pdf_action(action("/URI", URI=TextStringObject("../../target.md"))),
        ("relative PDF URI is not portable",),
    ),
    Hostile(
        "file URI",
        pdf_action(action("/URI", URI=TextStringObject("file:///tmp/x"))),
        ("forbidden file: URI",),
    ),
    Hostile(
        "URI Base", uri_base, ("catalog /URI /Base changes relative-link semantics",)
    ),
    Hostile(
        "unresolved GoTo",
        pdf_action(action("/GoTo", D=TextStringObject("absent"))),
        ("unresolved named destination",),
    ),
    Hostile("unresolved Dest", direct_absent, ("unresolved named destination",)),
    Hostile(
        "malformed AA",
        root_item("/AA", TextStringObject("bad")),
        ("additional-actions slot is not a dictionary",),
    ),
    Hostile(
        "Link annotation A/Dest conflict",
        action_destination_conflict("link"),
        ("mutually exclusive /A and /Dest",),
    ),
    Hostile(
        "outline A/Dest conflict",
        action_destination_conflict("outline"),
        ("mutually exclusive /A and /Dest",),
    ),
    Hostile(
        "malformed Next",
        pdf_action(
            action(
                "/URI",
                URI=TextStringObject("https://example.com"),
                Next=TextStringObject("bad"),
            )
        ),
        ("action slot is not a dictionary",),
    ),
    Hostile("catalog JavaScript", catalog_javascript, ("JavaScript",)),
    Hostile(
        "malformed structure destination",
        malformed_structure_destination,
        ("structure destination",),
    ),
    Hostile(
        "StructElem missing role",
        incomplete_structure_element("S"),
        ("NameObject /S role",),
    ),
    Hostile(
        "StructElem missing parent",
        incomplete_structure_element("P"),
        ("no /P parent",),
    ),
    Hostile(
        "StructElem wrong parent",
        incomplete_structure_element("wrong-P"),
        ("does not match traversal",),
    ),
    Hostile(
        "shared StructElem child",
        shared_structure_element,
        ("shared structure-child",),
    ),
    Hostile(
        "Boolean XYZ destination parameter",
        boolean_xyz_destination,
        ("destination parameter",),
    ),
    Hostile(
        "null FitR destination parameter",
        null_fitr_destination,
        ("FitR",),
    ),
    Hostile("non-Boolean IsMap", non_boolean_is_map, ("IsMap",)),
    Hostile(
        "duplicate named destination",
        duplicate_named_destination,
        ("duplicate",),
    ),
    Hostile(
        "wrong name-tree Limits",
        wrong_name_tree_limits,
        ("Limits",),
    ),
    Hostile(
        "odd name-tree Names array",
        odd_name_tree_array,
        ("even",),
    ),
    Hostile(
        "unsorted name-tree keys",
        unsorted_name_tree_keys,
        ("strictly ordered",),
    ),
    Hostile(
        "mixed Kids and Names name-tree node",
        mixed_name_tree_node,
        ("/Kids", "/Names"),
    ),
    Hostile("cyclic name tree", cyclic_name_tree, ("cyclic",)),
    Hostile(
        "reversed name-tree children",
        reversed_name_tree_children,
        ("ordered",),
    ),
    Hostile(
        "legacy catalog Dests",
        legacy_catalog_destinations,
        ("legacy", "/Dests"),
    ),
    Hostile("stream OpenAction", stream_open_action, ("neither an action",)),
    Hostile(
        "stream additional-actions dictionary",
        stream_additional_actions,
        ("additional-actions slot is not a dictionary",),
    ),
    Hostile(
        "stream catalog Names",
        stream_catalog_names,
        ("name-tree container is not a dictionary",),
    ),
    Hostile(
        "stream destination name-tree node",
        stream_name_tree_node,
        ("name-tree node is not a dictionary",),
    ),
    Hostile(
        "stream destination wrapper",
        stream_name_tree_wrapper,
        ("bounded destination wrapper",),
    ),
    Hostile(
        "stream structure root",
        stream_structure_root,
        ("structure root is not a dictionary",),
    ),
    Hostile(
        "stream structure element",
        stream_structure_element,
        ("structure child",),
    ),
    Hostile("stream catalog URI", stream_catalog_uri, ("catalog /URI",)),
    Hostile("one-node Next cycle", next_action_cycle(1), ("cyclic",)),
    Hostile("two-node Next cycle", next_action_cycle(2), ("cyclic",)),
)


def main() -> int:
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    if pypdf.__version__ != EXPECTED_PYPDF_VERSION:
        fail(f"requires pypdf {EXPECTED_PYPDF_VERSION}")
    if CHECKER.is_symlink() or not CHECKER.is_file():
        fail("production checker is unusable")
    with tempfile.TemporaryDirectory(
        prefix="pid-rs-publication-links-v2-"
    ) as temporary:
        base = Path(temporary)
        control = base / "control"
        initialize(control)
        success(control, "compound baseline")

        semantic_control = base / "semantic-control"
        initialize(semantic_control)
        semantic_controls(semantic_control)
        success(semantic_control, "entity and GitHub-slug controls")

        pdf_edge_control = base / "pdf-edge-control"
        initialize(pdf_edge_control)
        valid_pdf_edge_control(pdf_edge_control)
        success(pdf_edge_control, "valid PDF destination and action-value controls")

        fsmonitor_control = base / "fsmonitor-control"
        initialize(fsmonitor_control)
        fsmonitor_sentinel = configure_fsmonitor_control(fsmonitor_control)
        success(fsmonitor_control, "repository-local fsmonitor isolation control")
        if fsmonitor_sentinel.exists():
            fail("production checker executed the repository-local fsmonitor hook")

        for number, case in enumerate(H, 1):
            repo = base / f"hostile-{number:02d}"
            initialize(repo)
            if case.name == "blob untracked":
                write_text(repo / "untracked.md", "# Untracked\n")
            case.mutate(repo)
            rejection(repo, case)
    print(
        f"OK: {CHECK_NAME} passed (4 controls; {len(H)}/{len(H)} hostile mutations rejected; optimized={bool(sys.flags.optimize)})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
