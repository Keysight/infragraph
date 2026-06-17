import typer
from infragraph.translators.tool_handler import run_translator, run_discoverer
from infragraph.visualizer.visualize import run_visualizer

app = typer.Typer()

@app.command()
def discover(
    tool = typer.Argument(..., help="Discoverer to use"),
    output_file = typer.Option(None, "--output", "-o", help="Output file path (defaults to device.<dump>)"),
    dump = typer.Option("yaml", "--dump", help="Dump format (json or yaml)")
):
    """Run the tool on the local machine to auto-generate and translate the topology."""
    run_discoverer(tool, output_file, dump)

@app.command()
def translate(
    tool = typer.Argument(..., help="Translator to use"),
    input_file = typer.Option(..., "--input", "-i", help="Input file Path"),
    output_file = typer.Option(None, "--output", "-o", help="Output file path (defaults to device.<dump>)"),
    dump = typer.Option("yaml", "--dump", help="Dump format (json or yaml)")
):
    """Translate an existing topology input file into an InfraGraph."""
    run_translator(tool, input_file, output_file, dump)

@app.command()
def visualize(
    input_path: str = typer.Option(
        None,
        "--input", "-i",
        help="Path to the InfraGraph infrastructure yaml/json file. "
             "Omit (or use '-') to read from stdin, e.g. "
             "'infragraph translate lstopo -o - | infragraph visualize -o ./viz'.",
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
    """Visualize the infragraph"""
    run_visualizer(
        input_file=input_path,
        hosts=hosts,
        switches=switches,
        output=output_dir,
    )
 
 
if __name__ == "__main__":
    app()