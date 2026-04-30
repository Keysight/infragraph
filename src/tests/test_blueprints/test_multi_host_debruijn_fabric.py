from infragraph.infragraph_service import InfraGraphService
from infragraph.blueprints.devices.generic.server import Server
from infragraph.blueprints.devices.generic.generic_switch import Switch
from infragraph.blueprints.fabrics.multi_host_debruijn_fabric import DeBruijnFabricWithMultiHost
import networkx
import yaml


def dump_yaml(debruijn_fabric, filename):
    with open(filename + ".yaml", "w") as file:
        data = debruijn_fabric.serialize("dict")
        yaml.dump(data, file, default_flow_style=False, indent=4)


def test_debruijn():
    switch = Switch(port_count=16)
    server = Server()  

    fabric = DeBruijnFabricWithMultiHost(
        switch=switch,
        server=server,
        order=3,
    )

    service = InfraGraphService()
    service.set_graph(fabric)

    dump_yaml(fabric, "multi_host_debruijn")

    g = service.get_networkx_graph()
    #print(g)
    

if __name__ == "__main__":
    test_debruijn()