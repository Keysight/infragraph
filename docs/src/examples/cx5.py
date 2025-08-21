from infragraph import Device, ComponentIter, LinkIter


class Cx5(Device):
    def __init__(self):
        """Constructs an InfraGraph device based on a Mellanox CX5 network card
        and adds it the infrastructure devices property.

        """
        super(Device, self).__init__()
        self.name = "cx5"
        self.connections = []
        self.description = "Mellanox ConnectX-5 with 2 ports, 1 CX5 network processor chip, 1 pcie gen4 bus"
        asic = self.components.add(name="asic", type="cpu", description="Offload network processor chip")
        port = self.components.add(
            name="port",
            type="custom",
            external=True,
            description="The network ports on the ConnectX-5 card",
        )
        pcie = self.links.add(name="pcie")
        for port_idx in range(2):
            self.connections.append(f"{asic.name}.0.{pcie.name}.{port.name}.{port_idx}")


if __name__ == "__main__":
    print(Cx5())
