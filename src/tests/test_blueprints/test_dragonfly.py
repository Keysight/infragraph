import pytest
import networkx
from infragraph.infragraph_service import InfraGraphService
from infragraph.blueprints.devices.generic.generic_switch import Switch
from infragraph.blueprints.devices.generic.server import Server
from infragraph.blueprints.devices.nvidia.dgx import NvidiaDGX
from infragraph.blueprints.devices.amd.mi300x import MI300X
from infragraph.blueprints.fabrics.dragonfly_fabric import DragonflyFabric
from infragraph.visualizer.visualize import run_visualizer

def print_graph(graph):
    # for node, attrs in graph.nodes(data=True):
    #     print(f"Node: {node}, Attributes: {attrs}")

    # for u, v, attrs in graph.edges(data=True):
    #     print(f"Edge: ({u}, {v}), Attributes: {attrs}")
    pass

def dump_yaml(clos_fabric, filename):
    # import yaml
    # with open(filename + ".yaml", "w") as file:
    #     data = clos_fabric.serialize("dict")
    #     yaml.dump(data, file, default_flow_style=False, indent=4)
    pass

@pytest.mark.asyncio
async def test_dragonfly_server():
    """
    Generate and validate the dragonfly topology with server as host
    """
    server=Server()
    switch=Switch(port_count=16)
    dragonfly_fabric=DragonflyFabric(switch, server, 4, 2, 2)  
    assert len(dragonfly_fabric.instances) == 2
    for instance in dragonfly_fabric.instances:
        if instance.name == "server":
            assert instance.count == 36
        elif instance.name == "router":
            assert instance.count == 36
    service = InfraGraphService()
    service.set_graph(dragonfly_fabric)
    # validations
    g = service.get_networkx_graph()
    for node, attrs in g.nodes(data=True):
        assert attrs, f"Node {node} has empty attributes"
    for u, v, attrs in g.edges(data=True):
        assert attrs, f"Edge ({u}, {v}) has empty attributes"
    #print_graph(g)
    #print(networkx.write_network_text(g, vertical_chains=True))

@pytest.mark.asyncio
async def test_dragonfly_dgx():
    """
    Generate and validate the dragonfly topology with dgx as host
    """
    dgx=NvidiaDGX("dgx_a100")
    switch=Switch(port_count=32)
    dragonfly_fabric= DragonflyFabric(switch, dgx, 16, 8, 8)
    assert len(dragonfly_fabric.instances) == 2
    for instance in dragonfly_fabric.instances:
        if instance.name == "dgx_a100":
            assert instance.count == 2064
        elif instance.name == "router":
            assert instance.count == 2064
    service = InfraGraphService()
    service.set_graph(dragonfly_fabric)
    # validations
    g = service.get_networkx_graph() 
    for node, attrs in g.nodes(data=True):
        assert attrs, f"Node {node} has empty attributes"
    for u, v, attrs in g.edges(data=True):
        assert attrs, f"Edge ({u}, {v}) has empty attributes"
    #dump_yaml(dragonfly_fabric, "dragonfly_fabric_with_dgx")
    #print_graph(g)
    #print(networkx.write_network_text(g, vertical_chains=True))   
    #run_visualizer(infrastructure=dragonfly_fabric, output="/mnt/c/Users/anusghos/git/demo/dragonfly_fabric_with_dgx", 
    # hosts="dgx", switches="switch")

@pytest.mark.asyncio
async def test_dragonfly_mi300x():
    """
    Generate and validate the dragonfly topology with mi300x amd device as host
    """
    mi300x= MI300X()
    switch=Switch(port_count=32)
    dragonfly_fabric=DragonflyFabric(switch, mi300x, 16, 8, 8)
    assert len(dragonfly_fabric.instances) == 2
    for instance in dragonfly_fabric.instances:
        if instance.name == "mi300x":
            assert instance.count == 2064
        elif instance.name == "router":
            assert instance.count == 2064
    service=InfraGraphService()
    service.set_graph(dragonfly_fabric)
    # validations
    g = service.get_networkx_graph() 
    for node, attrs in g.nodes(data=True):
        assert attrs, f"Node {node} has empty attributes"
    for u, v, attrs in g.edges(data=True):
        assert attrs, f"Edge ({u}, {v}) has empty attributes"
    #print_graph(g)
    #print(networkx.write_network_text(g, vertical_chains=True)
    #run_visualizer(infrastructure=dragonfly_fabric, output="/mnt/c/Users/anusghos/git/demo/dragonfly_fabric_with_mi300x", hosts="mi300x", switches="switch")


if __name__ == "__main__":
    pytest.main(["-s", __file__])