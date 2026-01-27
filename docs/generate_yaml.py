import sys
import os

if __package__ in ["", None]:
    sys.path.insert(
        0,
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")),
    )
    print(f"Testing code using src\n{sys.path}")

from infragraph.blueprints.devices.server import Server
from infragraph.blueprints.devices.generic_switch import Switch
from infragraph.blueprints.fabrics.closfabric import ClosFabric
from infragraph.blueprints.devices.nvidia.cx5 import Cx5
from infragraph.blueprints.devices.nvidia.dgx import Dgx

for item in [Server(), Switch(), ClosFabric(), Cx5(), Dgx()]:
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "src", "yaml", f"{item.name}.yaml"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wt") as fp:
        fp.write(item.serialize(item.YAML))
