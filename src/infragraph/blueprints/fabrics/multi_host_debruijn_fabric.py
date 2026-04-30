from infragraph import *
from infragraph.infragraph_service import InfraGraphService
import itertools

from infragraph.blueprints.devices.generic.server import Server
from infragraph.blueprints.devices.generic.generic_switch import Switch


class DeBruijnFabricWithMultiHost(Infrastructure):
    """
    DeBruijn Fabric with Multiple Hosts per Switch + Redundant Fabric Links

    Inputs
    ------
    switch : fabric switch
    server : host device
    order  : DeBruijn order

    Ports

        0..d-1      primary outgoing
        d..2d-1     redundant outgoing
        2d..3d-1    primary incoming
        3d..4d-1    redundant incoming
        4d..sp-1    host ports
    """

    def __init__(self, switch: Switch, server: Server, order: int):

        super().__init__(
            name="multi-host-redundant-debruijn",
            description=f"DeBruijn Fabric (k={order})"
        )

        self.order = order

        # add devices
        self.devices.append(switch)
        self.devices.append(server)

        # components
        switch_port = InfraGraphService.get_component(switch, Component.PORT)
        host_nic = InfraGraphService.get_component(server, Component.NIC)

        sp = switch_port.count
        hn = host_nic.count

        degree = sp // 8
        if degree < 1:
            raise ValueError("Not enough switch ports")

        # host ports = half of total
        host_ports = sp // 2

        if host_ports % hn != 0:
            raise ValueError(
                f"Host NICs ({hn}) must divide available host ports ({host_ports})"
            )

        hosts_per_switch = host_ports // hn
        self.degree = degree

        # alphabet
        alphabet = [str(i) for i in range(degree)]

        # DeBruijn nodes
        nodes = [''.join(p) for p in itertools.product(alphabet, repeat=order)]
        self.nodes = nodes

        num_switches = len(nodes)

        # instances
        switches = self.instances.add(
            name="switch",
            device=switch.name,
            count=num_switches
        )

        total_hosts = num_switches * hosts_per_switch

        hosts = self.instances.add(
            name="host",
            device=server.name,
            count=total_hosts
        )

        node_index = {node: i for i, node in enumerate(nodes)}

        # links
        fabric_link = self.links.add(
            name="fabric-link",
            description="DeBruijn connectivity"
        )
        fabric_link.physical.bandwidth.gigabits_per_second = 400

        host_link = self.links.add(
            name="host-link",
            description="Host to switch connectivity"
        )
        host_link.physical.bandwidth.gigabits_per_second = 100

        
        # Fabric edges
        for node in nodes:

            src_idx = node_index[node]

            for i, digit in enumerate(alphabet):

                next_node = node[1:] + digit
                dst_idx = node_index[next_node]

                # Primary link
                edge = self.edges.add(
                    scheme=InfrastructureEdge.ONE2ONE,
                    link=fabric_link.name
                )
                edge.ep1.instance = f"{switches.name}[{src_idx}]"
                edge.ep1.component = f"{switch_port.name}[{i}]"

                edge.ep2.instance = f"{switches.name}[{dst_idx}]"
                edge.ep2.component = f"{switch_port.name}[{i + 2*degree}]"

                # Redundant link
                edge = self.edges.add(
                    scheme=InfrastructureEdge.ONE2ONE,
                    link=fabric_link.name
                )
                edge.ep1.instance = f"{switches.name}[{src_idx}]"
                edge.ep1.component = f"{switch_port.name}[{i + degree}]"

                edge.ep2.instance = f"{switches.name}[{dst_idx}]"
                edge.ep2.component = f"{switch_port.name}[{i + 3*degree}]"

        
        # Host edges (MULTIPLE HOST)
        host_port_start = 4 * degree
        host_global_idx = 0

        for sw_idx in range(num_switches):

            for h in range(hosts_per_switch):

                for nic in range(hn):

                    edge = self.edges.add(
                        scheme=InfrastructureEdge.ONE2ONE,
                        link=host_link.name
                    )

                    edge.ep1.instance = f"{hosts.name}[{host_global_idx}]"
                    edge.ep1.component = f"{host_nic.name}[{nic}]"

                    port_offset = h * hn + nic

                    edge.ep2.instance = f"{switches.name}[{sw_idx}]"
                    edge.ep2.component = f"{switch_port.name}[{host_port_start + port_offset}]"

                host_global_idx += 1