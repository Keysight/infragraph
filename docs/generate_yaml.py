import sys
import os

if __package__ in ["", None]:
    sys.path.insert(
        0,
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")),
    )
    print(f"Testing code using src\n{sys.path}")
from infragraph import *
from infragraph.blueprints.devices.generic.server import Server
from infragraph.blueprints.devices.generic.generic_switch import Switch
from infragraph.blueprints.fabrics.closfabric import ClosFabric
from infragraph.blueprints.devices.nvidia.cx5 import Cx5
from infragraph.blueprints.devices.nvidia.dgx import NvidiaDGX
from infragraph.blueprints.devices.common.transceiver.qsfp import QSFP
from infragraph.infragraph_service import InfraGraphService

for item in [Server(), Switch(), ClosFabric(), Cx5(), NvidiaDGX()]:
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "src", "yaml", f"{item.name}.yaml"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wt") as fp:
        fp.write(item.serialize(item.YAML))

# generate for dgx(cx5(qsfp))
qsfp = QSFP("qsfp28_100g")
cx5 = Cx5(variant="cx5_100g_single", transceiver=qsfp)
dgx = NvidiaDGX("dgx_h100", cx5)
infrastructure = Api().infrastructure()
# we need to append added devices
infrastructure.devices.append(dgx).append(cx5).append(qsfp)
infrastructure.instances.add(name=dgx.name, device=dgx.name, count=1)
infrastructure.name = "dgx_cx5_qsfp_composed"
path = os.path.abspath(os.path.join(os.path.dirname(__file__), "src", "yaml", f"{infrastructure.name}.yaml"))
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, "wt") as fp:
    fp.write(infrastructure.serialize(infrastructure.YAML))

# generate for dgx(cx5)
cx5 = "cx5_100g_single"
dgx = NvidiaDGX("dgx_h100", cx5)
infrastructure = Api().infrastructure()
# we need to append added devices
infrastructure.devices.append(dgx)
infrastructure.instances.add(name=dgx.name, device=dgx.name, count=1)
infrastructure.name = "dgx_cx5_nic"
path = os.path.abspath(os.path.join(os.path.dirname(__file__), "src", "yaml", f"{infrastructure.name}.yaml"))
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, "wt") as fp:
    fp.write(infrastructure.serialize(infrastructure.YAML))