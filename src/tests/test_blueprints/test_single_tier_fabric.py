import pytest
import networkx
from infragraph.infragraph_service import InfraGraphService
from infragraph.blueprints.fabrics.single_tier_fabric import SingleTierFabric
from infragraph.blueprints.devices.nvidia.dgx import Dgx
from infragraph.blueprints.devices.server import Server

def print_graph(graph):
    for node, attrs in graph.nodes(data=True):
        print(f"Node: {node}, Attributes: {attrs}")

    for u, v, attrs in graph.edges(data=True):
        print(f"Edge: ({u}, {v}), Attributes: {attrs}")

@pytest.mark.asyncio
async def test_single_tier_fabric_one_dgx():
    """
    Generate a single tier fabric with 1 dgx host and validate the infragraph
    """
    dgx = Dgx()
    single_tier_fabric = SingleTierFabric(dgx, 1)
    # create the graph
    service = InfraGraphService()
    service.set_graph(single_tier_fabric)

    # validations
    g = service.get_networkx_graph()
    print(networkx.write_network_text(g, vertical_chains=True))
    print_graph(g)

@pytest.mark.asyncio
async def test_single_tier_fabric_multi_dgx():
    """
    Generate a single tier fabric with multi dgx host and validate the infragraph
    """
    dgx = Dgx()
    single_tier_fabric = SingleTierFabric(dgx, 3)
    # create the graph
    service = InfraGraphService()
    service.set_graph(single_tier_fabric)

    # validations
    g = service.get_networkx_graph()
    print(networkx.write_network_text(g, vertical_chains=True))
    print_graph(g)

@pytest.mark.asyncio
async def test_single_tier_fabric_multi_server():
    """
    Generate a single tier fabric with multi server host and validate the infragraph
    """
    server = Server()
    single_tier_fabric = SingleTierFabric(server, 2)
    # create the graph
    service = InfraGraphService()
    service.set_graph(single_tier_fabric)

    # validations
    g = service.get_networkx_graph()
    print(networkx.write_network_text(g, vertical_chains=True))
    print_graph(g)

if __name__ == "__main__":
    pytest.main(["-s", __file__])
