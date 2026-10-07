"""Build the PQL.Assert library from src/lib and merge it into the test models.

Commands:
  check   Fail (exit 1) if any test model's PQL.Assert.* functions drift from src/lib.
  sync    Rewrite each test model's functions.tmdl with the src/lib functions,
          keeping test-suite UDFs, lineageTags and the model's function order.
  stage   Copy the test PBIPs to an output folder (default: _stage) with the
          merged functions.tmdl, ready for deployment.

Drift ignores lineageTag, annotations, /// and // comment lines, and whitespace,
so a Power BI Desktop round-trip does not count as drift.
"""

import argparse
import difflib
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC_LIB = REPO / "src" / "lib"
LIBRARY_PREFIX = "PQL.Assert."

# (PBIP folder, model name)
MODELS = [
    (REPO / "tests" / "model", "TestingModel"),
    (REPO / "tests" / "rls_model", "RLS_Model"),
]

FUNCTION_RE = re.compile(r"^function\s+'([^']+)'\s*=")
NON_LOGIC_RE = re.compile(r"^\s*(lineageTag:|annotation\s|///|//)")


class Block:
    """One function in a TMDL file: leading /// lines, the function line, its
    expression lines and its property lines (lineageTag, annotation, ...)."""

    def __init__(self, name, docs, header, expression, properties):
        self.name = name
        self.docs = docs
        self.header = header
        self.expression = expression
        self.properties = properties

    @property
    def lineage_tag(self):
        return next((p for p in self.properties if p.startswith("lineageTag:")), None)

    @property
    def logic(self):
        """Whitespace-insensitive expression text used for drift comparison."""
        lines = [l for l in self.expression if l.strip() and not NON_LOGIC_RE.match(l)]
        return " ".join(" ".join(lines).split())

    def render(self):
        """Render in the layout Power BI Desktop writes: tabs for the base
        indentation and a blank line after each property."""
        out = list(self.docs) + [self.header]
        out += ["\t\t" + l if l else "" for l in _trim_blank(self.expression)]
        for prop in self.properties:
            out.append("\t" + prop)
            out.append("")
        if not self.properties:
            out.append("")
        return out


def _trim_blank(lines):
    lines = list(lines)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def _strip_levels(line, levels, unit):
    """Remove `levels` indentation units (a tab or `unit` spaces) from the start of line."""
    for _ in range(levels):
        if line.startswith("\t"):
            line = line[1:]
        elif line.startswith(" " * unit):
            line = line[unit:]
        else:
            break
    return line


def _depth(line, unit):
    depth, i = 0, 0
    while i < len(line):
        if line[i] == "\t":
            depth, i = depth + 1, i + 1
        elif line.startswith(" " * unit, i):
            depth, i = depth + 1, i + unit
        else:
            break
    return depth


def parse_blocks(lines, unit=4):
    """Parse top-level function blocks. `lines` must already be at depth 0 for
    /// and function lines, depth 1 for properties, depth 2+ for the expression."""
    blocks, docs, cur = [], [], None
    for line in lines:
        if line.startswith("///"):
            if cur:
                blocks.append(cur)
                cur = None
            docs.append(line)
            continue
        m = FUNCTION_RE.match(line)
        if m:
            if cur:
                blocks.append(cur)
            cur = Block(m.group(1), docs, line, [], [])
            docs = []
            continue
        if cur is None:
            continue
        if not line.strip():
            if not cur.properties:
                cur.expression.append("")
            continue
        depth = _depth(line, unit)
        if depth >= 2:
            cur.expression.append(_strip_levels(line, 2, unit))
        else:
            cur.properties.append(line.strip())
    if cur:
        blocks.append(cur)
    return blocks


def read_library():
    """Parse every src/lib/*.tmdl createOrReplace script into function blocks."""
    library = {}
    for path in sorted(SRC_LIB.glob("*.tmdl")):
        if path.name == "functions.tmdl":
            continue
        raw = path.read_text(encoding="utf-8-sig").splitlines()
        unit = 4
        body = []
        for line in raw:
            if re.match(r"^\s*createOrReplace\s*$", line):
                continue
            body.append(_strip_levels(line.rstrip(), 1, unit))
        for block in parse_blocks(body, unit):
            if block.name in library:
                raise SystemExit(f"Duplicate function {block.name} in {path.name}")
            library[block.name] = block
    return library


def functions_path(folder, model):
    return folder / f"{model}.SemanticModel" / "definition" / "functions.tmdl"


