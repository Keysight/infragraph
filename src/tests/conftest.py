import pytest
import sys
import os

if __package__ in ["", None]:
    # this path will be used instead of an installed package when running tests
    # within the development environment src/infragraph directory
    sys.path.insert(
        0,
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
    )
    print(f"Testing code using src\n{sys.path}")


from infragraph import Infrastructure, Component
from infragraph.server import Server
from infragraph.switch import Switch
from infragraph.infragraph_service import InfraGraphService


@pytest.fixture
def closfabric() -> Infrastructure:
    """Return a 2 tier clos fabric with the following characteristics:
    - 4 generic servers
    - each generic server with 2 npus and 2 nics
    - 4 leaf switches each with 16 ports
    - 3 spine switch each with 16 ports
    - connectivity between servers and leaf switches is 100G
    - connectivity between servers and spine switch is 400G
    """
    infra = Infrastructure(name="clos-fabric", description="2 Tier Clos Fabric")

    server = Server()
    switch = Switch()
    infra.devices.append(server).append(switch)

    hosts = infra.instances.add(name="host", device=server.name, count=4)
    leaf_switches = infra.instances.add(name="leaf", device=switch.name, count=4)
    spine_switches = infra.instances.add(name="spine", device=switch.name, count=3)

    leaf_link = infra.links.add(
        name="leaf-link",
        description="Link characteristics for connectivity between servers and leaf switches",
    )
    leaf_link.physical.bandwidth.gigabits_per_second = 100
    spine_link = infra.links.add(
        name="spine-link",
        description="Link characteristics for connectivity between leaf switches and spine switches",
    )
    spine_link.physical.bandwidth.gigabits_per_second = 400

    # link the hosts to the leaf switches
    for idx in range(hosts.count):
        edge = infra.edges.add(many2many=True, link=leaf_link.name)
        edge.ep1.instance = f"{hosts.name}[{idx}]"
        edge.ep1.component = InfraGraphService.get_component(server, Component.NIC).name
        edge.ep2.instance = f"{leaf_switches.name}[{idx}]"
        edge.ep2.component = InfraGraphService.get_component(switch, Component.PORT).name

    # link every leaf switch to every spine switch
    switch_component = InfraGraphService.get_component(server, Component.NIC).name
    for idx in range(leaf_switches.count):
        edge = infra.edges.add(many2many=True, link=spine_link.name)
        edge.ep1.instance = f"{leaf_switches.name}[{idx}]"
        edge.ep1.component = f"{switch_component}[{hosts.count + idx}]"
        edge.ep2.instance = f"{spine_switches.name}"
        edge.ep2.component = f"{switch_component}[{idx}]"

    return infra
