import pytest
import networkx
from infragraph.infragraph import Api
from infragraph.infragraph_service import InfraGraphService
from infragraph.blueprints.devices.cisco.ucs_c88_5A_m8 import cisco_ucsc_885A_m8


@pytest.mark.asyncio
@pytest.mark.parametrize("count", [1, 2])
@pytest.mark.parametrize(
    "device",
    [
        cisco_ucsc_885A_m8(xpu_type="hgx_h100"),
        cisco_ucsc_885A_m8(xpu_type="hgx_h200"),
        cisco_ucsc_885A_m8(xpu_type="mi300x"),
        cisco_ucsc_885A_m8(xpu_type="mi350x"),
    ],
)
async def test_ucsc_885A_m8(count, device):
    """From a Cisco UCS C885A M8 device, generate a graph and validate the graph.

    - with a count > 1 there should be no connectivity between device instances
    """
    # create the graph
    device.validate()
    infrastructure = Api().infrastructure()
    infrastructure.devices.append(device)
    infrastructure.instances.add(name=device.name, device=device.name, count=count)
    service = InfraGraphService()
    service.set_graph(infrastructure)

    # validations
    g = service.get_networkx_graph()
    print(f"\ndevice {device.name} is a {g}")
    print(networkx.write_network_text(g, vertical_chains=True))


if __name__ == "__main__":
    pytest.main(["-s", __file__])