from infragraph.infragraph import *

class DellPowerSwitchZ9864FOn(Device):
    """
    InfraGraph blueprint of the Dell PowerSwitch Z9864F-ON.
    """

    OSFP_PORT_COUNT = 64  
    SFP_PORT_COUNT = 2     

    def __init__(self):
        """Adds an InfraGraph device to infrastructure based on the following components:
        - 1 CPU
        - 64 osfp112 ports (800GbE, multi-rate capable)
        - 2 SFP+ ports (10GbE)
        - integrated circuitry connecting all ports to the ASIC
        """
        super(Device, self).__init__()
        self.name = "powerswitch_z9864f_on"
        self.description = "Dell PowerSwitch Z9864F-ON 64x400GbE  aggregation switch"

        cpu = self.components.add(
            name="cpu",
            description=" Intel Xeon D-1714",
            count=1,
        )
        cpu.choice = Component.CPU

        memory=self.components.add(
            name="memory",
            description="32GB DDR4 ECC",
            count=1,
        )

        osfp_ports = self.components.add(
            name="osfp_port",
            description="OSFP112 800GbE multi-rate port",
            count=self.OSFP_PORT_COUNT,
        )
        osfp_ports.choice = Component.PORT

        sfp_ports = self.components.add(
            name="sfp_port",
            description="SFP+ 10GbE port",
            count=self.SFP_PORT_COUNT,
        )
        sfp_ports.choice = Component.PORT

        ic = self.links.add(
            name="ic",
            description="Integrated circuitry between ASIC and ports",
        )

        mem_bus=self.links.add(
            name="mem_bus",
            description="ddr4 memory bus",
        )

        qsfp_edge = self.edges.add(scheme=DeviceEdge.MANY2MANY, link=ic.name)
        qsfp_edge.ep1.component = cpu.name
        qsfp_edge.ep2.component = osfp_ports.name

        sfp_edge = self.edges.add(scheme=DeviceEdge.MANY2MANY, link=ic.name)
        sfp_edge.ep1.component = cpu.name
        sfp_edge.ep2.component = sfp_ports.name

        mem_edge=self.edges.add(scheme=DeviceEdge.ONE2ONE, link=mem_bus.name)
        mem_edge.ep1.component=cpu.name
        mem_edge.ep2.component=memory.name


if __name__ == "__main__":
    device = DellPowerSwitchZ9864FOn()
    print(device.serialize(encoding=Device.YAML))