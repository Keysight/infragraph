from typing import Optional
from infragraph import Device, ComponentIter, LinkIter


class DgxA100(Device):
    def __init__(self, count: int, nic: Optional[Device] = None):
        """Adds an InfraGraph device to infrastructure based on the following components:
        - 2 cpus
        - 8 npus
        - 4 pcie switches
        - 8 nics
        - 8 nvlink switches
        """
        super(Device, self).__init__()
        self.name = "dgxa100"
        self.count = count
        self.connections = []
        self.description = "Nvidia DGX-A100 Server"

        cpu = self.components.add(name="cpu", type="cpu", description="AMD Epyc 7742 CPU")
        npu = self.components.add(name="npu", type="npu", external=True, description="Nvidia A100 GPU")
        nvlsw = self.components.add(name="nvlsw", type="custom", description="NVLink Switch")
        pciesw = self.components.add(name="pciesw", type="custom", description="PCI Express Switch Gen 4")
        if nic is None:
            self.components.add(name="nic", type="nic", description="Generic Nic Card")
            self.components.add(name="port", type="custom", description="Generic Nic Interface Port")
        else:
            for c in nic.components:
                self.components.add(name=c.name)

        fabric = self.links.add(name="fabric", description="AMD Infinity Fabric")
        pcie = self.links.add(name="pcie")

        self.connections.append(f"{cpu.name}.0.{fabric.name}.{cpu.name}.1")
        for cpu_idx, pciesw_idx in zip([0, 0, 1, 1], [0, 1, 2, 3]):
            self.connections.append(f"{cpu.name}.{cpu_idx}.{pcie.name}.{pciesw.name}.{pciesw_idx}")
        for pciesw_idx, npu_idx in zip([i for i in range(4) for _ in range(2)], range(8)):
            self.connections.append(f"{pciesw.name}.{pciesw_idx}.{pcie.name}.{npu.name}.{npu_idx}")
        for npu_idx, nvlsw_idx in zip([i for i in range(8) for _ in range(8)], [i for i in range(8)] * 8):
            self.connections.append(f"{npu.name}.{npu_idx}.{pcie.name}.{nvlsw.name}.{nvlsw_idx}")


if __name__ == "__main__":
    device = DgxA100(count=4)
    print(device.serialize(encoding=Device.YAML))
