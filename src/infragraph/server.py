from infragraph import *

# pyright: reportArgumentType=false


class Server(Device):
    def __init__(self, npu_factor: int = 1):
        """Adds an InfraGraph device to infrastructure based on the following components:
        - 1 cpu for every 2 npus
        - 1 pcie switch for every 1 cpu
        - X npus = npu_factor * 2
        - 1 nic for every npu with 2 nics connected to a pcie switch
        - 1 nvswitch connected to all npus
        """
        super(Device, self).__init__()
        self.name = "server"
        self.description = "A generic server with npu_factor * 4 npu(s)"

        cpu = self.components.add(
            name="cpu",
            description="Generic CPU",
            count=npu_factor,
        )
        cpu.choice = Component.CPU
        npu = self.components.add(
            name="npu",
            description="Generic GPU/NPU",
            count=npu_factor * 2,
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
            count=npu_factor,
        )
        pciesw.choice = Component.CUSTOM
        nic = self.components.add(
            name="nic",
            description="Generic Nic",
            count=npu_factor * 2,
        )
        nic.choice = Component.NIC

        cpu_fabric = self.links.add(name="fabric", description="CPU Fabric")
        nvlink = self.links.add(name="nvlink")
        pcie = self.links.add(name="pcie")

        edge = self.edges.add(scheme=DeviceEdge.MANY2MANY, link=cpu_fabric.name)
        edge.ep1.component = cpu.name
        edge.ep2.component = cpu.name

        edge = self.edges.add(scheme=DeviceEdge.MANY2MANY, link=nvlink.name)
        edge.ep1.component = npu.name
        edge.ep2.component = nvlsw.name

        for idx in range(pciesw.count):
            edge = self.edges.add(scheme=DeviceEdge.MANY2MANY, link=pcie.name)
            edge.ep1.component = f"{cpu.name}[{idx}]"
            edge.ep2.component = f"{pciesw.name}[{idx}]"

        npu_slices = [f"{idx}:{idx+2}" for idx in range(0, npu.count, 2)]
        for npu_idx, pciesw_idx in zip(npu_slices, range(pciesw.count)):
            edge = self.edges.add(scheme=DeviceEdge.MANY2MANY, link=pcie.name)
            edge.ep1.component = f"{npu.name}[{npu_idx}]"
            edge.ep2.component = f"{pciesw.name}[{pciesw_idx}]"

        for nic_idx, pciesw_idx in zip(npu_slices, range(pciesw.count)):
            edge = self.edges.add(scheme=DeviceEdge.MANY2MANY, link=pcie.name)
            edge.ep1.component = f"{nic.name}[{nic_idx}]"
            edge.ep2.component = f"{pciesw.name}[{pciesw_idx}]"


if __name__ == "__main__":
    device = Server(npu_factor=2)
    print(device.serialize(encoding=Device.YAML))