def read_model(folder, model):
    text = functions_path(folder, model).read_text(encoding="utf-8-sig")
    return parse_blocks(text.splitlines())


def merge(library, model_blocks):
    """Replace library functions in place, drop ones no longer in src/lib,
    keep every other UDF, and append new library functions at the end."""
    merged, seen = [], set()
    for block in model_blocks:
        if not block.name.startswith(LIBRARY_PREFIX):
            merged.append(block)
            continue
        src = library.get(block.name)
        if src is None:
            continue
        seen.add(block.name)
        merged.append(_with_lineage(src, block.lineage_tag))
    merged += [b for n, b in library.items() if n not in seen]
    return merged


def _with_lineage(src, lineage_tag):
    props = [p for p in src.properties if not p.startswith("lineageTag:")]
    if lineage_tag:
        props.insert(0, lineage_tag)
    return Block(src.name, src.docs, src.header, src.expression, props)


def render(blocks):
    lines = []
    for block in blocks:
        lines += block.render()
    return "\n".join(_trim_blank(lines)) + "\n\n"


def drift(library, model_blocks):
    model_lib = {b.name: b for b in model_blocks if b.name.startswith(LIBRARY_PREFIX)}
    missing = sorted(set(library) - set(model_lib))
    removed = sorted(set(model_lib) - set(library))
    changed = sorted(n for n in set(library) & set(model_lib)
                     if library[n].logic != model_lib[n].logic)
    return missing, removed, changed, model_lib


def cmd_check(library, verbose):
    failed = False
    for folder, model in MODELS:
        blocks = read_model(folder, model)
        missing, removed, changed, model_lib = drift(library, blocks)
        suites = [b.name for b in blocks if not b.name.startswith(LIBRARY_PREFIX)]
        status = "OK" if not (missing or removed or changed) else "DRIFT"
        print(f"{model}: {status} ({len(model_lib)} library functions, {len(suites)} other UDFs)")
        for label, names in (("missing", missing), ("removed from src/lib", removed), ("changed", changed)):
            for name in names:
                print(f"  {label}: {name}")
                if verbose and label == "changed":
                    a = library[name].logic.split(" ")
                    b = model_lib[name].logic.split(" ")
                    for d in difflib.unified_diff(a, b, "src/lib", model, n=3, lineterm=""):
                        print(f"      {d}")
        failed |= status == "DRIFT"
    if failed:
        print("\nThe test models are out of sync with src/lib. Run:\n"
              "  python ci/build_stage.py sync\n"
              "then reopen the models in Power BI Desktop and commit the result.")
    return 1 if failed else 0


def cmd_sync(library):
    for folder, model in MODELS:
        path = functions_path(folder, model)
        blocks = parse_blocks(path.read_text(encoding="utf-8-sig").splitlines())
        missing, removed, changed, _ = drift(library, blocks)
        if not (missing or removed or changed):
            # Leave Desktop's formatting alone when the logic already matches.
            print(f"{model}: already in sync")
            continue
        path.write_text(render(merge(library, blocks)), encoding="utf-8", newline="\n")
        print(f"{model}: updated {path.relative_to(REPO)}")
    return 0


def cmd_stage(library, out):
    out = (REPO / out).resolve()
    if out.exists():
        shutil.rmtree(out)
    ignore = shutil.ignore_patterns("localSettings.json", "cache.abf")
    for folder, model in MODELS:
        for item in ("SemanticModel", "Report"):
            src = folder / f"{model}.{item}"
            if src.exists():
                shutil.copytree(src, out / src.name, ignore=ignore)
        staged = functions_path(out, model)
        staged.write_text(render(merge(library, read_model(folder, model))),
                          encoding="utf-8", newline="\n")
        print(f"{model}: staged to {staged.parent.parent.relative_to(REPO)}")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="fail if test models drift from src/lib")
    check.add_argument("-v", "--verbose", action="store_true", help="show token diffs for changed functions")
    sub.add_parser("sync", help="write src/lib functions into the test models")
    stage = sub.add_parser("stage", help="copy test PBIPs with merged functions to an output folder")
    stage.add_argument("--out", default="_stage")
    args = parser.parse_args()

    library = read_library()
    if args.command == "check":
        return cmd_check(library, args.verbose)
    if args.command == "sync":
        return cmd_sync(library)
    return cmd_stage(library, args.out)


if __name__ == "__main__":
    sys.exit(main())
