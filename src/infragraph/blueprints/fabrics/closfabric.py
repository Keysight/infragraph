from infragraph import *
from infragraph.blueprints.devices.server import Server
from infragraph.blueprints.devices.generic_switch import Switch
from infragraph.infragraph_service import InfraGraphService


class ClosFabric(Infrastructure):
    """Return a 2 tier clos fabric with the following characteristics:
    - 4 generic servers
    - each generic server with 2 npus and 2 nics
    - 4 leaf switches each with 16 ports
    - 3 spine switch each with 16 ports
    - connectivity between servers and leaf switches is 100G
    - connectivity between servers and spine switch is 400G
    """

    def __init__(self):
        super().__init__(name="closfabric", description="2 Tier Clos Fabric")

        server = Server()
        switch = Switch()
        self.devices.append(server).append(switch)

        hosts = self.instances.add(name="host", device=server.name, count=4)
        leaf_switches = self.instances.add(name="leafsw", device=switch.name, count=4)
        spine_switches = self.instances.add(name="spinesw", device=switch.name, count=3)

        leaf_link = self.links.add(
            name="leaf-link",
            description="Link characteristics for connectivity between servers and leaf switches",
        )
        leaf_link.physical.bandwidth.gigabits_per_second = 100
        spine_link = self.links.add(
            name="spine-link",
            description="Link characteristics for connectivity between leaf switches and spine switches",
        )
        spine_link.physical.bandwidth.gigabits_per_second = 400

        host_component = InfraGraphService.get_component(server, Component.NIC)
        switch_component = InfraGraphService.get_component(switch, Component.PORT)

        # link each host to one leaf switch
        for idx in range(hosts.count):
            edge = self.edges.add(scheme=InfrastructureEdge.ONE2ONE, link=leaf_link.name)
            edge.ep1.instance = f"{hosts.name}[{idx}]"
            edge.ep1.component = host_component.name
            edge.ep2.instance = f"{leaf_switches.name}[{idx}]"
            edge.ep2.component = switch_component.name

        # link every leaf switch to every spine switch
        print()
        for leaf_idx in range(leaf_switches.count):
            for spine_idx in range(spine_switches.count):
                edge = self.edges.add(scheme=InfrastructureEdge.ONE2ONE, link=spine_link.name)
                edge.ep1.instance = f"{leaf_switches.name}[{leaf_idx}]"
                edge.ep1.component = f"{switch_component.name}[{host_component.count + spine_idx}]"
                edge.ep2.instance = f"{spine_switches.name}[{spine_idx}]"
                edge.ep2.component = f"{switch_component.name}[{leaf_idx}]"
