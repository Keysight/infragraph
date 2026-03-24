import click
from infragraph.translators.translator_handler import run_translator
from .visualizer.visualize import run_visualizer


@click.group()
def cli():
    pass

@cli.command()
@click.argument("tool", type=click.Choice(["lstopo", "lspci"]))
@click.option("-i", "--input", "input_file", help="Input file path")
@click.option("-o", "--output", "output_file", default="dev.yaml", help="Output file path")
@click.option("--dump", type=click.Choice(["json", "yaml"]), default="yaml")

def translator(tool, input_file, output_file, dump):
    """Run selected translator"""
    run_translator(tool, input_file, output_file, dump)

@cli.command()
@click.option(
    "--input", "-i",
    "input_path",
    required=True,
    type=click.Path(exists=True, dir_okay=False, readable=True, path_type=str),
    help="Path to the InfraGraph infrastructure file.",
)
@click.option(
    "--hosts",
    default="",
    help="Comma-separated instance names that are hosts (e.g., 'dgx1,dgx2'). Only used in visualizer mode.",
)
@click.option(
    "--switches",
    default="",
    help="Comma-separated switch names (e.g., 'sw1,sw2'). Only used in visualizer mode.",
)
@click.option(
    "--output", "-o",
    "output_dir",
    required=True,
    type=click.Path(file_okay=False, writable=True, path_type=str),
    help="Output directory path where results will be generated.",
)

def visualize(input_path: str, hosts: str, switches: str, output_dir: str):
   """Visualize the graph"""
   run_visualizer(input_file=input_path, hosts=hosts, switches=switches, output=output_dir)



if __name__ == "__main__":
    cli()