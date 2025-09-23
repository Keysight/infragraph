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
    print(networkx.write_network_text(g, sources=["host.0.npu.0"], vertical_chains=False))


if __name__ == "__main__":
    pytest.main(["-s", __file__])
