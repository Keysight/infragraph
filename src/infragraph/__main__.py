import typer
from infragraph.translators.translator_handler import run_translator
from infragraph.visualizer.visualize import run_visualizer
 
app = typer.Typer()
 
@app.command()
def translate(
    tool = typer.Argument(..., help="Translator to use available lstopo, nccl"),
    input_file = typer.Option(None, "--input", "-i", help="Input file Path"),
    output_file = typer.Option("device.yaml","--output", "-o", help="Output file path"),
    device_name = typer.Option(None, "--device-name", help="Name of the device or system being described. Required for the 'nccl' translator; inferred from the XML for 'lstopo' if not provided."),
    dump = typer.Option("yaml", "--dump", help="Dump format (json or yaml)")
):
    """Translate the tools"""
    run_translator(tool, input_file, output_file, dump, device_name)
 
@app.command()
def visualize(
    input_path: str = typer.Option(
        ...,
        "--input", "-i",
        help="Path to the InfraGraph infrastructure yaml/json file.",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
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
    run_visualizer(
        input_file=input_path,
        hosts=hosts,
        switches=switches,
        output=output_dir,
    )
 
 
if __name__ == "__main__":
    app()