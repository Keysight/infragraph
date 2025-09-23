import pytest
import conftest
import networkx
from infragraph import *
from infragraph.infragraph_service import InfraGraphService


@pytest.mark.asyncio
async def test_infrastructure(closfabric: Infrastructure):
    """Validate the device, generate a graph from a device and validate the graph."""
    service = InfraGraphService()
    service.set_graph(closfabric.serialize())
    g = service.get_networkx_graph()
    print(f"\nInfrastructure is a {g}")
    print(networkx.write_network_text(g, vertical_chains=True))


if __name__ == "__main__":
    pytest.main(["-s", __file__])
