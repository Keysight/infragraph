import os
import tempfile
import xml.etree.ElementTree as ET
import ctypes

from pathlib import Path
from typing import Dict, List, Tuple
from infragraph import *

# Constants
CPU_FABRICS = {
    "AuthenticAMD": "AMD Infinity Fabric",
    "GenuineIntel": "Intel Ultra Path Interconnect(UPI)",
}

NVLINK_TCLASS = {
    "0x068000": "NVSwitch",
    "0x03": "P2P",
}

NVIDIA_MODEL_CLASS = {
    "0x2321": "NVIDIA H100 NVL 94GB",
    "0x2330": "NVIDIA H100 80GB",
    "0x20b0": "NVIDIA A100"
}

MELLANOX_MODEL_CLASS = {
    "0x1021": "Mellanox ConnectX-7 VF",
    "0x101b": "Mellanox ConnectX-6 VPI"
}

XPU_PCI_CLASS_PREFIX = "0x03"
NIC_PCI_CLASS_PREFIX = "0x02"
PCI_BRIDGE_CLASS_PREFIX = "0x0604"

class NcclHelper:
    def generate_nccl_topology():
        # Load NCCL shared library
        nccl = ctypes.CDLL("libnccl.so")
        cuda = ctypes.CDLL("libcudart.so")

        # Get GPU count
        n_devices = ctypes.c_int(0)
        cuda.cudaGetDeviceCount(ctypes.byref(n_devices))
        n_devices = n_devices.value
        print(f"Found {n_devices} GPUs")

        # Setup communicator and device arrays
        CommType = ctypes.c_void_p * n_devices # void* comms[n_devices] in c;
        comms = CommType()
        devs = (ctypes.c_int * n_devices)(*range(n_devices)) # giving gpu ids in order

        # initializes NCCL across all specified GPUs in one call
        # Internally it:
        # Probes PCI topology
        # Detects NVLink connections
        # Detects NUMA topology
        # Builds the internal topology graph
        # Dumps XML to NCCL_TOPO_DUMP_FILE if the env var is set
        # ncclCommInitAll(comms, nDevices, devs); 
        ret = nccl.ncclCommInitAll(comms, ctypes.c_int(n_devices), devs)
        if ret != 0:
            print(f"NCCL init failed with error code: {ret}")
            return

        print(f"Topology dumped to: {os.environ.get('NCCL_TOPO_DUMP_FILE', 'not set')}")

        # Cleanup, frees the communicator resources for each GPU
        for i in range(n_devices):
            nccl.ncclCommDestroy(comms[i])


