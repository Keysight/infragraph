import typer
from infragraph.translators.translator_handler import run_translator
from infragraph.visualizer.visualize import run_visualizer

app = typer.Typer()

@app.command()
def translate(
    tool = typer.Argument(..., help="Translator to use"),
    input_file = typer.Option(None, "--input", "-i", help="Input file Path"),
    output_file = typer.Option("dev.yaml","--output", "-o", help="Output file path"),
    dump = typer.Option("yaml", "--dump", help="Dump format (json or yaml)")
):

    run_translator(tool, input_file, output_file, dump)

@app.command()
def visualize(
    input_path: str = typer.Option(
        ...,
        "--input", "-i",
        help="Path to the InfraGraph infrastructure file.",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    hosts: str = typer.Option(
        "",
        "--hosts",
        help="Comma-separated instance names that are hosts (e.g., 'dgx1,dgx2'). Only used in visualizer mode.",
    ),
    switches: str = typer.Option(
        "",
        "--switches",
        help="Comma-separated switch names (e.g., 'sw1,sw2'). Only used in visualizer mode.",
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