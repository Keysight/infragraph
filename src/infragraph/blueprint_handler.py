import importlib
import inspect
from pathlib import Path
from typing import List, NamedTuple, Literal, Optional, Union, get_args, get_origin
from infragraph import Device

import typer

PACKAGE_ROOT = Path(__file__).parent
DEVICES_ROOT = PACKAGE_ROOT / "blueprints" / "devices"

DESCRIPTIONS = {
    "mi300x": "AMD Instinct MI300X AI/ML host (NIC + GPU + PCIe switch topology)",
    "osfp": "OSFP pluggable transceiver (400G/800G optical module)",
    "qsfp": "QSFP pluggable transceiver",
    "sfp": "SFP pluggable transceiver",
    "generic-switch": "Generic Ethernet switch with a configurable port count",
    "server": "Generic server with a configurable NPU factor",
    "ironwood-rack": "Google Ironwood TPU rack (4x4x4 3D-torus, 64 XPUs)",
    "cx5": "NVIDIA/Mellanox ConnectX-5 NIC",
    "dgx": "NVIDIA DGX system (selectable profile, e.g. DGX H100)",
}


class Blueprint(NamedTuple):
    slug: str
    category: str  # vendor/category dir, or "" for uncategorized
    py_file: Path


def discover_blueprints() -> List[Blueprint]:
    """List device blueprints from the folder layout alone — no imports needed."""
    found: List[Blueprint] = []
    for py_file in sorted(DEVICES_ROOT.rglob("*.py")):
        if py_file.name.startswith("_"):
            continue

        rel_parts = py_file.relative_to(DEVICES_ROOT).parts  # ('amd', 'mi300x.py')
        slug = py_file.stem.replace("_", "-")
        # <category>/<file>.py -> category; flat files -> ""
        category = rel_parts[0] if len(rel_parts) > 1 else ""

        found.append(Blueprint(slug, category, py_file))
    return found


def _format(bp: Blueprint, indent: str) -> str:
    line = f"{indent}- {bp.slug}"
    desc = DESCRIPTIONS.get(bp.slug, "")
    if desc:
        line += f"  —  {desc}"
    return line


def run_list_blueprints() -> None:
    devices = discover_blueprints()

    if devices:
        typer.echo("\nDevices:")
        for category in sorted({bp.category for bp in devices if bp.category}):
            typer.echo(f"  {category}")
            for bp in (b for b in devices if b.category == category):
                typer.echo(_format(bp, "    "))
        for bp in (b for b in devices if not b.category): # incase no category/vendors
            typer.echo(_format(bp, "  "))

    typer.echo("")


def _load_blueprint_class(py_file: Path):
    """Import a single blueprint file and return the blueprint class it defines."""

    rel = py_file.relative_to(PACKAGE_ROOT)
    module_name = "infragraph." + ".".join(rel.with_suffix("").parts)
    module = importlib.import_module(module_name)
    for cls in vars(module).values(): # find all classes in a module
        if not isinstance(cls, type) or cls.__module__ != module.__name__: # if cls in not a class
            continue
        if issubclass(cls, Device) and cls is not Device:
            return cls
    return None



# --- Dynamic per-device CLI -------------------------------------------------
#
# Each device blueprint's constructor is introspected so its parameters become
# real CLI options (e.g. `infragraph blueprint dgx --profile dgx_h100`).
# `Literal[...]` annotations turn into a fixed choice list; ints/floats/bools
# map to their click types; anything else (incl. Union[str, Device]) is a string.


def _typer_annotation(annotation):
    """Map a constructor annotation to one Typer can render as a CLI option.

    `Literal[...]` and scalars are kept as-is (Typer turns Literals into a
    choice list natively). Optionals are preserved. Anything Typer can't
    express on a flag — notably `Union[str, Device]` — collapses to `str`.
    """
    if annotation is inspect.Parameter.empty:
        return str

    origin = get_origin(annotation)

    # if it's a choice list or a basic scalar, keep it exactly as written; only fall through to the rewriting logic for the awkward types.
    if origin is Literal or annotation in (int, float, bool, str):
        return annotation

    if origin is Union:
        members = [a for a in get_args(annotation) if a is not type(None)]
        has_none = type(None) in get_args(annotation)
        # Optional[Literal[...]] / Optional[<scalar>] round-trip unchanged.
        if len(members) == 1 and (
            get_origin(members[0]) is Literal or members[0] in (int, float, bool, str)
        ):
            return annotation
        # Union[str, Device] and friends -> a plain (optional) string.
        return Optional[str] if has_none else str

    return str


def _make_command(cls, slug: str):
    """Build a Typer command callback whose options mirror cls.__init__."""
    sig = inspect.signature(cls.__init__) # reads the parameter list of the device class's constructor
    params: List[inspect.Parameter] = []
    annotations = {}

    for pname, param in sig.parameters.items():
        if pname == "self":
            continue
        if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD): # This skips *args and **kwargs parameters, because they can't be turned into concrete CLI options.
            continue
        ann = _typer_annotation(param.annotation)
        has_default = param.default is not inspect.Parameter.empty
        option = typer.Option(param.default if has_default else ...)
        params.append(
            inspect.Parameter(
                pname, inspect.Parameter.KEYWORD_ONLY, default=option, annotation=ann
            )
        )
        annotations[pname] = ann

    params.append(
        inspect.Parameter(
            "output",
            inspect.Parameter.KEYWORD_ONLY,
            default=typer.Option(
                None, "--output", "-o",
                help=f"Output YAML path (defaults to {slug}.yaml).",
            ),
            annotation=Optional[str],
        )
    )
    annotations["output"] = Optional[str]

    def command(**kwargs):
        output = kwargs.pop("output", None)
        instance = cls(**kwargs)
        out = output or f"{slug}.yaml"
        Path(out).write_text(instance.serialize(encoding=Device.YAML))
        typer.echo(f"Wrote {out}")

    # Hand Typer a synthetic signature so it introspects the per-device options.
    command.__signature__ = inspect.Signature(params)
    command.__annotations__ = annotations
    command.__name__ = slug.replace("-", "_")
    doc = (cls.__doc__ or "").strip()
    command.__doc__ = doc.split("\n", 1)[0] if doc else DESCRIPTIONS.get(slug, "")
    return command


def build_blueprint_app() -> typer.Typer:
    """Build the `blueprint` sub-app with one command per device blueprint."""
    bp_app = typer.Typer(
        help="Generate a device blueprint, passing its constructor parameters as options.",
        no_args_is_help=True,
    )

    @bp_app.command(name="list")
    def _list():
        """List the available device blueprints, grouped by vendor."""
        run_list_blueprints()

    for bp in discover_blueprints():
        cls = _load_blueprint_class(bp.py_file)
        if cls is None:
            continue
        # bp_app.command(name=...) returns a decorator (a function that takes a function and registers it). The @ just applies that returned decorator to the function defined right below it.
        # Why we can't use @bp_app in the loop: the @ form requires a def (or class) literally written underneath it, with a name known at write-time. But here the commands are generated in a loop — there's no def to decorate, and the name (bp.slug) varies per iteration. So we call it directly:
        bp_app.command(name=bp.slug)(_make_command(cls, bp.slug)) # creating command dynamically here
    return bp_app