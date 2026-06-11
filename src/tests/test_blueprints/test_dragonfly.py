import pytest
import networkx
from infragraph.infragraph_service import InfraGraphService
from infragraph.blueprints.devices.generic.generic_switch import Switch
from infragraph.blueprints.devices.generic.server import Server
from infragraph.blueprints.fabrics.dragonfly_fabric import DragonflyFabric
from infragraph.visualizer.visualize import run_visualizer

@pytest.mark.asyncio
async def test_dragonfly_fabric():
    """
    Generate and validate the dragonfly topology
    """
    server=Server()
    switch=Switch(port_count=16)

    dragonfly_fabric=DragonflyFabric(switch,server,4,2,2)
    
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
    print(networkx.write_network_text(g, vertical_chains=True))

if __name__ == "__main__":
    pytest.main(["-s", __file__])