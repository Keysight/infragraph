import click
from infragraph.translators.translator_handler import run_translator


@click.group()
def cli():
    pass

@cli.command()
@click.argument("tool", type=click.Choice(["lstopo", "lspci"]))
@click.option("-i", "--input", "input_file", help="Input file path")
@click.option("-o", "--output", "output_file", default="dev.yaml", help="Output file path")
@click.option("--dump", type=click.Choice(["dict", "json", "yaml"]), default="yaml")
def translator(tool, input_file, output_file, dump):
    """Run selected translator"""
    run_translator(tool, input_file, output_file, dump)

# we can add some more cli.command() eg for visualizer.

if __name__ == "__main__":
    cli()