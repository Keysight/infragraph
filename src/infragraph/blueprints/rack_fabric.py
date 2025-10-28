from infragraph import *
from infragraph.server import Server
from infragraph.switch import Switch
from infragraph.infragraph_service import InfraGraphService


class RackFabric(Infrastructure):
    """Return a single tier rack fabric with the following characteristics:
    Inputs:
        - server (device instance)
        - server count - 'x'
    Output:
        - servers with 'x' count
        - a generic rack switch with n ports where:
            n = server count 'x' * nics in each server
        - connectivity between servers and rack switches is 100G
    """

    def __init__(self, server: Device, server_count: int):
        super().__init__(name="rack-fabric", description="Single Tier Rack Fabric")

        server_nic_component = InfraGraphService.get_component(server, Component.NIC)
        total_ports = server_nic_component.count * server_count

        switch = Switch(total_ports)
        self.devices.append(server).append(switch)
        
        hosts = self.instances.add(name=server.name, device=server.name, count=server_count)
        rack_switch = self.instances.add(name="rack_switch", device=switch.name, count=1)

        rack_link = self.links.add(
            name="rack-link",
            description="Link characteristics for connectivity between servers and leaf switches",
        )
        rack_link.physical.bandwidth.gigabits_per_second = 100

        
        switch_component = InfraGraphService.get_component(switch, Component.PORT)

        # link each host to one leaf switch
        for idx in range(total_ports):
            host_index = idx // server_nic_component.count
            host_component_index = idx % server_nic_component.count
            edge = self.edges.add(
                scheme=InfrastructureEdge.ONE2ONE, link=rack_link.name
            )
            edge.ep1.instance = f"{hosts.name}[{host_index}]"
            edge.ep1.component = f"{server_nic_component.name}[{host_component_index}]"
            edge.ep2.instance = f"{rack_switch.name}[0]"
            edge.ep2.component = f"{switch_component.name}[{idx}]"

