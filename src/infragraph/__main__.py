import os
import stat
import typer
from infragraph.translators.translator_handler import run_translator
from infragraph.visualizer.visualize import run_visualizer

app = typer.Typer()


def _stdin_is_pipe() -> bool:
    return stat.S_ISFIFO(os.fstat(0).st_mode)


@app.command()
def translate(
    tool = typer.Argument(..., help="Translator to use available lstopo, nccl"),
    input_file = typer.Option(None, "--input", "-i", help="Input file Path"),
    output_file = typer.Option(
        None, "--output", "-o",
        help="Output file path. Defaults to device.yaml. If omitted and this "
             "command's output is piped to another command (e.g. "
             "'infragraph translate lstopo | infragraph visualize ...'), the "
             "translated data is written to stdout instead.",
    ),
    device_name = typer.Option(None, "--device-name", help="Name of the device or system being described. Required for the 'nccl' translator; inferred from the XML for 'lstopo' if not provided."),
    dump = typer.Option("yaml", "--dump", help="Dump format (json or yaml)")
):
    """Translate the tools"""
    run_translator(tool, input_file, output_file, dump, device_name)

@app.command()
def visualize(
    input_path: str = typer.Option(
        None,
        "--input", "-i",
        help="Path to the InfraGraph infrastructure yaml/json file. If "
             "omitted, reads from stdin when piped in from another command "
             "(e.g. 'infragraph translate lstopo | infragraph visualize "
             "--output OUT_DIR').",
    ),
    hosts: str = typer.Option(
        "",
        "--hosts",
        help="Comma-separated instance names that are hosts (used in visualizer).",
    ),
    switches: str = typer.Option(
        "",
        "--switches",
        help="Comma-separated switch names (used in visualizer).",
    ),
    output_dir: str = typer.Option(
        ...,
        "--output", "-o",
        help="Output directory path where results will be generated.",
        file_okay=False,
        writable=True,
    ),
):
    """Visualize the graph"""
    if input_path is None:
        if not _stdin_is_pipe():
            raise typer.BadParameter(
                "No input provided. Pass --input FILE, or pipe data in, e.g. "
                "'infragraph translate lstopo | infragraph visualize --output OUT_DIR'.",
                param_hint="--input",
            )
        input_path = "-"
    elif not os.path.isfile(input_path):
        raise typer.BadParameter(f"Input file not found: {input_path}", param_hint="--input")

    run_visualizer(
        input_file=input_path,
        hosts=hosts,
        switches=switches,
        output=output_dir,
    )
 
 
if __name__ == "__main__":
    app()