from infragraph import *
from infragraph.infragraph_service import InfraGraphService
import itertools


class MultiHostDeBruijnFabric(Infrastructure):
    """
    DeBruijn Fabric with Multiple Hosts per Switch + Redundant Fabric Links

    Inputs
    switch : fabric switch
    server : host device
    order  : DeBruijn order

    Ports
        0..d-1      primary outgoing
        d..2d-1     redundant outgoing
        2d..3d-1    primary incoming
        3d..4d-1    redundant incoming
        4d..switch_port.count-1    host ports
    """

    def __init__(self, switch: Device, server: Device, order: int):
        super().__init__(
            name="multi-host-redundant-debruijn",
            description=f"DeBruijn Fabric (k={order})",
        )
        
        self.devices.append(switch)
        self.devices.append(server)

        switch_port = InfraGraphService.get_component(switch, Component.PORT)
        host_nic = InfraGraphService.get_component(server, Component.NIC)

        degree = switch_port.count // 8
        host_ports = switch_port.count // 2

        if degree < 1:
            raise ValueError("Not enough switch ports")

        if host_ports % host_nic.count != 0:
            raise ValueError(
                f"Host NICs ({host_nic.count}) must divide available host ports ({host_ports})"
            )

        # Each access switch dedicates half of its ports to hosts
        # host count is based on NICs per host
        hosts_per_switch = host_ports // host_nic.count

        # Build de bruijn node labels.
        # For degree d and order n, the fabric has d^n switches, each having unique label
        alphabet = [str(i) for i in range(degree)]
        nodes = ["".join(p) for p in itertools.product(alphabet, repeat=order)]
        num_switches = len(nodes)

        # Create fabric switches and Hosts
        switches = self.instances.add(name="switch", device=switch.name, count=num_switches)
        hosts = self.instances.add(name="host", device=server.name, count=num_switches * hosts_per_switch)
        node_index = {node: i for i, node in enumerate(nodes)}

        # Added links
        # fabric link connects fabric switches
        # host links connects hosts with fabric switches
        fabric_link = self.links.add(name="fabric-link", description="DeBruijn connectivity")
        fabric_link.physical.bandwidth.gigabits_per_second = 400
        host_link = self.links.add(name="host-link", description="Host to switch connectivity")
        host_link.physical.bandwidth.gigabits_per_second = 100

        # Added de bruijn fabric edges
        # Routing - shifting node label left and appending each alphabet digit of destination node
        # two types of link - primary link, redundant link
        for node in nodes:
            src_idx = node_index[node]
            for i, digit in enumerate(alphabet):
                next_node = node[1:] + digit
                dst_idx = node_index[next_node]

                # Primary link
                edge = self.edges.add(scheme=InfrastructureEdge.ONE2ONE, link=fabric_link.name)
                edge.ep1.instance = f"{switches.name}[{src_idx}]"
                edge.ep1.component = f"{switch_port.name}[{i}]"
                edge.ep2.instance = f"{switches.name}[{dst_idx}]"
                edge.ep2.component = f"{switch_port.name}[{i + 2*degree}]"

                # Redundant link
                edge = self.edges.add(scheme=InfrastructureEdge.ONE2ONE, link=fabric_link.name)
                edge.ep1.instance = f"{switches.name}[{src_idx}]"
                edge.ep1.component = f"{switch_port.name}[{i + degree}]"
                edge.ep2.instance = f"{switches.name}[{dst_idx}]"
                edge.ep2.component = f"{switch_port.name}[{i + 3*degree}]"

        # Attach hosts to access switch
        host_port_start = 4 * degree
        host_global_idx = 0
        for sw_idx in range(num_switches):
            for h in range(hosts_per_switch):
                for nic in range(host_nic.count):
                    port_offset = h * host_nic.count + nic
                    edge = self.edges.add(scheme=InfrastructureEdge.ONE2ONE, link=host_link.name)
                    edge.ep1.instance = f"{hosts.name}[{host_global_idx}]"
                    edge.ep1.component = f"{host_nic.name}[{nic}]"
                    edge.ep2.instance = f"{switches.name}[{sw_idx}]"
                    edge.ep2.component = (f"{switch_port.name}[{host_port_start + port_offset}]")
                host_global_idx += 1
