from infragraph import *
from infragraph.infragraph_service import InfraGraphService
from infragraph.infragraph import *


class DragonflyFabric(Infrastructure):
    """Return a balanced Dragonfly fabric.

    A balanced Dragonfly satisfies a == 2p == 2h, where:
        - a = routers per group
        - p = host/terminal ports per router
        - h = global/inter-group ports per router
    Total groups = a*h + 1 (maximum supported by a balanced Dragonfly).

    Each router uses p + (a-1) + h ports:
        ports [0, p)                       -> hosts
        ports [p, p + a - 1)               -> intra-group peers
        ports [p + a - 1, p + a - 1 + h)   -> global (inter-group)

    Inputs:
        - switch    
        - host      
        - a, p, h
        - bandwidth
    """

    def __init__(
        self,
        switch: Device,
        host: Device,
        a: int,
        p: int,
        h: int,
        bandwidth=None,
    ):
        super().__init__(
            name="dragonfly-fabric",
            description="Balanced Dragonfly Fabric",
        )

        # balanced dragonfly constraint
        if not (a == 2 * p == 2 * h):
            raise ValueError(
                f"Balanced Dragonfly requires a == 2p == 2h; got a={a}, p={p}, h={h}"
            )

        switch_port_component = InfraGraphService.get_component(switch, Component.PORT)
        host_nic_component = InfraGraphService.get_component(host, Component.NIC)

        ports_per_router = p + (a - 1) + h
        if switch_port_component.count < ports_per_router:
            raise ValueError(
                f"Switch needs at least {ports_per_router} ports "
                f"(p + (a-1) + h); got {switch_port_component.count}"
            )

        if p % host_nic_component.count != 0:
            raise ValueError(
                f"Host NIC count ({host_nic_component.count}) does not divide "
                f"terminal ports per router (p={p}) evenly"
            )

        # bandwidth defaults: [host_switch, intra, inter]
        if bandwidth is None:
            bandwidth = [100, 100, 100]
        assert len(bandwidth) == 3, "bandwidth list must have 3 entries"

        # counts
        total_groups = a * h + 1
        routers_per_group = a
        total_switches = total_groups * routers_per_group
        hosts_per_router = p // host_nic_component.count
        total_hosts = total_groups * routers_per_group * hosts_per_router

        # port-range bases on each router
        intra_port_base = p
        global_port_base = p + (a - 1)

        # devices 
        self.devices.append(host).append(switch)
        host_instance = self.instances.add(
            name=host.name, device=host.name, count=total_hosts
        )
        switch_instance = self.instances.add(
            name="router", device=switch.name, count=total_switches
        )

        # links 
        host_switch_link = self.links.add(
            name="host_switch_link",
            description="Link between host and router (terminal)",
        )
        host_switch_link.physical.bandwidth.gigabits_per_second = bandwidth[0]

        intra_switch_link = self.links.add(
            name="intra_switch_link",
            description="Link between routers within the same group",
        )
        intra_switch_link.physical.bandwidth.gigabits_per_second = bandwidth[1]

        inter_switch_link = self.links.add(
            name="inter_switch_link",
            description="Link between routers in different groups (global)",
        )
        inter_switch_link.physical.bandwidth.gigabits_per_second = bandwidth[2]

        # host and router  
        for group_idx in range(total_groups):
            for local_router in range(routers_per_group):
                router_idx = group_idx * routers_per_group + local_router
                terminal_port = 0
                for host_in_rack in range(hosts_per_router):
                    host_idx = router_idx * hosts_per_router + host_in_rack
                    for nic_idx in range(host_nic_component.count):
                        edge = self.edges.add(
                            scheme=InfrastructureEdge.ONE2ONE,
                            link=host_switch_link.name,
                        )
                        edge.ep1.instance = f"{host_instance.name}[{host_idx}]"
                        edge.ep1.component = f"{host_nic_component.name}[{nic_idx}]"
                        edge.ep2.instance = f"{switch_instance.name}[{router_idx}]"
                        edge.ep2.component = f"{switch_port_component.name}[{terminal_port}]"
                        terminal_port += 1

        # router to router intra-group
        for group_idx in range(total_groups):
            base = group_idx * routers_per_group
            intra_cursor = [intra_port_base] * routers_per_group
            for i in range(routers_per_group):
                for j in range(i + 1, routers_per_group):
                    edge = self.edges.add(
                        scheme=InfrastructureEdge.ONE2ONE,
                        link=intra_switch_link.name,
                    )
                    edge.ep1.instance = f"{switch_instance.name}[{base + i}]"
                    edge.ep1.component = f"{switch_port_component.name}[{intra_cursor[i]}]"
                    edge.ep2.instance = f"{switch_instance.name}[{base + j}]"
                    edge.ep2.component = f"{switch_port_component.name}[{intra_cursor[j]}]"
                    intra_cursor[i] += 1
                    intra_cursor[j] += 1

        # router to router inter-group 
        next_router_in_group = [0] * total_groups
        next_port_on_router = [0] * total_groups

        for gi in range(total_groups):
            for gj in range(gi + 1, total_groups):
                ri = gi * routers_per_group + next_router_in_group[gi]
                rj = gj * routers_per_group + next_router_in_group[gj]
                pi = global_port_base + next_port_on_router[gi]
                pj = global_port_base + next_port_on_router[gj]

                edge = self.edges.add(
                    scheme=InfrastructureEdge.ONE2ONE,
                    link=inter_switch_link.name,
                )
                edge.ep1.instance = f"{switch_instance.name}[{ri}]"
                edge.ep1.component = f"{switch_port_component.name}[{pi}]"
                edge.ep2.instance = f"{switch_instance.name}[{rj}]"
                edge.ep2.component = f"{switch_port_component.name}[{pj}]"

                # if filled all h ports, move to next router
                next_port_on_router[gi] += 1
                if next_port_on_router[gi] == h:
                    next_port_on_router[gi] = 0
                    next_router_in_group[gi] += 1

                # same for gj
                next_port_on_router[gj] += 1
                if next_port_on_router[gj] == h:
                    next_port_on_router[gj] = 0
                    next_router_in_group[gj] += 1