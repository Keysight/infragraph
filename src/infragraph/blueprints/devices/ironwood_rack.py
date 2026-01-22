from infragraph import *

# pyright: reportArgumentType=false


class IronwoodRack(Device):
    """
    InfraGraph device definition for the IRONWOOD_TORUS_RACK_4x4x4.

    System Description:
    - A single rack containing 32 CPUs, 64 XPUs, and 32 NICs.
    - CPUs: AMD Turin Zen5 EPYC (32 units).
    - XPUs: Ironwood (64 units) with HBM.
    - NICs: nic200 (32 units).
    - Interconnects:
        - XPUs are interconnected in a 4x4x4 3D Torus using ICI links (1400 GBPS).
        - CPUs are connected to XPUs via PCIe Gen5 (128 GBPS).
        - CPUs are connected to NICs via PCIe Gen5 (128 GBPS).
    """
    # Supporting references:
    # - https://docs.cloud.google.com/tpu/docs/v4
    # - https://henryhmko.github.io/posts/tpu/tpu.html
    # - https://newsletter.semianalysis.com/p/google-ai-infrastructure-supremacy

    DIMENSION = 4
    XPU_COUNT = 64
    CPU_COUNT = 32
    NIC_COUNT = 32

    def __init__(self):
        super(Device, self).__init__()
        self.name = "IRONWOOD_TORUS_RACK_4x4x4"
        self.description = "Rack with 64 XPUs in 4x4x4 Torus, 32 CPUs, and 32 NICs"

        # ---------------------------------------------------------------------
        # Components
        # ---------------------------------------------------------------------

        # 1. XPUs (IRONWOOD)
        ironwood = self.components.add(
            name="IRONWOOD",
            description="Ironwood TPU",
            count=self.XPU_COUNT,
        )
        ironwood.choice = Component.XPU

        # 2. CPUs (AMD_TURIN_ZEN5_EPYC)
        cpu = self.components.add(
            name="AMD_TURIN_ZEN5_EPYC",
            description="AMD EPYC CPU",
            count=self.CPU_COUNT,
        )
        cpu.choice = Component.CPU

        # 3. NICs (nic200)
        nic = self.components.add(
            name="nic200",
            description="Network Interface Card",
            count=self.NIC_COUNT,
        )
        nic.choice = Component.NIC

        # ---------------------------------------------------------------------
        # Links
        # ---------------------------------------------------------------------

        # ICI Link for XPU Torus
        ici = self.links.add(
            name="ici",
            description="Interchip Interconnect (ICI) link",
        )
        ici.physical.bandwidth.gigabits_per_second = 1400

        # PCIe Gen5 Link for Host Connections
        pcie_gen5 = self.links.add(
            name="pcie_gen5",
            description="PCI Express Gen5 link",
        )
        pcie_gen5.physical.bandwidth.gigabits_per_second = 128

        # ---------------------------------------------------------------------
        # Topology Construction
        # ---------------------------------------------------------------------

        # 1. 4x4x4 3D Torus Interconnect (XPU <-> XPU)
        # We define connections for a 3D grid where edges wrap around boundaries.
        self._add_torus_topology(ironwood, ici)

        # 2. CPU <-> XPU Connections
        # Logic: Each CPU connects to 2 XPUs.
        # CPU[i] connects to IRONWOOD[2*i] and IRONWOOD[2*i + 1]
        self._connect_cpu_xpu(cpu, ironwood, pcie_gen5)

        # 3. CPU <-> NIC Connections
        # Logic: Each CPU connects to 1 NIC.
        # CPU[i] connects to NIC[i]
        self._connect_cpu_nic(cpu, nic, pcie_gen5)

    def _add_torus_topology(self, component, link):
        """
        Creates a 3D Torus topology for the given component using the specified link.
        Assumes the component count is a perfect cube of self.DIMENSION (4x4x4=64).
        """
        dim = self.DIMENSION

        # Helper to map 3D coordinates to flat index
        def get_idx(x, y, z):
            return x + (y * dim) + (z * dim * dim)

        # Iterate through every node in the 4x4x4 grid
        for z in range(dim):
            for y in range(dim):
                for x in range(dim):
                    current_idx = get_idx(x, y, z)

                    # Connect to neighbors in positive directions (Right, Down, Back)
                    # The wrap-around (modulo) creates the Torus property.

                    # Neighbor X (Right)
                    neighbor_x = get_idx((x + 1) % dim, y, z)
                    self._add_one2one(link, component, current_idx, component, neighbor_x)

                    # Neighbor Y (Down)
                    neighbor_y = get_idx(x, (y + 1) % dim, z)
                    self._add_one2one(link, component, current_idx, component, neighbor_y)

                    # Neighbor Z (Back)
                    neighbor_z = get_idx(x, y, (z + 1) % dim)
                    self._add_one2one(link, component, current_idx, component, neighbor_z)

    def _connect_cpu_xpu(self, cpu_comp, xpu_comp, link):
        """
        Connects CPUs to XPUs.
        Assumes 32 CPUs and 64 XPUs (1:2 ratio).
        """
        xpus_per_cpu = 2
        for i in range(self.CPU_COUNT):
            base_xpu = i * xpus_per_cpu
            for k in range(xpus_per_cpu):
                xpu_idx = base_xpu + k
                self._add_one2one(link, cpu_comp, i, xpu_comp, xpu_idx)

    def _connect_cpu_nic(self, cpu_comp, nic_comp, link):
        """
        Connects CPUs to NICs.
        Assumes 1:1 ratio.
        """
        for i in range(self.CPU_COUNT):
            self._add_one2one(link, cpu_comp, i, nic_comp, i)

    def _add_one2one(self, link, comp1, idx1, comp2, idx2):
        """
        Helper to add a ONE2ONE edge between two indexed components.
        """
        edge = self.edges.add(scheme=DeviceEdge.ONE2ONE, link=link.name)
        edge.ep1.component = f"{comp1.name}[{idx1}]"
        edge.ep2.component = f"{comp2.name}[{idx2}]"


if __name__ == "__main__":
    device = IronwoodRack()
    print(device.serialize(encoding=Device.YAML))
