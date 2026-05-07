import networkx
from infragraph.infragraph import *
from infragraph.infragraph_service import InfraGraphService
from infragraph.blueprints.devices.amd.mi300x import MI300X
from infragraph.visualizer.visualize import run_visualizer

device = MI300X()

infrastructure=Api().infrastructure()
infrastructure.devices.append(device)
infrastructure.instances.add(
    name=device.name,
    device=device.name,
    count=1,
)

device.validate()
service = InfraGraphService()
service.set_graph(infrastructure)

g = service.get_networkx_graph()
print(f"\ndevice {device.name} is a {g}")
print(networkx.write_network_text(g, vertical_chains=True))

'''run_visualizer(
    infrastructure=infrastructure,
    output="./viz",
    hosts=device.name,
)'''