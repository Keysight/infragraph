import typer
from infragraph.translators.translator_handler import run_translator
app = typer.Typer()

@app.command()
def translator(
    tool = typer.Argument(..., help="Translator to use"),
    input_file = typer.Option(None, "--input", "-i", help="Input file Path"),
    output_file = typer.Option("dev.yaml","--output", "-o", help="Output file path"),
    dump = typer.Option("yaml", "--dump", help="Dump format (json or yaml)")
):

    run_translator(tool, input_file, output_file, dump)


@app.command()
def visualizer(

):
    pass


if __name__ == "__main__":
    app()