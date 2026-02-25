import importlib
import click


@click.command()
@click.option(
    "-t",
    "--translator",
    required=True,
    type=click.Choice(["lstopo", "lspci"]),
    help="Translator to use",
)
@click.option(
    "--input",
    "input_file",
    required=True,
    type=click.Path(exists=True),
    help="Input file",
)
@click.option(
    "--output",
    default="yaml",
    type=click.Choice(["json", "yaml", "dict"]),
    help="Output format",
)
def main(translator, input_file, output):
    module = importlib.import_module(
        f"infragraph.translators.{translator}_translator"
    )

    result = module.run(input_file, output)
    click.echo(result)


if __name__ == "__main__":
    main()