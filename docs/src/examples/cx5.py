from infragraph import Device, DeviceEdge, DeviceEdgeIter, ComponentIter, LinkIter


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
        self.connections = []
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
            self.connections.append(f"{asic.name}.0.{pcie.name}.{port.name}.{port_idx}")
            self.edges.add(
                ep1=[f"{asic.name}.0"],
                link=pcie.name,
                ep2=[f"{port.name}.{port_idx}"],
                directed=False,
            )


if __name__ == "__main__":
    print(Cx5())
