from infragraph import *
from infragraph.infragraph_service import InfraGraphService
import itertools

from infragraph.blueprints.devices.generic.server import Server
from infragraph.blueprints.devices.generic.generic_switch import Switch


class DeBruijnFabricWithAccessLayer(Infrastructure):
    """
    De Bruijn Fabric with Access Layer

    Inputs:
        switch : fabric switch device
        server : host device
        order  : order of DeBruijn graph

    Derived:
        sp = switch radix
        degree = sp / 8

    Fabric Switch Ports
    -------------------
    0..degree-1          primary outgoing
    degree..2degree-1    redundant outgoing
    2degree..3degree-1   primary incoming
    3degree..4degree-1   redundant incoming
    4degree..sp-1        access switch uplinks

    Access Switch Ports
    -------------------
    0..(sp/2 -1)         hosts
    remaining            fabric switch connection + unused
    """

    def __init__(self, switch: Switch, server: Server, order: int):

        super().__init__(
            name="debruijn-fabric-access",
            description=f"DeBruijn Fabric with Access Layer (order={order})"
        )

        self.order = order

        # devices
        self.devices.append(switch)
        self.devices.append(server)

        # components
        switch_port = InfraGraphService.get_component(switch, Component.PORT)
        host_nic = InfraGraphService.get_component(server, Component.NIC)

        sp = switch_port.count
        hn = host_nic.count

        if sp % 8 != 0:
            raise ValueError("Switch radix must be divisible by 8")

        degree = sp // 8
        self.degree = degree

        # host capacity
        host_ports = sp // 2

        if host_ports % hn != 0:
            raise ValueError("Host NIC count must divide available host ports")

        hosts_per_access = host_ports // hn

        # alphabet
        alphabet = [str(i) for i in range(degree)]

        # DeBruijn nodes
        nodes = [''.join(p) for p in itertools.product(alphabet, repeat=order)]
        self.nodes = nodes

        num_switches = len(nodes)

        # Fabric switches
        fabric_switches = self.instances.add(
            name="fabric_switch",
            device=switch.name,
            count=num_switches
        )

        # Access switch device
        access_switch = Switch(port_count=sp)
        self.devices.append(access_switch)

        access_port = InfraGraphService.get_component(access_switch, Component.PORT)

        # Access switches
        access_switches = self.instances.add(
            name="access_switch",
            device=access_switch.name,
            count=num_switches
        )

        # Hosts
        total_hosts = num_switches * hosts_per_access

        hosts = self.instances.add(
            name="host",
            device=server.name,
            count=total_hosts
        )

        node_index = {node: i for i, node in enumerate(nodes)}

        # links
        fabric_link = self.links.add(
            name="fabric-link",
            description="DeBruijn fabric connectivity"
        )
        fabric_link.physical.bandwidth.gigabits_per_second = 400

        access_link = self.links.add(
            name="access-uplink",
            description="Access switch to fabric switch"
        )
        access_link.physical.bandwidth.gigabits_per_second = 200

        host_link = self.links.add(
            name="host-link",
            description="Host to access switch"
        )
        host_link.physical.bandwidth.gigabits_per_second = 100

        
        # Fabric edges (with redundancy)

        for node in nodes:

            src_idx = node_index[node]

            for i, digit in enumerate(alphabet):

                next_node = node[1:] + digit
                dst_idx = node_index[next_node]

                # primary fabric link
                edge = self.edges.add(
                    scheme=InfrastructureEdge.ONE2ONE,
                    link=fabric_link.name
                )

                edge.ep1.instance = f"{fabric_switches.name}[{src_idx}]"
                edge.ep1.component = f"{switch_port.name}[{i}]"

                edge.ep2.instance = f"{fabric_switches.name}[{dst_idx}]"
                edge.ep2.component = f"{switch_port.name}[{i + 2*degree}]"

                # redundant fabric link
                edge = self.edges.add(
                    scheme=InfrastructureEdge.ONE2ONE,
                    link=fabric_link.name
                )

                edge.ep1.instance = f"{fabric_switches.name}[{src_idx}]"
                edge.ep1.component = f"{switch_port.name}[{i + degree}]"

                edge.ep2.instance = f"{fabric_switches.name}[{dst_idx}]"
                edge.ep2.component = f"{switch_port.name}[{i + 3*degree}]"

        
        # Access → Fabric links

        uplink_start = 4 * degree

        for idx in range(num_switches):

            edge = self.edges.add(
                scheme=InfrastructureEdge.ONE2ONE,
                link=access_link.name
            )

            edge.ep1.instance = f"{access_switches.name}[{idx}]"
            edge.ep1.component = f"{access_port.name}[0]"

            edge.ep2.instance = f"{fabric_switches.name}[{idx}]"
            edge.ep2.component = f"{switch_port.name}[{uplink_start}]"

       
        # Hosts → Access switches

        host_index = 0

        for sw_idx in range(num_switches):

            for h in range(hosts_per_access):

                for nic in range(hn):

                    port_index = h * hn + nic

                    edge = self.edges.add(
                        scheme=InfrastructureEdge.ONE2ONE,
                        link=host_link.name
                    )

                    edge.ep1.instance = f"{hosts.name}[{host_index}]"
                    edge.ep1.component = f"{host_nic.name}[{nic}]"

                    edge.ep2.instance = f"{access_switches.name}[{sw_idx}]"
                    edge.ep2.component = f"{access_port.name}[{port_index}]"

                host_index += 1