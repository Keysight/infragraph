from infragraph.translators.lstopo_translator import run_lstopo_parser

def run_translator(tool: str, input_file: str, output_path: str, dump_format: str) -> str:
    supported_translators = ["lstopo"]
    if tool not in supported_translators:
        raise ValueError(f"Unsupported tool: {tool}")
    if tool == "lstopo":
        run_lstopo_parser(input_file, output_path, dump_format)

