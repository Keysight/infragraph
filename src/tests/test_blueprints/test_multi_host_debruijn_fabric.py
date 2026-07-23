from infragraph.infragraph_service import InfraGraphService
from infragraph.blueprints.devices.generic.server import Server
from infragraph.blueprints.devices.generic.generic_switch import Switch
from infragraph.blueprints.fabrics.multi_host_debruijn_fabric import MultiHostDeBruijnFabric
from infragraph.blueprints.devices.nvidia.dgx import NvidiaDGX
import networkx
import pytest

DGX_PROFILES = [
    "dgx1",
    "dgx2",
    "dgx_a100",
    "dgx_h100",
    "dgx_gb200",
]
@pytest.mark.asyncio
async def test_debruijn_multi_host_fabric():
    """
    Generate a debruijn fabric with multiple hosts per switch

    """
    switch = Switch(port_count=16)
    server = Server()
    fabric = MultiHostDeBruijnFabric(switch, server, 3)

    service = InfraGraphService()
    service.set_graph(fabric)

    graph = service.get_networkx_graph()
    # print(networkx.write_network_text(graph, vertical_chains=True))

@pytest.mark.asyncio
@pytest.mark.parametrize("dgx_profile", DGX_PROFILES)
async def test_debruijn_multi_host_fabric_with_dgx(dgx_profile):
    """
    Generate a debruijn fabric with each supported DGX device

    """
    switch = Switch(port_count=16)
    dgx = NvidiaDGX(dgx_profile)
    fabric = MultiHostDeBruijnFabric(switch, dgx, 3)

    service = InfraGraphService()
    service.set_graph(fabric)

    graph = service.get_networkx_graph()
    # print(networkx.write_network_text(graph, vertical_chains=True))


if __name__ == "__main__":
    pytest.main(["-s", __file__])
