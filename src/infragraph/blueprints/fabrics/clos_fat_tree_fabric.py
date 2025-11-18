from infragraph import *
from infragraph.blueprints.devices.generic_switch import Switch
from infragraph.infragraph_service import InfraGraphService


class ClosFatTreeFabric(Infrastructure):
    """Return a clos fat tree fabric with the following characteristics:
    Inputs:
        - switch (device instance)
        - host
        - levels - L
        - bandwidth - list of bandwidth for each level 
    Output:
    """

    def __init__(self, switch: Device, host: Device, levels: int, bandwidth):
        super().__init__(name="clos-fat-tree-fabric", description="Clos Fat Tree Fabric")

        # levels assertion
        if levels > 3 or levels <= 1:
            raise ValueError("Invalid levels, Should be greater than 0 and less than 3")

        switch_port_component = InfraGraphService.get_component(switch, Component.PORT)                     
        host_nic_component = InfraGraphService.get_component(host, Component.NIC)
        switch_port_count = switch_port_component.count
        # switch port assertion with host nic
        if (switch_port_count//2) % host_nic_component.count != 0:
            raise ValueError(
                f"Host ports ({host_nic_component.count}) not divisible by switch ports ({switch_port_count//2})"
            )
        
        if len(bandwidth) != 0:
            assert len(bandwidth) == levels
        else:
            for i in range(0, levels):
                bandwidth.append(100 * (i + 1))

        
        total_hosts = (2 * (switch_port_count // 2) ** levels) // host_nic_component.count
        tier_0_count = 2 * (switch_port_count // 2) * (levels - 1)
        hosts_per_rack = (switch_port_count//2) // host_nic_component.count
        # add host & switch devices
        self.devices.append(host).append(switch)
        host_instance = self.instances.add(name=host.name, device=host.name, count=total_hosts)

        # tier 0 is present always
        tier_0_link = self.links.add(
            name="tier_0_link",
            description="Link characteristics for connectivity between host and tier 0 switches",
        )
        tier_0_link.physical.bandwidth.gigabits_per_second = bandwidth[0]
        tier_0_instance = self.instances.add(name="tier_0", device=switch.name, count=tier_0_count)

        # generate connections - tier_0 to host
        # link each host to one tier 0 switch
        for tier_0_switch_index in range(tier_0_count):
            tier_0_switch_port_index = 0
            for host_group in range(0, hosts_per_rack):
                # for each host, get the index 
                for host_nic_index in range(0, host_nic_component.count):
                    host_index = host_group + (tier_0_switch_index * hosts_per_rack)
                    edge = self.edges.add(
                        scheme=InfrastructureEdge.ONE2ONE, link=tier_0_link.name
                    )
                    edge.ep1.instance = f"{host_instance.name}[{host_index}]"
                    edge.ep1.component = f"{host_nic_component.name}[{host_nic_index}]"
                    edge.ep2.instance = f"{tier_0_instance.name}[{tier_0_switch_index}]"
                    edge.ep2.component = f"{switch_port_component.name}[{tier_0_switch_port_index}]"
                    tier_0_switch_port_index = tier_0_switch_port_index + 1

        if levels == 2:
            # connect spine with tier_0
            tier_1_link = self.links.add(
                name="tier_1_link",
                description="Link characteristics for connectivity between tier 0 and tier 1 switches",
            )
            tier_1_link.physical.bandwidth.gigabits_per_second = bandwidth[1]

            spine_switch_count = (switch_port_count // 2) ** (levels - 1)
            tier_1_instance = self.instances.add(name="tier_1", device=switch.name, count=spine_switch_count)

            # connect spine switch with rack switch here
            rack_switch_port_index = switch_port_count // 2
            for pod_switch_index in range(spine_switch_count):
                rack_switch_index = 0
                for pod_switch_port_index in range(0, switch_port_count):
                    edge = self.edges.add(
                        scheme=InfrastructureEdge.ONE2ONE, link=tier_1_link.name
                    )
                    edge.ep1.instance = f"{tier_1_instance.name}[{pod_switch_index}]"
                    edge.ep1.component = f"{switch_port_component.name}[{pod_switch_port_index}]"
                    edge.ep2.instance = f"{tier_0_instance.name}[{rack_switch_index}]"
                    edge.ep2.component = f"{switch_port_component.name}[{rack_switch_port_index}]"
                    rack_switch_index = rack_switch_index + 1
                rack_switch_port_index = rack_switch_port_index + 1
        
        elif levels == 3:
            # connect tier0 and tier1
            number_of_pods = 2 * (switch_port_count // 2) * (levels - 2)
            tier_1_link = self.links.add(
                name="tier_1_link",
                description="Link characteristics for connectivity between tier 0 and tier 1 switches",
            )
            tier_1_link.physical.bandwidth.gigabits_per_second = bandwidth[1]
            
            tier_1_count = tier_0_count
            tier_1_instance = self.instances.add(name="tier_1", device=switch.name, count=tier_1_count)

            # group the tier 0 and tier 1 and connect them
            tier_group_count = tier_1_count // number_of_pods
            for pod_switch_index in range(0, tier_1_count, tier_group_count):
                rack_switch_port_index = switch_port_count // 2
                for pod_switch_group in range(pod_switch_index, min(pod_switch_index + tier_group_count, tier_1_count)):
                    pod_switch_port_index = 0
                    
                    for rack_switch_index in range(pod_switch_index, min(pod_switch_index + tier_group_count, tier_1_count)):
                        edge = self.edges.add(
                            scheme=InfrastructureEdge.ONE2ONE, link=tier_1_link.name
                        )
                        edge.ep1.instance = f"{tier_1_instance.name}[{pod_switch_group}]"
                        edge.ep1.component = f"{switch_port_component.name}[{pod_switch_port_index}]"
                        edge.ep2.instance = f"{tier_0_instance.name}[{rack_switch_index}]"
                        edge.ep2.component = f"{switch_port_component.name}[{rack_switch_port_index}]"
                        pod_switch_port_index = pod_switch_port_index + 1
                    rack_switch_port_index = rack_switch_port_index + 1

            # connect tier1 and tier2
            tier_2_link = self.links.add(
                name="tier_2_link",
                description="Link characteristics for connectivity between tier 1 and tier 2 switches",
            )
            tier_2_link.physical.bandwidth.gigabits_per_second = bandwidth[2]

            spine_switch_count = (switch_port_count // 2) ** (levels - 1)
            tier_2_instance = self.instances.add(name="tier_2", device=switch.name, count=spine_switch_count)

            # connect spine switch with pod switch here
            pod_switch_port_index = switch_port_count // 2
            for spine_switch_index in range(spine_switch_count):
                pod_switch_index = 0
                for spine_switch_port_index in range(0, switch_port_count):
                    edge = self.edges.add(
                        scheme=InfrastructureEdge.ONE2ONE, link=tier_1_link.name
                    )
                    edge.ep1.instance = f"{tier_2_instance.name}[{spine_switch_index}]"
                    edge.ep1.component = f"{switch_port_component.name}[{spine_switch_port_index}]"
                    edge.ep2.instance = f"{tier_1_instance.name}[{pod_switch_index}]"
                    edge.ep2.component = f"{switch_port_component.name}[{pod_switch_port_index}]"
                    pod_switch_index = pod_switch_index + 1
                pod_switch_port_index = pod_switch_port_index + 1

            