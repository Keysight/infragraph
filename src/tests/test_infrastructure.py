import pytest
import conftest
import networkx
from infragraph import *
from infragraph.closfabric import ClosFabric
from infragraph.infragraph_service import InfraGraphService


@pytest.mark.asyncio
async def test_infrastructure():
    """Validate the device, generate a graph from a device and validate the graph."""
    # create the graph
    service = InfraGraphService()
    service.set_graph(ClosFabric())

    # validations
    g = service.get_networkx_graph()
    print(f"\nInfrastructure is a {g}")
    print(networkx.write_network_text(g, vertical_chains=True))


if __name__ == "__main__":
    pytest.main(["-s", __file__])
