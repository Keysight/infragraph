from infragraph import *
from infragraph.infragraph_service import InfraGraphService
import itertools

class HybridDeBruijnFabric(Infrastructure):
    """
    A Hybrid of De Bruijn Fabric and Clos Fabric with Access Layer of Rack Switches

    Inputs:
        switch : fabric switch device
        server : host device
        order  : order of DeBruijn graph

    Derived:
        switch_port.count = switch radix
        degree = switch_port.count / 8

    Fabric Switch Ports:
    0..degree-1          primary outgoing
    degree..2degree-1    redundant outgoing
    2degree..3degree-1   primary incoming
    3degree..4degree-1   redundant incoming
    4degree..switch_port.count-1   access switch uplinks

    Access Switch Ports:
    0..(switch_port.count/2 -1)         hosts
    remaining            fabric switch connection + unused
    
    """

    def __init__(self, switch: Device, server: Device, order: int):
        super().__init__(
            name="hybrid-debruijn-fabric",
            description=f"DeBruijn Fabric With Rack Switches(order={order})",
        )

        switch_port = InfraGraphService.get_component(switch, Component.PORT)
        host_nic = InfraGraphService.get_component(server, Component.NIC)

        # The switch radix must divide evenly across the full port plan:
        # half the ports are for fabric links and half are for host/access links;
        # within the fabric half, ports are split into incoming and outgoing;
        # within both incoming and outgoing groups, ports are split again into
        # primary and redundant links. Therefore switch port must be divisible by 8 (2*2*2)
        if switch_port.count % 8 != 0:
            raise ValueError("Switch radix must be divisible by 8")

        # degree of graph = connected neighbour nodes
        degree = switch_port.count // 8
        host_ports = switch_port.count // 2

        if degree < 1:
            raise ValueError("Not enough switch ports")
        
        if host_ports % host_nic.count != 0:
            raise ValueError("Host NIC count must divide available host ports")

        # Each access switch dedicates half of its ports to hosts
        # host count is based on NICs per host
        hosts_per_access_switch = host_ports // host_nic.count

        self.devices.append(switch)
        self.devices.append(server)

        # Build de bruijn node labels.
        # For degree d and order n, the fabric has d^n switches, each having unique label
        alphabet = [str(i) for i in range(degree)]
        nodes = ["".join(p) for p in itertools.product(alphabet, repeat=order)]
        num_switches = len(nodes)

        # Create one fabric switch and one access switch per de bruijn node
        fabric_switches = self.instances.add(name="fabric_switch", device=switch.name, count=num_switches)
        access_switches = self.instances.add(name="access_switch", device=switch.name, count=num_switches)

        # Create Hosts per access/rack switch
        total_hosts = num_switches * hosts_per_access_switch
        hosts = self.instances.add(name="host", device=server.name, count=total_hosts)
        node_index = {node: i for i, node in enumerate(nodes)}

        # Create links
        # fabric link connects fabric switches
        # access links connects fabric switch and access switch
        fabric_link = self.links.add(name="fabric-link", description="DeBruijn fabric connectivity")        
        fabric_link.physical.bandwidth.gigabits_per_second = 400
        access_link = self.links.add(name="access-uplink", description="Access switch to fabric switch")
        access_link.physical.bandwidth.gigabits_per_second = 200
        host_link = self.links.add(name="host-link", description="Host to access switch")
        host_link.physical.bandwidth.gigabits_per_second = 100

        # Added de bruijn fabric edges
        # Routing - shifting node label left and appending each alphabet digit of destination node
        # two types of link - primary link, redundant link
        for node in nodes:
            src_idx = node_index[node]
            for i, digit in enumerate(alphabet):
                next_node = node[1:] + digit
                dst_idx = node_index[next_node]
                
                # primary link
                edge = self.edges.add(scheme=InfrastructureEdge.ONE2ONE, link=fabric_link.name)               
                edge.ep1.instance = f"{fabric_switches.name}[{src_idx}]"
                edge.ep1.component = f"{switch_port.name}[{i}]"
                edge.ep2.instance = f"{fabric_switches.name}[{dst_idx}]"
                edge.ep2.component = f"{switch_port.name}[{i + 2*degree}]"

                # redundant link
                edge = self.edges.add(scheme=InfrastructureEdge.ONE2ONE, link=fabric_link.name)
                edge.ep1.instance = f"{fabric_switches.name}[{src_idx}]"
                edge.ep1.component = f"{switch_port.name}[{i + degree}]"
                edge.ep2.instance = f"{fabric_switches.name}[{dst_idx}]"
                edge.ep2.component = f"{switch_port.name}[{i + 3*degree}]"

        # Added access switch to fabric switch edges
        uplink_start = 4 * degree
        for idx in range(num_switches):
            edge = self.edges.add(scheme=InfrastructureEdge.ONE2ONE, link=access_link.name)
            edge.ep1.instance = f"{access_switches.name}[{idx}]"
            edge.ep1.component = f"{switch_port.name}[0]"
            edge.ep2.instance = f"{fabric_switches.name}[{idx}]"
            edge.ep2.component = f"{switch_port.name}[{uplink_start}]"

        # Attach hosts to access switch
        host_index = 0
        for sw_idx in range(num_switches):
            for h in range(hosts_per_access_switch):
                for nic in range(host_nic.count):
                    port_index = h * host_nic.count + nic
                    edge = self.edges.add(scheme=InfrastructureEdge.ONE2ONE, link=host_link.name)
                    edge.ep1.instance = f"{hosts.name}[{host_index}]"
                    edge.ep1.component = f"{host_nic.name}[{nic}]"
                    edge.ep2.instance = f"{access_switches.name}[{sw_idx}]"
                    edge.ep2.component = f"{switch_port.name}[{port_index}]"                   
                host_index += 1

