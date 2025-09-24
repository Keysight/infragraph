from typing import Optional
from infragraph import *

# pyright: reportArgumentType=false


class Dgx(Device):
    def __init__(self, nic_device: Optional[Device] = None):
        """Adds an InfraGraph device to infrastructure based on the following components:
        - 2 cpus
        - 8 npus
        - 4 pcie switches
        - 8 nics
        - 1 nvlink switch
        """
        super(Device, self).__init__()
        self.name = "dgx"
        self.description = "Nvidia DGX System"

        cpu = self.components.add(
            name="cpu",
            description="AMD Epyc 7742 CPU",
            count=2,
        )
        cpu.choice = Component.CPU
        npu = self.components.add(
            name="npu",
            description="Nvidia A100 GPU",
            count=8,
        )
        npu.choice = Component.NPU
        nvlsw = self.components.add(
            name="nvlsw",
            description="NVLink Switch",
            count=1,
        )
        nvlsw.choice = Component.CUSTOM
        pciesw = self.components.add(
            name="pciesw",
            description="PCI Express Switch Gen 4",
            count=4,
        )
        pciesw.choice = Component.CUSTOM
        if nic_device is None:
            nic = self.components.add(
                name="nic",
                description="Generic Nic",
                count=8,
            )
            nic.choice = Component.NIC
        else:
            nic = self.components.add(
                name=nic_device.name,
                description=nic_device.description,
                count=8,
            )
            nic.choice = Component.DEVICE

        cpu_fabric = self.links.add(name="fabric", description="AMD Infinity Fabric")
        pcie = self.links.add(name="pcie")
        nvlink = self.links.add(name="nvlink")

        edge = self.edges.add(scheme=DeviceEdge.MANY2MANY, link=cpu_fabric.name)
        edge.ep1.component = cpu.name
        edge.ep2.component = cpu.name

        edge = self.edges.add(scheme=DeviceEdge.MANY2MANY, link=nvlink.name)
        edge.ep1.component = npu.name
        edge.ep2.component = nvlsw.name

        for npu_idx, pciesw_idx in zip(["0:2", "2:4", "4:6", "6:8"], range(pciesw.count)):
            edge = self.edges.add(scheme=DeviceEdge.MANY2MANY, link=pcie.name)
            edge.ep1.component = f"{npu.name}[{npu_idx}]"
            edge.ep2.component = f"{pciesw.name}[{pciesw_idx}]"

        for nic_idx, pciesw_idx in zip(["0:2", "2:4", "4:6", "6:8"], range(pciesw.count)):
            edge = self.edges.add(scheme=DeviceEdge.MANY2MANY, link=pcie.name)
            edge.ep1.component = f"{nic.name}[{nic_idx}]"
            edge.ep2.component = f"{pciesw.name}[{pciesw_idx}]"


if __name__ == "__main__":
    device = Dgx()
    print(device.serialize(encoding=Device.YAML))
