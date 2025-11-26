from infragraph import *
from infragraph.blueprints.devices.generic_switch import Switch
from infragraph.infragraph_service import InfraGraphService


class SingleTierFabric(Infrastructure):
    """Return a single tier rack fabric with the following characteristics:
    Inputs:
        - server (device instance)
        - server count - 'x'
        - bandwidth in Gbps
    Output:
        - servers with 'x' count
        - a generic rack switch with n ports where:
            n = server count 'x' * nics in each server
        - connectivity between switch and hosts is the provided bandwidth
    """

    def __init__(self, server: Device, server_count: int, bandwidth: int = 100):
        super().__init__(name="single-tier-fabric", description="Single Tier Fabric")

        server_nic_component = InfraGraphService.get_component(server, Component.NIC)
        total_ports = server_nic_component.count * server_count

        switch_device = Switch(total_ports)
        self.devices.append(server).append(switch_device)
        
        hosts = self.instances.add(name=server.name, device=server.name, count=server_count)
        switch_instance = self.instances.add(name="switch", device=switch_device.name, count=1)

        switch_link = self.links.add(
            name="switch-link",
            description="Link characteristics for connectivity between servers and rack switches",
        )
        switch_link.physical.bandwidth.gigabits_per_second = bandwidth

        switch_component = InfraGraphService.get_component(switch_device, Component.PORT)

        # link each host to one leaf switch
        for idx in range(total_ports):
            host_index = idx // server_nic_component.count
            host_component_index = idx % server_nic_component.count
            edge = self.edges.add(
                scheme=InfrastructureEdge.ONE2ONE, link=switch_link.name
            )
            edge.ep1.instance = f"{hosts.name}[{host_index}]"
            edge.ep1.component = f"{server_nic_component.name}[{host_component_index}]"
            edge.ep2.instance = f"{switch_instance.name}[0]"
            edge.ep2.component = f"{switch_component.name}[{idx}]"

