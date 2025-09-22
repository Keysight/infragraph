from typing import Optional
from infragraph import *

# pyright: reportArgumentType=false


class Switch(Device):
    def __init__(self, port_count: int = 16):
        """Adds an InfraGraph device to infrastructure based on the following components:
        - 1 generic asic
        - nic_count number of ports
        - integrated circuitry connecting ports to asic
        """
        super(Device, self).__init__()
        self.name = "switch"
        self.description = "A generic switch"

        asic = self.components.add(
            name="asic",
            description="Generic ASIC",
            count=1,
        )
        asic.choice = Component.CPU
        port = self.components.add(
            name="port",
            description="Generic port",
            count=port_count,
        )
        port.choice = Component.PORT

        ic = self.links.add(name="ic", description="Generic integrated circuitry")

        edge = self.edges.add(many2many=True, link=ic.name)
        edge.ep1.component = asic.name
        edge.ep2.component = port.name


if __name__ == "__main__":
    device = Switch()
    print(device.serialize(encoding=Device.YAML))
