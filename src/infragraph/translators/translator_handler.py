from infragraph.translators.lstopo_translator import run_lstopo_parser
from infragraph.translators.nccl_translator import run_nccl_parser


def run_translator(tool: str, input_file: str, output_path: str, dump_format: str, device_name: str) -> str:
    supported_translators = ["lstopo", "nccl"]
    if tool not in supported_translators:
        raise ValueError(f"Unsupported tool: {tool}")
    if tool == "lstopo":
        run_lstopo_parser(device_name, input_file, output_path, dump_format)

    elif tool == "nccl":
        if device_name is None:
            raise ValueError(
                "The 'nccl' translator requires a device name. "
                "Please provide it via the --device-name option."
            )
        run_nccl_parser(device_name, input_file, output_path, dump_format)
    