class NcclParser:
    """Parser for NCCL XML topology files to generate device topology graphs."""

    def __init__(self, file_path: str):
        _, ext = os.path.splitext(file_path)
        if ext.lower() != ".xml":
            raise ValueError(
                f"NcclParser expects an XML file, got '{ext}' instead."
            )
        self.file_path = file_path
        self.tree = ET.parse(file_path)
        self.root = self.tree.getroot()
        self.device = Device()
        self.device.name = "mydevice"

        # Data structures for tracking components
        self.pci_bridge_to_pcidevice: Dict[str, List[str]] = {}
        self.pci_device_to_component: Dict[str, List[str]] = {}
        self.cpu_to_bridge_map: Dict[str, int] = {}
        self.cpu_to_direct_device_map: Dict[int,int] = {}
        self.gpu_pairs: Dict[int, int] = {}
        self.device_model_map: Dict[int, int] = {}

    

    def parse(self, infra_type: str = "infragraph"):
        """Main parsing method that orchestrates the entire parsing process."""
        self._parse_cpu_info()

        bridge_map, bridge_count, pci_device_count = self._build_pci_bridge_dict()

        self._create_components(bridge_count, pci_device_count)
        self._create_cpu_fabric_links()
        self._create_topology_edges(bridge_map)

        if infra_type == "device":
            return self.device

        infra = Infrastructure()
        infra.devices.append(self.device)
        infra.instances.add(name=self.device.name, device=self.device.name, count=1)
        return infra

    def _parse_cpu_info(self):
        cpu_elements = self.root.findall(".//cpu")
        cpu_element = self.root.find(".//cpu")

        if cpu_element is None:
            raise ValueError("No <cpu> elements found in XML.")

        self.cpu_count = len(cpu_elements)
        self.cpu_vendor = cpu_element.get("vendor", "")
        
        for idx, node in enumerate(cpu_elements):
            cpu_str = f"cpu_{idx}"
            cpu_close_bridges = node.findall("./pci")
            self.cpu_to_bridge_map[cpu_str] = len(cpu_close_bridges)

        self.cpu = self.device.components.add(
            name="cpu",
            description=self.cpu_vendor,
            count=self.cpu_count,
        )
        self.cpu.choice = Component.CPU
        
        # Track (cpu_index, nic_count) for bare NICs under each CPU
        self._non_pci_nic_count = 0
        self._cpu_non_pci_nic_map: List[Tuple[int, int]] = []  # (cpu_idx, count)
        for idx, cpu in enumerate(self.root.iter("cpu")):
            count = sum(1 for child in cpu if child.tag == "nic")
            if count:
                self._cpu_non_pci_nic_map.append((idx, count))
                self._non_pci_nic_count += count

    def _detect_nvlink_type(self) -> str:
        """Detect NVLink interconnect type from the first nvlink element."""
        nvlink = self.root.find(".//nvlink")
        if nvlink is None:
            return None
        return nvlink.get("tclass", "")

    def _build_gpu_pairs(self) -> Dict[int, int]:
        """
        Build GPU peer-to-peer pairs from NVLink connections.
        Only applicable when NVLink tclass indicates direct P2P (not NVSwitch).
        """
        busid_to_rank: Dict[str, int] = {}

        def map_gpus(elem, current_busid=None):
            if elem.tag == "pci":
                current_busid = elem.get("busid")
            if elem.tag == "gpu":
                busid_to_rank[current_busid] = int(elem.get("rank"))
            for child in elem:
                map_gpus(child, current_busid)

        map_gpus(self.root)

        pairs: Dict[int, int] = {}

        def find_pairs(elem, current_rank=None):
            if elem.tag == "gpu":
                current_rank = int(elem.get("rank"))
            if elem.tag == "nvlink" and current_rank is not None:
                target_busid = elem.get("target")
                if target_busid in busid_to_rank:
                    pairs[current_rank] = busid_to_rank[target_busid]
            for child in elem:
                find_pairs(child, current_rank)

        find_pairs(self.root)
        return pairs
    def _connect_non_pci_nics_to_cpu(self):
        """Connect bare <nic> elements (not under any PCI bridge) directly to their CPU."""
        if not self._non_pci_nic_count:
            return

        # PCI-discovered NICs are indexed first; bare NICs follow
        pci_nic_count = sum(
            1 for components in self.pci_device_to_component.values()
            if components == ["nic"]
        )
        nic_index = pci_nic_count  # bare NICs start after PCI NICs

        # Use a direct link (or reuse self.pci — pick whatever fits your model)
        cpu_nic_link = self.device.links.add(name="cpu_nic", description="CPU to NIC direct")

        for cpu_idx, count in self._cpu_non_pci_nic_map:
            for _ in range(count):
                edge = self.device.edges.add(
                    scheme=DeviceEdge.MANY2MANY,
                    link=cpu_nic_link.name,
                )
                edge.ep1.component = f"{self.cpu.name}[{cpu_idx}]"
                edge.ep2.component = f"{self.nic.name}[{nic_index}]"
                nic_index += 1

    def _build_pci_bridge_dict(self) -> Tuple[Dict, int, int]:
        bridge_map: Dict[str, List[str]] = {}
        bridge_index = 0
        pci_device_index = 0
        cpu_direct_current_idx = 0

        # track the starting bridge index for each cpu
        self.cpu_bridge_start: Dict[int, int] = {}
        self.cpu_real_bridge_count: Dict[int, int] = {}

        def parse_node(xml_node, parent_bridge_key):
            nonlocal bridge_index, pci_device_index
            pci_class = xml_node.get("class", "")
            device_model = xml_node.get("device", "")

            if pci_class.startswith(PCI_BRIDGE_CLASS_PREFIX):
                current_key = f"pci_bridge{bridge_index}"
                bridge_index += 1
                bridge_map[current_key] = []
                if parent_bridge_key is not None:
                    bridge_map[parent_bridge_key].append(current_key)
                for child in xml_node:
                    parse_node(child, current_key)

            elif pci_class.startswith(XPU_PCI_CLASS_PREFIX):
                pci_device_key = f"pci_device{pci_device_index}"
                pci_device_index += 1
                self.pci_bridge_to_pcidevice.setdefault(parent_bridge_key, []).append(pci_device_key)

                self.pci_device_to_component[pci_device_key] = ["gpu"]
                if device_model != "":
                    if device_model in NVIDIA_MODEL_CLASS:
                        if "xpu" not in self.device_model_map:
                            self.device_model_map["xpu"] = NVIDIA_MODEL_CLASS[device_model]


            elif pci_class.startswith(NIC_PCI_CLASS_PREFIX):
                pci_device_key = f"pci_device{pci_device_index}"
                pci_device_index += 1
                self.pci_bridge_to_pcidevice.setdefault(parent_bridge_key, []).append(pci_device_key)
                self.pci_device_to_component[pci_device_key] = ["nic"]
                if device_model != "":
                    if device_model in MELLANOX_MODEL_CLASS:
                        if "nic" not in self.device_model_map:
                            self.device_model_map["nic"] = MELLANOX_MODEL_CLASS[device_model]

        for cpu in self.root.iter("cpu"):
            root_key = None
            real_bridge_count = 0
            # Record where this CPU's bridges start
            # (synthetic bridge, if created, will be AT bridge_index before we increment)
            bridge_start_for_cpu = bridge_index

            for pci in cpu:
                if pci.tag != "pci":
                    continue
                pci_class = pci.get("class", "")

                if not pci_class.startswith(PCI_BRIDGE_CLASS_PREFIX):
                    # Direct device under CPU — create synthetic root bridge once
                    if root_key is None:
                        root_key = f"pci_bridge{bridge_index}"
                        self.cpu_to_direct_device_map[cpu_direct_current_idx] = bridge_index
                        bridge_index += 1
                        bridge_map[root_key] = []
                        # synthetic bridge was inserted before real bridges;
                        # update start so real bridges are tracked correctly
                        bridge_start_for_cpu = bridge_index
                else:
                    real_bridge_count += 1

                parse_node(pci, parent_bridge_key=root_key)

            self.cpu_bridge_start[cpu_direct_current_idx] = bridge_start_for_cpu
            self.cpu_real_bridge_count[cpu_direct_current_idx] = real_bridge_count
            cpu_direct_current_idx += 1

        return bridge_map, bridge_index, pci_device_index

    def _create_components(self, bridge_count: int, pci_device_count: int):
        """Create all device components: PCI bridges, PCI devices, GPUs, NICs."""
        self.pci = self.device.links.add(name="pci")

        self.pci_bridge = self.device.components.add(
            name="pci_bridge",
            description="PCI bridge connecting PCI devices or other PCI bridges",
            count=bridge_count,
        )
        self.pci_bridge.choice = Component.CUSTOM
        self.pci_bridge.custom.type = "pci_bridge"

        self.pci_device = self.device.components.add(
            name="pci_device",
            description="PCI endpoint device (GPU or NIC)",
            count=pci_device_count,
        )
        self.pci_device.choice = Component.CUSTOM
        self.pci_device.custom.type = "pci_device"
        
        # check if the device model is present in the xml
        if "xpu" not in self.device_model_map:
            self.device_model_map["xpu"] = "xpu"
        if "nic" not in self.device_model_map:
            self.device_model_map["nic"] = "nic"

        xpu_count = len(self.root.findall(".//gpu"))
        self.xpu = self.device.components.add(
            name="xpu",
            description=self.device_model_map["xpu"],
            count=xpu_count,
        )
        self.xpu.choice = Component.XPU

        # Combine PCI-discovered NICs + bare <nic> tags under <cpu>
        pci_nic_count = sum(
            1 for components in self.pci_device_to_component.values()
            if components == ["nic"]
        )
        nic_count = pci_nic_count + self._non_pci_nic_count

        if nic_count > 0:
            self.nic = self.device.components.add(
                name="nic",
                description=self.device_model_map["nic"],
                count=nic_count,
            )
            self.nic.choice = Component.NIC

    def _create_cpu_fabric_links(self):
        """Create CPU fabric interconnect links for multi-CPU systems."""
        if self.cpu_count > 1:
            cpu_fabric_name = CPU_FABRICS.get(self.cpu_vendor, "")
            if cpu_fabric_name:
                cpu_fabric = self.device.links.add(
                    name=cpu_fabric_name,
                    description=cpu_fabric_name,
                )
                edge = self.device.edges.add(
                    scheme=DeviceEdge.MANY2MANY,
                    link=cpu_fabric.name,
                )
                edge.ep1.component = self.cpu.name
                edge.ep2.component = self.cpu.name

    def _create_topology_edges(self, bridge_map: Dict):
        """Create all topology edges for the device."""
        self._connect_bridges(bridge_map)
        self._connect_cpu_to_bridges()
        self._connect_pci_devices_to_bridges()
        self._connect_pci_devices_to_components()
        self._connect_gpu_peers()
        self._connect_non_pci_nics_to_cpu() 

    def _connect_bridges(self, bridge_map: Dict):
        """Connect PCI bridges according to the hierarchy."""
        for parent_key, children in bridge_map.items():
            parent_index = parent_key[10:]
            for child_key in children:
                edge = self.device.edges.add(
                    scheme=DeviceEdge.ONE2ONE,
                    link=self.pci.name,
                )
                edge.ep1.component = f"{self.pci_bridge.name}[{parent_index}]"
                edge.ep2.component = f"{self.pci_bridge.name}[{child_key[10:]}]"

    def _connect_cpu_to_bridges(self):
        for idx in range(self.cpu_count):
            start = self.cpu_bridge_start[idx]
            count = self.cpu_real_bridge_count[idx]

            for i in range(start, start + count):
                edge = self.device.edges.add(
                    scheme=DeviceEdge.MANY2MANY,
                    link=self.pci.name
                )
                edge.ep1.component = f"{self.cpu.name}[{idx}]"
                edge.ep2.component = f"{self.pci_bridge.name}[{i}]"

            # Connect to synthetic bridge if this cpu has direct devices
            if idx in self.cpu_to_direct_device_map:
                edge = self.device.edges.add(
                    scheme=DeviceEdge.MANY2MANY,
                    link=self.pci.name
                )
                edge.ep1.component = f"{self.cpu.name}[{idx}]"
                edge.ep2.component = f"{self.pci_bridge.name}[{self.cpu_to_direct_device_map[idx]}]"

    def _connect_pci_devices_to_bridges(self):
        """Connect PCI endpoint devices to their parent bridges."""
        for bridge_key, pci_devices in self.pci_bridge_to_pcidevice.items():
            bridge_index = bridge_key[10:]
            for pci_device_key in pci_devices:
                edge = self.device.edges.add(
                    scheme=DeviceEdge.MANY2MANY,
                    link=self.pci.name,
                )
                edge.ep1.component = f"{self.pci_bridge.name}[{bridge_index}]"
                edge.ep2.component = f"{self.pci_device.name}[{pci_device_key[10:]}]"

    def _connect_pci_devices_to_components(self):
        """Connect PCI endpoint devices to their actual GPU or NIC components."""
        gpu_index = 0
        nic_index = 0

        for pci_device_key, components in self.pci_device_to_component.items():
            pci_device_index = pci_device_key[10:]

            for component_type in components:
                edge = self.device.edges.add(
                    scheme=DeviceEdge.MANY2MANY,
                    link=self.pci.name,
                )
                edge.ep1.component = f"{self.pci_device.name}[{pci_device_index}]"

                if component_type == "gpu":
                    edge.ep2.component = f"{self.xpu.name}[{gpu_index}]"
                    gpu_index += 1
                else:
                    edge.ep2.component = f"{self.nic.name}[{nic_index}]"
                    nic_index += 1
    def _get_nvswitch_targets(self) -> list:
        """Collect unique NVSwitch busids from all nvlink elements with NVSwitch tclass."""
        seen = set()
        ordered = []
        for nvlink in self.root.iter("nvlink"):
            if nvlink.get("tclass", "") == "0x068000":
                target = nvlink.get("target")
                if target and target not in seen:
                    seen.add(target)
                    ordered.append(target)
        return ordered
    
    def _connect_gpu_peers(self):
        """Connect GPUs via NVLink — either P2P or through NVSwitches."""
        tclass = self._detect_nvlink_type()

        if tclass is not None and tclass.startswith("0x03"):
            # P2P direct GPU-to-GPU NVLink
            self.gpu_pairs = self._build_gpu_pairs()
            nvlink = self.device.links.add(name="nvlink", description="NVLink P2P")
            for src_rank, dst_rank in self.gpu_pairs.items():
                edge = self.device.edges.add(
                    scheme=DeviceEdge.MANY2MANY,
                    link=nvlink.name,
                )
                edge.ep1.component = f"{self.xpu.name}[{src_rank}]"
                edge.ep2.component = f"{self.xpu.name}[{dst_rank}]"

        else:
            # NVSwitch topology — each GPU connects to every NVSwitch
            nvswitch_targets = self._get_nvswitch_targets()
            nvswitch_count = len(nvswitch_targets)

            busid_to_index = {busid: i for i, busid in enumerate(nvswitch_targets)}

            self.nvswitch = self.device.components.add(
                name="nvsw",
                description="NVSwitch",
                count=nvswitch_count,
            )
            self.nvswitch.choice = Component.CUSTOM
            self.nvswitch.custom.type = "switch"

            nvlink = self.device.links.add(name="nvlink", description="NVLink NVSwitch")

            def get_gpu_nvswitch_connections(elem, current_rank=None):
                if elem.tag == "gpu":
                    current_rank = int(elem.get("rank"))
                if elem.tag == "nvlink" and current_rank is not None:
                    tclass = elem.get("tclass", "")
                    target = elem.get("target")
                    if tclass == "0x068000" and target in busid_to_index:
                        sw_index = busid_to_index[target]
                        edge = self.device.edges.add(
                            scheme=DeviceEdge.MANY2MANY,
                            link=nvlink.name,
                        )
                        edge.ep1.component = f"{self.xpu.name}[{current_rank}]"
                        edge.ep2.component = f"{self.nvswitch.name}[{sw_index}]"
                for child in elem:
                    get_gpu_nvswitch_connections(child, current_rank)

            get_gpu_nvswitch_connections(self.root)


def run_nccl_parser(
    input_file: str,
    output_file: str = "device.yaml",
    dump_format: str = "yaml",
) -> str:
    """Parse a NCCL topology XML file and export it in the requested format."""

    tmp_xml = None
    if input_file is None:
        tmp_xml = Path(tempfile.gettempdir()) / "nccl_topo.xml"
        os.environ["NCCL_TOPO_DUMP_FILE"] = str(tmp_xml)
        NcclHelper.generate_nccl_topology()
        input_file = str(tmp_xml)

    _, ext = os.path.splitext(output_file)
    ext = ext.lstrip(".").lower()

    if ext != dump_format.lower():
        raise ValueError(
            f"Output extension '.{ext}' does not match format '{dump_format}'."
        )

    if not os.path.isfile(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")

    parser = NcclParser(input_file)
    device_model = parser.parse()

    serialized_data = device_model.serialize(dump_format)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(serialized_data)
        print(f"Translated output written to: {output_file}")

    return serialized_data
