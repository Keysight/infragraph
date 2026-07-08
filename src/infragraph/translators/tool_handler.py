import os

from infragraph.translators.lstopo_translator import run_lstopo_parser
from infragraph.translators.nccl_translator import run_nccl_parser

SUPPORTED_TOOLS = ["lstopo", "nccl"]


def _resolve_output_path(output_path: str, dump_format: str) -> str:
    """Resolve the final output file path, creating directories as needed.

    - No output specified -> ``device.<dump_format>`` in the current directory.
    - ``-`` -> passed through unchanged (serialized output goes to stdout).
    - A directory (ends with a separator or is an existing dir) -> the directory
      is created and the file is written as ``<dir>/device.<dump_format>``.
    - Otherwise treated as a file path; its parent directory is created.

    The file extension is derived from ``dump_format`` so the extension always
    reflects the actual content (e.g. ``--dump json`` writes ``device.json``).
    """
    if output_path is None:
        return f"device.{dump_format}"

    if output_path == "-":
        return output_path

    is_dir = output_path.endswith(("/", os.sep)) or os.path.isdir(output_path)
    if is_dir:
        os.makedirs(output_path, exist_ok=True)
        return os.path.join(output_path, f"device.{dump_format}")

    parent = os.path.dirname(output_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    return output_path


def run_discoverer(tool: str, output_path: str, dump_format: str, device_name: str = None) -> str:
    """Discover the local topology by running the tool itself, then translate.

    No input file is taken; the tool (e.g. lstopo, nccl) is executed to produce
    the raw topology, which is then converted into an InfraGraph.
    """
    if tool not in SUPPORTED_TOOLS:
        raise ValueError(f"Unsupported tool: {tool}")
    if tool == "lstopo":
        # input_file=None signals run_lstopo_parser to run lstopo and
        # auto-generate the XML before parsing. device_name is optional for
        # lstopo — it is inferred from the XML when not supplied.
        return run_lstopo_parser(
            device_name,
            input_file=None,
            output_file=_resolve_output_path(output_path, dump_format),
            dump_format=dump_format,
        )
    elif tool == "nccl":
        # input_file=None signals run_nccl_parser to run NCCL and auto-generate
        # the topology XML before parsing. NCCL topology carries no device name,
        # so one must be supplied explicitly.
        if device_name is None or device_name == "":
            raise ValueError(
                "discover requires --device-name for the 'nccl' discoverer."
            )
        return run_nccl_parser(
            device_name,
            None,
            _resolve_output_path(output_path, dump_format),
            dump_format,
        )

def run_translator(tool: str, input_file: str, output_path: str, dump_format: str, device_name: str = None) -> str:
    """Translate an existing topology file into an InfraGraph.

    Requires an input file; this does not auto-generate the raw topology.
    Use the ``discover`` subcommand to auto-generate it.
    """
    if tool not in SUPPORTED_TOOLS:
        raise ValueError(f"Unsupported tool: {tool}")
    if input_file is None or input_file == "":
        raise ValueError(
            "translate requires an input file (--input/-i). "
            "Use 'infragraph discover' to auto-generate the topology instead."
        )
    if tool == "lstopo":
        return run_lstopo_parser(
            device_name,
            input_file=input_file,
            output_file=_resolve_output_path(output_path, dump_format),
            dump_format=dump_format,
        )
    elif tool == "nccl":
        if device_name is None or device_name == "":
            raise ValueError(
                "translate requires --device-name for the 'nccl' translator."
            )
        return run_nccl_parser(
            device_name,
            input_file,
            _resolve_output_path(output_path, dump_format),
            dump_format,
        )

