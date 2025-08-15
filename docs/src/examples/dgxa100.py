import sys
sys.path.append("../../../artifacts")

from infragraph import Infrastructure, Device
from cx5 import Cx5

class DgxA100:
    def __init__(self, infra: Infrastructure, nic: Device):
        """Constructs an InfraGraph device based on the following DGX-A100 components.
        - 2 cpus
        - 8 npus
        - 4 pcie switches
        - 8 nics
        - 8 nvlink switches
        """
        device = infra.devices.add(name="dgx-a100", connections=[])
        device.description = "Nvidia DGX-A100 server"

        cpu = device.components.add(name="cpu", type="cpu", description="AMD Epyc 7742 CPU")
        npu = device.components.add(name="npu", type="npu", external=True, description="Nvidia A100 GPU")
        nvlsw = device.components.add(name="nvlsw", type="custom", description="NVLink Switch")
        pciesw = device.components.add(name="pciesw", type="custom", description="PCI Express Switch Gen 4")

        fabric = device.links.add(name="fabric", description="AMD Infinity Fabric")
        pcie = device.links.add(name="pcie")

        device.connections.append(f"{cpu.name}.0.{fabric.name}.{cpu.name}.1")
        for cpu_idx, pciesw_idx in zip([0, 0, 1, 1], [0, 1, 2, 3]):
            device.connections.append(f"{cpu.name}.{cpu_idx}.{pcie.name}.{pciesw.name}.{pciesw_idx}")
        for pciesw_idx, npu_idx in zip([i for i in range(4) for _ in range(2)], range(8)):
            device.connections.append(f"{pciesw.name}.{pciesw_idx}.{pcie.name}.{npu.name}.{npu_idx}")
        for npu_idx, nvlsw_idx in zip([i for i in range(8) for _ in range(8)], [i for i in range(8)] * 8):
            device.connections.append(f"{npu.name}.{npu_idx}.{pcie.name}.{nvlsw.name}.{nvlsw_idx}")


if __name__ == "__main__":
    infra = Infrastructure(name="clos fabric")
    DgxA100(infra, Cx5(infra))
    print(infra)