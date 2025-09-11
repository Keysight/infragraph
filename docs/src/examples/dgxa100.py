from typing import Optional
from infragraph import Component, Device, DeviceEdge, DeviceEdgeIter, ComponentIter, LinkIter


class DgxA100(Device):
    def __init__(self, count: int, nic: Optional[Device] = None):
        """Adds an InfraGraph device to infrastructure based on the following components:
        - 2 cpus
        - 8 npus
        - 4 pcie switches
        - 8 nics
        - 6 nvlink switches
        """
        super(Device, self).__init__()
        self.name = "dgxa100"
        self.count = count
        self.connections = []
        self.description = "Nvidia DGX-A100 System"

        cpu = self.components.add(name="cpu", type=Component.CPU, description="AMD Epyc 7742 CPU")
        npu = self.components.add(
            name="npu", type=Component.NPU, external=True, description="Nvidia A100 GPU"
        )
        nvlsw = self.components.add(name="nvlsw", type=Component.CUSTOM, description="NVLink Switch")
        pciesw = self.components.add(
            name="pciesw", type=Component.CUSTOM, description="PCI Express Switch Gen 4"
        )
        if nic is None:
            self.components.add(name="nic", type=Component.NIC, description="Generic Nic")
        else:
            for c in nic.components:
                self.components.add(name=c.name)

        fabric = self.links.add(name="fabric", description="AMD Infinity Fabric")
        pcie = self.links.add(name="pcie")

        for idx in range(self.count):
            parent = f"{self.name}.{idx}"
            # self.edges.append(DeviceEdge(ep1=[parent, f""], ep2=[parent, f""], link=fabric.name))
            # for cpu_idx, pciesw_idx in zip([0, 0, 1, 1], [0, 1, 2, 3]):
            #     self.connections.append(f"{cpu.name}.{cpu_idx}.{pcie.name}.{pciesw.name}.{pciesw_idx}")
            # for pciesw_idx, npu_idx in zip([i for i in range(4) for _ in range(2)], range(8)):
            #     self.connections.append(f"{pciesw.name}.{pciesw_idx}.{pcie.name}.{npu.name}.{npu_idx}")
            # for npu_idx, nvlsw_idx in zip([i for i in range(8)] * 8, [i for i in range(6) for _ in range(8)]):
            #     self.connections.append(f"{npu.name}.{npu_idx}.{pcie.name}.{nvlsw.name}.{nvlsw_idx}")


if __name__ == "__main__":
    device = DgxA100(count=4)
    print(device.serialize(encoding=Device.YAML))
