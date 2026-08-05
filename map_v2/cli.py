from __future__ import annotations

import argparse
from importlib import import_module
import json
from pathlib import Path
import sys

from .domain import MapDomainError, load_domain_manifest
from .lattice import DEFAULT_STATE_DIR, MapV2Error, MapV2Lattice
from .runtime import MapRuntimeError, PrologTargetCompiler


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="map-v2",
        description="Independent LLM-operated Prolog lattice and proof shell.",
    )
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE_DIR, help="Lattice state directory")
    parser.add_argument(
        "--domain-manifest",
        type=Path,
        required=True,
        help="Path to a map.domain.v1 manifest",
    )
    parser.add_argument(
        "--construction-adapter",
        help="Explicit PSC adapter as MODULE:ATTRIBUTE for typed construction commands",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    _add_mutation_commands(sub)
    _add_query_commands(sub)
    return parser


def _add_mutation_commands(sub: argparse._SubParsersAction) -> None:
    new = sub.add_parser("new", help="Create a lattice and its managed Prolog workspace")
    new.add_argument("subject")
    new.add_argument("target")
    new.add_argument("--root")

    expand = sub.add_parser("expand", help="Break an open node into child nodes")
    expand.add_argument("name")
    expand.add_argument("parts", nargs="+")

    kappa = sub.add_parser("kappa", help="Declare the domain invariants a node must preserve")
    kappa.add_argument("name")
    kappa.add_argument("domain")
    kappa.add_argument("invariants", nargs="+", metavar="NAME=DESCRIPTION")

    compute = sub.add_parser("compute", help="Inspect domain obligations before authoring facts")
    compute.add_argument("name", nargs="?")

    fill = sub.add_parser("fill", help="Build a computed node with complete Prolog facts")
    fill.add_argument("name")
    fill.add_argument("facts", nargs="+")

    fill_construction = sub.add_parser(
        "fill-construction",
        help="Validate a PSC payload and lower it into candidate-only facts",
    )
    fill_construction.add_argument("name")
    fill_construction.add_argument("payload", help="JSON object or @path/to/payload.json")

    retry = sub.add_parser("retry", help="Move a SOUP node back to DERIVE for repair")
    retry.add_argument("name")

    revise = sub.add_parser("revise", help="Replace a repairing node's facts after COMPUTE")
    revise.add_argument("name")
    revise.add_argument("facts", nargs="+")

    revise_construction = sub.add_parser(
        "revise-construction",
        help="Replace a repairing node with a validated PSC payload",
    )
    revise_construction.add_argument("name")
    revise_construction.add_argument("payload", help="JSON object or @path/to/payload.json")

    select = sub.add_parser("select", help="Select the node compile uses by default")
    select.add_argument("name")

    compile_parser = sub.add_parser("compile", help="Verify the selected node through its MAP domain")
    compile_parser.add_argument("name", nargs="?")

    combine = sub.add_parser("combine", help="Combine nodes with compatible current ONT certificates")
    combine.add_argument("name")
    combine.add_argument("sources", nargs="+")

    export_certificate = sub.add_parser(
        "export-certificate", help="Export one current compiled MAP certificate"
    )
    export_certificate.add_argument("output", type=Path)
    export_certificate.add_argument("name", nargs="?")

    promote = sub.add_parser("promote", help="Promote a combined PATTERN to IMPLEMENT")
    promote.add_argument("name")

    reify = sub.add_parser("reify", help="Turn an IMPLEMENT pattern into an SES+1 DERIVE node")
    reify.add_argument("name")


def _add_query_commands(sub: argparse._SubParsersAction) -> None:
    sub.add_parser("next", help="Show the next lawful LLM work item")
    sub.add_parser("queue", help="Show open, repair, and compile work")
    sub.add_parser("guide", help="Route the next generic MAP lattice move")
    sub.add_parser("tree", help="Show the lattice tree")
    show = sub.add_parser("show", help="Show the lattice or one node")
    show.add_argument("name", nargs="?")
    sub.add_parser("workspace", help="Show the managed Prolog workspace path and source")


def _dispatch(args: argparse.Namespace, lattice: MapV2Lattice):
    if args.command == "new":
        return lattice.create(args.subject, args.target, root=args.root)
    if args.command == "expand":
        return lattice.expand(args.name, args.parts)
    if args.command == "kappa":
        return lattice.declare_kappa(args.name, args.domain, _parse_invariants(args.invariants))
    if args.command == "compute":
        return lattice.compute(args.name)
    if args.command == "fill":
        return lattice.fill(args.name, args.facts)
    if args.command == "fill-construction":
        return lattice.fill_construction(args.name, _parse_payload(args.payload))
    if args.command == "retry":
        return lattice.retry(args.name)
    if args.command == "revise":
        return lattice.revise(args.name, args.facts)
    if args.command == "revise-construction":
        return lattice.revise_construction(args.name, _parse_payload(args.payload))
    if args.command == "select":
        return lattice.select(args.name)
    if args.command == "compile":
        return lattice.compile(args.name)
    if args.command == "combine":
        return lattice.combine(args.name, args.sources)
    if args.command == "export-certificate":
        return _write_artifact(args.output, lattice.export_certificate(args.name))
    if args.command == "promote":
        return lattice.promote(args.name)
    if args.command == "reify":
        return lattice.reify(args.name)
    if args.command == "next":
        return lattice.next()
    if args.command == "queue":
        return {"queue": lattice.queue()}
    if args.command == "guide":
        return lattice.guide()
    if args.command == "tree":
        return lattice.tree()
    if args.command == "show":
        return lattice.show(args.name)
    if args.command == "workspace":
        lattice.show()
        return {
            "workspace": str(lattice.workspace_path),
            "source": lattice.workspace_path.read_text(encoding="utf-8"),
        }
    raise MapV2Error(f"unsupported command: {args.command}")


def _parse_invariants(values: list[str]) -> dict[str, str]:
    invariants: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise MapV2Error(
                f"invariant must use NAME=DESCRIPTION syntax: {value!r}"
            )
        name, description = value.split("=", 1)
        name = name.strip()
        description = description.strip()
        if not name or not description:
            raise MapV2Error(
                f"invariant must have a non-empty name and description: {value!r}"
            )
        if name in invariants:
            raise MapV2Error(f"duplicate invariant: {name}")
        invariants[name] = description
    return invariants


def _parse_payload(value: str) -> dict:
    if value.startswith("@"):
        payload = json.loads(Path(value[1:]).read_text(encoding="utf-8"))
    else:
        payload = json.loads(value)
    if not isinstance(payload, dict):
        raise MapV2Error("typed construction payload must be a JSON object")
    return payload


def _load_construction_adapter(reference: str | None):
    if not reference:
        return None
    if ":" not in reference:
        raise MapV2Error("construction adapter must use MODULE:ATTRIBUTE syntax")
    module_name, attribute = reference.split(":", 1)
    value = getattr(import_module(module_name), attribute)
    return value() if isinstance(value, type) else value


def _write_artifact(path: Path, payload: dict) -> dict:
    if path.exists():
        raise MapV2Error(f"refusing to overwrite artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    digest = payload.get("envelope_sha256") or payload.get("candidate_sha256")
    return {"artifact": str(path.resolve()), "sha256": digest}


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        domain = load_domain_manifest(args.domain_manifest)
        lattice = MapV2Lattice(
            args.state,
            compiler=PrologTargetCompiler(domain),
            construction_adapter=_load_construction_adapter(
                args.construction_adapter
            ),
        )
        result = _dispatch(args, lattice)
    except (MapDomainError, MapRuntimeError, MapV2Error, ValueError) as exc:  # codenose ignore: expected CLI error packet
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps({"ok": True, "result": result}, indent=2, sort_keys=True))
    return 0
