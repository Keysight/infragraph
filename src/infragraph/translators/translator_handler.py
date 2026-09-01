import os
import stat

from infragraph.translators.lstopo_translator import run_lstopo_parser
from infragraph.translators.nccl_translator import run_nccl_parser

DEFAULT_OUTPUT_FILE = "device.yaml"


def _resolve_output_path(output_path: str | None) -> str:
    """Resolve the CLI --output value.

    An explicit value (including one that happens to equal the old default)
    is always used as-is. When --output is omitted, translated data goes to
    stdout if this process' stdout is itself a pipe (e.g. `infragraph
    translate lstopo | infragraph visualize ...`); otherwise it falls back
    to device.yaml exactly as before, so standalone invocations are unchanged.
    """
    if output_path is not None:
        return output_path
    if stat.S_ISFIFO(os.fstat(1).st_mode):
        return "-"
    return DEFAULT_OUTPUT_FILE


def run_translator(tool: str, input_file: str, output_path: str | None, dump_format: str, device_name: str) -> str:
    supported_translators = ["lstopo", "nccl"]
    if tool not in supported_translators:
        raise ValueError(f"Unsupported tool: {tool}")

    output_path = _resolve_output_path(output_path)

    if tool == "lstopo":
        run_lstopo_parser(device_name, input_file, output_path, dump_format)

    elif tool == "nccl":
        if device_name is None:
            raise ValueError(
                "The 'nccl' translator requires a device name. "
                "Please provide it via the --device-name option."
            )
        run_nccl_parser(device_name, input_file, output_path, dump_format)


