import pytest
import conftest
import networkx
from infragraph.infragraph import Api
from infragraph.infragraph_service import InfraGraphService
from infragraph.blueprints.rack_fabric import RackFabric
from infragraph.cx5 import Cx5
from infragraph.dgx import Dgx
from infragraph.server import Server
from infragraph.switch import Switch

def print_graph(graph):
    for node, attrs in graph.nodes(data=True):
        print(f"Node: {node}, Attributes: {attrs}")

    for u, v, attrs in graph.edges(data=True):
        print(f"Edge: ({u}, {v}), Attributes: {attrs}")

@pytest.mark.asyncio
async def test_rack_fabric_1_dgx():
    """From an infragraph device, generate a graph and validate the graph.

    - with a count > 1 there should be no connectivity between device instances
    """
    dgx = Dgx()
    rack_fabric = RackFabric(dgx, 1)
    # create the graph
    service = InfraGraphService()
    service.set_graph(rack_fabric)

    # validations
    g = service.get_networkx_graph()
    print(networkx.write_network_text(g, vertical_chains=True))
    print_graph(g)

@pytest.mark.asyncio
async def test_rack_fabric_3_dgx():
    """From an infragraph device, generate a graph and validate the graph.

    - with a count > 1 there should be no connectivity between device instances
    """
    dgx = Dgx()
    rack_fabric = RackFabric(dgx, 3)
    # create the graph
    service = InfraGraphService()
    service.set_graph(rack_fabric)

    # validations
    g = service.get_networkx_graph()
    print(networkx.write_network_text(g, vertical_chains=True))
    print_graph(g)

@pytest.mark.asyncio
async def test_rack_fabric_2_server():
    """From an infragraph device, generate a graph and validate the graph.

    - with a count > 1 there should be no connectivity between device instances
    """
    server = Server()
    rack_fabric = RackFabric(server, 2)
    # create the graph
    service = InfraGraphService()
    service.set_graph(rack_fabric)

    # validations
    g = service.get_networkx_graph()
    print(networkx.write_network_text(g, vertical_chains=True))
    print_graph(g)

if __name__ == "__main__":
    pytest.main(["-s", __file__])
