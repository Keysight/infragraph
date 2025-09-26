import sys
import os

if __package__ in ["", None]:
    sys.path.insert(
        0,
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")),
    )
    print(f"Testing code using src\n{sys.path}")

from infragraph.server import Server
from infragraph.switch import Switch
from infragraph.closfabric import ClosFabric
from infragraph.cx5 import Cx5
from infragraph.dgx import Dgx

for item in [Server(), Switch(), ClosFabric(), Cx5(), Dgx()]:
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "src", "yaml", f"{item.name}.yaml"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wt") as fp:
        fp.write(item.serialize(item.YAML))
