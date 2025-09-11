from infragraph import Device, DeviceEdge, DeviceEndpoint, DeviceEdgeIter, ComponentIter, LinkIter


class Cx5(Device):
    NETWORK_PORTS: int = 2

    def __init__(self):
        """Creates an Infragraph Device object representing a Mellanox CX5 network card.
        - 1 network processor chip
        - 1 pcie gen4 bus
        - 2 phy ports
        """
        super(Device, self).__init__()
        self.name = "cx5"
        self.count = 1
        self.description = "Mellanox ConnectX-5"
        asic = self.components.add(
            name="asic",
            type="cpu",
            description="Offload network processor chip",
        )
        port = self.components.add(
            name="port",
            type="custom",
            external=True,
            description="The network port on the ConnectX-5 card",
        )
        pcie = self.links.add(name="pcie")
        for port_idx in range(Cx5.NETWORK_PORTS):
            edge = self.edges.add(link=pcie.name)
            edge.ep1.component = "asdfasdf"  # f"{asic.name}.0]"
            edge.ep2.component = f"{port.name}[{port_idx}]"
            self.edges.append(edge)
        self.validate()


if __name__ == "__main__":
    print(Cx5())
