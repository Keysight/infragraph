# InfraGraph CLI

InfraGraph provides a command-line interface (CLI) built with [Typer](https://typer.tiangolo.com/) for converting system descriptions into InfraGraph format and visualizing infrastructure topologies.

## Installation

```bash
pip install infragraph
```

Alternatively, clone the repo and build:

```bash
git clone https://github.com/Keysight/infragraph.git
cd infragraph
make clean
make install
```

Or download the `.whl` from [releases](https://github.com/Keysight/infragraph/releases) and install directly:

```bash
pip install infragraph-<version>.whl
```

Once installed, the `infragraph` command is available in your terminal.

## Commands

### `translate`

Convert output from supported system tools into an InfraGraph YAML or JSON definition.

```
infragraph translate <tool> -i <input_file> -o <output_file> --dump <format>
```

| Argument / Option | Description |
|---|---|
| `tool` | Translator to use (e.g., `lstopo`) |
| `-i`, `--input` | Path to the input file |
| `-o`, `--output` | Output file path (default: `dev.yaml`) |
| `--dump` | Output format — `yaml` or `json` (default: `yaml`) |

**Supported translators:** `lstopo`

**Example** — convert an `lstopo` XML export to InfraGraph YAML:

```bash
infragraph translate lstopo -i lstopo_output.xml -o my_device.yaml --dump yaml
```

### `visualize`

Generate an interactive HTML visualization from an InfraGraph infrastructure definition.

```
infragraph visualize -i <input_file> -o <output_dir> [--hosts <hosts>] [--switches <switches>]
```

| Option | Description |
|---|---|
| `-i`, `--input` | Path to the InfraGraph YAML/JSON file |
| `-o`, `--output` | Output directory where the visualization will be generated |
| `--hosts` | Comma-separated device names to render as hosts |
| `--switches` | Comma-separated device names to render as switches |

**Example** — visualize an infrastructure with host and switch hints:

```bash
infragraph visualize -i my_infrastructure.yaml -o ./viz --hosts "dgx_a100" --switches "leaf_switch,spine_switch"
```

Then open `./viz/index.html` in a browser. The visualizer produces a multi-level view: a top-level graph of instances and inter-device connectivity, with drill-down into each device's internal components (xPUs, NICs, CPUs, memory, PCIe topology, etc.).
