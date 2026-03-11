import re
from pathlib import Path
from nbconvert import PythonExporter
import nbformat
import textwrap

def wrap_notebook_in_function(input_nb_path: Path, output_py_path: Path, function_name: str):
    """
    Converts a Jupyter notebook (.ipynb) to a Python script wrapped inside a function.
    """
    with open(input_nb_path, "r", encoding="utf-8") as f:
        notebook = nbformat.read(f, as_version=4)

    exporter = PythonExporter()
    script_body, _ = exporter.from_notebook_node(notebook)

    cleaned_code = []
    for line in script_body.splitlines():
        if re.match(r"^#\s*In\[.*\]:", line):
            continue
        if "# coding:" in line or line.strip().startswith("#!/usr/bin/env"):
            continue
        cleaned_code.append(line)

    cleaned_script = "\n".join(cleaned_code)
    cleaned_script = re.sub(r"\n\s*\n+", "\n\n", cleaned_script)

    # ---- separate imports ----
    import_lines = []
    code_lines = []

    for line in cleaned_script.splitlines():
        if re.match(r"^\s*(import |from .+ import )", line):
            import_lines.append(line)
        else:
            code_lines.append(line)

    imports_block = "\n".join(import_lines)
    code_block = "\n".join(code_lines)

    # indent only the actual code
    indented_code = textwrap.indent(code_block, "        ")

    wrapped_code = (
        f"{imports_block}\n\n"
        f"def {function_name}():\n\n"
        f"    try:"
        f"{indented_code}\n"
        f"        assert True\n"
        f"    except Exception as e:\n"
        f"        assert False, f'Unexpected exception: {{e}}'\n"
    )
    output_py_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_py_path, "w", encoding="utf-8") as f:
        f.write(wrapped_code)

    print(f"Converted: {input_nb_path} → {output_py_path}")


def convert_all_notebooks(root_dir: str = "infragraph/notebooks"):
    """
    Recursively converts all .ipynb notebooks under `root_dir` into Python files
    wrapped in functions, saving them under a `tests/` subfolder.
    """
    for notebook_path in Path(root_dir).rglob("*.ipynb"):
        if ".ipynb_checkpoints" in notebook_path.parts:
            continue
        output_name = f"test_{notebook_path.stem}.py"
        output_path = Path("tests") / "test_notebooks" / output_name

        function_name = output_path.stem

        wrap_notebook_in_function(notebook_path, output_path, function_name)       


if __name__ == "__main__":
    convert_all_notebooks()
