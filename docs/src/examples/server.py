from typing import Optional
from infragraph import Component, Device, DeviceEdge, DeviceEdgeIter, ComponentIter, LinkIter


class Server(Device):
    def __init__(self, count: int, npu_factor: int = 1):
        """Adds an InfraGraph device to infrastructure based on the following components:
        - 1 cpu for every 4 npus
        - X npus = npu_factor * 4
        - 1 pcie switch for every 4 npus
        - 1 nic for every npus connected to a pcie switch
        - 1 nvswitch for all npus
        """
        super(Device, self).__init__()
        self.name = "server"
        self.count = count
        self.connections = []
        self.description = "A generic server with npu_factor * 4 npu(s)"

        cpu = self.components.add(name="cpu", type=Component.CPU, description="Generic CPU")
        npu = self.components.add(
            name="npu", type=Component.NPU, external=True, description="Generic GPU/NPU"
        )
        nvlsw = self.components.add(name="nvlsw", type=Component.CUSTOM, description="NVLink Switch")
        pciesw = self.components.add(
            name="pciesw", type=Component.CUSTOM, description="PCI Express Switch Gen 4"
        )
        nic = self.components.add(name="nic", type=Component.NIC, description="Generic Nic")

        fabric = self.links.add(name="fabric", description="CPU Fabric")
        pcie = self.links.add(name="pcie")

        for idx in range(self.count):
            parent = f"{self.name}.{idx}"
            self.edges.append(DeviceEdge(ep1=[parent, f""], ep2=[parent, f""], link=fabric.name))
            self.connections.append(
                f"{self.name}.{idx}.{cpu.name}.0.{fabric.name}.{self.name}.{idx}.{cpu.name}.1"
            )
            for cpu_idx, pciesw_idx in zip([0, 0, 1, 1], [0, 1, 2, 3]):
                self.connections.append(f"{cpu.name}.{cpu_idx}.{pcie.name}.{pciesw.name}.{pciesw_idx}")
            for pciesw_idx, npu_idx in zip([i for i in range(4) for _ in range(2)], range(8)):
                self.connections.append(f"{pciesw.name}.{pciesw_idx}.{pcie.name}.{npu.name}.{npu_idx}")
            for npu_idx, nvlsw_idx in zip([i for i in range(8)] * 8, [i for i in range(6) for _ in range(8)]):
                self.connections.append(f"{npu.name}.{npu_idx}.{pcie.name}.{nvlsw.name}.{nvlsw_idx}")


if __name__ == "__main__":
    device = Server(count=1, npu_factor=2)
    print(device.serialize(encoding=Device.YAML))
