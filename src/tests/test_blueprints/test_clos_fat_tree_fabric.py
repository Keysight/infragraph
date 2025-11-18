import pytest
import networkx
from infragraph.infragraph_service import InfraGraphService
from infragraph.blueprints.fabrics.clos_fat_tree_fabric import ClosFatTreeFabric
from infragraph.blueprints.devices.dgx import Dgx
from infragraph.blueprints.devices.server import Server
from infragraph.blueprints.devices.generic_switch import Switch

def print_graph(graph):
    for node, attrs in graph.nodes(data=True):
        print(f"Node: {node}, Attributes: {attrs}")

    for u, v, attrs in graph.edges(data=True):
        print(f"Edge: ({u}, {v}), Attributes: {attrs}")

@pytest.mark.asyncio
async def test_two_tier_clos_fat_tree_fabric_with_dgx():
    """
    Generate a single tier fabric with 1 dgx host and validate the infragraph
    """
    dgx = Dgx()
    switch = Switch(port_count=16)
    clos_fat_tree = ClosFatTreeFabric(switch, dgx, 2, [])
    # create the graph
    service = InfraGraphService()
    service.set_graph(clos_fat_tree)

    # validations
    g = service.get_networkx_graph()
    print(networkx.write_network_text(g, vertical_chains=True))
    print_graph(g)

@pytest.mark.asyncio
async def test_two_tier_clos_fat_tree_fabric_with_server():
    """
    Generate a single tier fabric with 1 dgx host and validate the infragraph
    """
    server = Server()
    switch = Switch(port_count=8)
    clos_fat_tree = ClosFatTreeFabric(switch, server, 2, [])
    # create the graph
    service = InfraGraphService()
    service.set_graph(clos_fat_tree)

    # validations
    g = service.get_networkx_graph()
    print(networkx.write_network_text(g, vertical_chains=True))
    print_graph(g)

# @pytest.mark.asyncio
# async def test_three_tier_clos_fat_tree_fabric_with_server():
#     """
#     Generate a single tier fabric with 1 dgx host and validate the infragraph
#     """
#     server = Server()
#     switch = Switch(port_count=4)
#     clos_fat_tree = ClosFatTreeFabric(switch, server, 3, [])
#     # create the graph
#     service = InfraGraphService()
#     service.set_graph(clos_fat_tree)

#     # validations
#     g = service.get_networkx_graph()
#     print(networkx.write_network_text(g, vertical_chains=True))
#     print_graph(g)

if __name__ == "__main__":
    pytest.main(["-s", __file__])
