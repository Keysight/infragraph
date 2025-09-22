from infragraph import *


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
        self.description = "Mellanox ConnectX-5"

        asic = self.components.add(
            name="asic",
            description="Offload network processor chip",
            count=1,
        )
        asic.choice = Component.CPU
        port = self.components.add(
            name="port",
            description="The network port on the ConnectX-5 card",
            count=2,
        )
        port.choice = Component.PORT

        pcie = self.links.add(name="pcie")
        edge = self.edges.add(link=pcie.name, many2many=True)
        edge.ep1.component = f"{asic.name}"
        edge.ep2.component = f"{port.name}"
        self.edges.append(edge)


if __name__ == "__main__":
    print(Cx5())
