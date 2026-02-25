import xml.etree.ElementTree as ET
import argparse
from infragraph import *
from typing import Dict, List, Set, Tuple

# Constants
CPU_FABRICS = {
    "GenuineIntel": "Intel Ultra Path Interconnect(UPI)",
    "AuthenticAMD": "AMD Infinity Fabric"
}

XPU_PCI_CLASS = {
    "0300": "Display GPU",
    "0302": "Compute GPU",
}

XPU_VENDOR_CLASS = {
    "102b": "Matrox card/controller",
    "10de": "Nvidia GPU"
}

NIC_PCI_CLASS = {
    "0200": "Ethernet NIC",
    "0207": "InfiniBand NIC",
    "0208": "Non Ethernet",
    "0280":""
}

NIC_VENDOR_CLASS = {
    "15b3": "Mellanox NIC",
    "8086": "Intel NIC",
    "14e4": "Broadcom Nic",
}


class LstopoParser:
    """Parser for lstopo XML files to generate device topology graphs."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.tree = ET.parse(file_path)
        self.root = self.tree.getroot()
        self.device = Device()
        
        # Data structures for tracking components
        self.gpu_models = []
        self.nics = []
        self.nv_switch_count = 0
        self.bridge_to_pcidevice: Dict[str, List[str]] = {}
        self.pcidevice_to_component: Dict[str, List[str]] = {}
        self.pcidevice_is_nvslw: Dict[str, List[str]] = {}
        self.package_to_root_map: Dict[str, int] = {}
        
    def parse(self) -> Device:
        """Main parsing method that orchestrates the entire parsing process."""
        self._extract_device_name()
        self._parse_cpu_info()
        self._parse_pci_devices()
        self._create_components()
        self._create_cpu_fabric_links()
        
        # Build bridge topology and create edges
        bridge_map, bridge_count, root_count = self._build_pci_bridge_dict()
        self._create_bridge_components(root_count, bridge_count)
        self._create_topology_edges(bridge_map)
        
        return self.device
    
    def _extract_device_name(self):
        """Extract device name from DMI or Platform info."""
        dmi_elem = self.root.find(".//info[@name='DMIProductName']")
        platform_elem = self.root.find(".//info[@name='PlatformModel']")
        
        self.device.name = (
            dmi_elem.get("value") if dmi_elem is not None 
            else platform_elem.get("value") if platform_elem is not None 
            else "your_device"
        )
    
    def _parse_cpu_info(self):
        """Parse CPU information and create CPU components."""
        cpu_model_elem = self.root.find(".//info[@name='CPUModel']")
        cpu_vendor_elem = self.root.find(".//info[@name='CPUVendor']")
        
        if cpu_model_elem is None or cpu_vendor_elem is None:
            raise ValueError("Missing required CPU information in XML.")
        
        self.cpu_model = cpu_model_elem.get("value")
        self.cpu_vendor = cpu_vendor_elem.get("value")
        
        # Count CPU packages and map to root bridges
        machine = self.root.find("object[@type='Machine']")
        packages = machine.findall(".//object[@type='Package']")
        self.cpu_count = len(packages)
        
        for idx, pkg in enumerate(packages):
            cpu_str = f"cpu_{idx}"
            root_bridges = pkg.findall(".//object[@type='Bridge'][@depth='0']")
            self.package_to_root_map[cpu_str] = len(root_bridges)
        
        # Create CPU component
        self.cpu = self.device.components.add(
            name="cpu",
            description=self.cpu_model,
            count=self.cpu_count
        )
        self.cpu.choice = Component.CPU
    
    def _parse_pci_devices(self):
        """Parse all PCI devices (GPUs, NICs, NVSwitches)."""
        for obj in self.root.iter("object"):
            obj_type = obj.get("type")
            obj_subtype = obj.get("subtype")
            
            # Count NVSwitches
            if obj_subtype == "NVSwitch":
                self.nv_switch_count += 1
            
            # Parse PCI devices
            if obj_type == "PCIDev":
                self._parse_single_pci_device(obj)
        
        # Clean NIC names
        self.nics = [s.replace('[', '').replace(']', '') for s in self.nics]
    
    def _parse_single_pci_device(self, obj: ET.Element):
        """Parse a single PCI device and categorize it."""
        pci_type = obj.get("pci_type", "")
        pci_code = pci_type[:4]
        pci_vendor = pci_type[6:10]
        
        # Check if it's a GPU
        if pci_code in XPU_PCI_CLASS:
            self._extract_gpu_info(obj, pci_vendor)
   
        # Check if it's a NIC
        elif pci_code in NIC_PCI_CLASS:
            self._extract_nic_info(obj, pci_vendor)
    
    def _extract_gpu_info(self, obj: ET.Element, pci_vendor: str):
        """Extract GPU information from PCI device."""
        # Check for GPU model in OSDev
        osdevs = obj.findall("object[@type='OSDev']")
        if osdevs:
            for osdev in osdevs:
                for info in osdev.findall("info"):
                    if info.get("name") == "GPUModel":
                        self.gpu_models.append(info.get("value"))
                        return
        # Fallback to PCIDevice info
        pci_device_elem = obj.find("info[@name='PCIDevice']")
        if pci_device_elem is not None:
            self.gpu_models.append(pci_device_elem.get("value"))
        else:
            if pci_vendor in XPU_VENDOR_CLASS:
                self.gpu_models.append(XPU_VENDOR_CLASS[pci_vendor])
    
    def _extract_nic_info(self, obj: ET.Element, pci_vendor: str):
        """Extract NIC information from PCI device."""
        if pci_vendor in NIC_VENDOR_CLASS:
            pci_device_elem = obj.find("./info[@name='PCIDevice']")
            if pci_device_elem is not None:
                self.nics.append(pci_device_elem.get("value").replace("+", ""))
            else:
                self.nics.append(NIC_VENDOR_CLASS[pci_vendor])
    
    def _create_components(self):
        """Create all device components (GPUs, NICs, NVSwitches)."""
        # Create NVSwitch component
        if self.nv_switch_count > 0:
            self.nvlsw = self.device.components.add(
                name="nvlsw",
                description="NV Switch",
                count=self.nv_switch_count,
            )
            self.nvlsw.choice = Component.SWITCH
        
        # Create GPU components
        self.gpu_name_to_component = self._create_gpu_components()
        
        # Create NIC components
        self.nic_name_to_component = self._create_nic_components()
    
    def _create_gpu_components(self) -> Dict[str, Component]:
        """Create GPU components and return mapping."""
        gpu_name_to_component = {}
        filtered_gpu_models =  [i.replace("[","").replace("]","") for i in self.gpu_models]
        self.gpu_models = filtered_gpu_models
        unique_gpus = set(self.gpu_models)
        
        if unique_gpus:
            gpu_counts = {gpu: self.gpu_models.count(gpu) for gpu in unique_gpus}
            
            for gpu_name in unique_gpus:
                xpu = self.device.components.add(
                    name=gpu_name,
                    description=gpu_name,
                    count=gpu_counts[gpu_name]
                )
                xpu.choice = Component.XPU
                gpu_name_to_component[gpu_name] = xpu
        
        return gpu_name_to_component
    
    def _create_nic_components(self) -> Dict[str, Component]:
        """Create NIC components and return mapping."""
        nic_name_to_component = {}
        unique_nics = set(self.nics)
        
        if unique_nics:
            nic_counts = {nic: self.nics.count(nic) for nic in unique_nics}
            
            for nic_name in unique_nics:
                nic = self.device.components.add(
                    name=nic_name,
                    description=nic_name,
                    count=nic_counts[nic_name]
                )
                nic.choice = Component.NIC
                nic_name_to_component[nic_name] = nic
        
        return nic_name_to_component
    
    def _create_cpu_fabric_links(self):
        """Create CPU fabric interconnect links for multi-CPU systems."""
        if self.cpu.count > 1:
            cpu_fabric_name = CPU_FABRICS.get(self.cpu_vendor, "")
            if cpu_fabric_name:
                cpu_fabric = self.device.links.add(
                    name=cpu_fabric_name,
                    description=cpu_fabric_name,
                )
                edge = self.device.edges.add(
                    scheme=DeviceEdge.MANY2MANY,
                    link=cpu_fabric.name
                )
                edge.ep1.component = self.cpu.name
                edge.ep2.component = self.cpu.name
    
    def _build_pci_bridge_dict(self) -> Tuple[Dict, int, int]:
        """Build PCI bridge hierarchy dictionary."""
        bridge_map = {}
        root_index = 0
        bridge_index = 0
        pci_device_index = 0
        nv_switch_index = 0
        
        def parse_bridge(obj: ET.Element, parent_key: str = None) -> str:
            """Recursively parse bridge hierarchy."""
            nonlocal bridge_index, pci_device_index, nv_switch_index
            
            # Assign bridge key
            current_key = f"pci_bridge{bridge_index}"
            bridge_index += 1
            
            if parent_key is not None:
                bridge_map.setdefault(parent_key, []).append(current_key)
            
            bridge_map.setdefault(current_key, [])
            
            # Process children
            for child in obj:
                if child.tag == "object":
                    child_type = child.get("type")
                    
                    if child_type == "Bridge" and len(child) != 0:
                        parse_bridge(child, current_key)
                    
                    elif child_type == "PCIDev":
                        self._process_pci_device(
                            child, current_key, pci_device_index, nv_switch_index
                        )
                        
                        # Handle NVSwitch
                        if child.get("subtype") == "NVSwitch":
                            nv_switch_index += 1
                        
                        pci_device_index += 1
            
            return current_key
        
        # Find and parse root bridges
        for obj in self.root.iter("object"):
            if obj.get("type") == "Bridge" and obj.get("depth") == "0":
                root_key = f"root{root_index}"
                root_index += 1
                bridge_map[root_key] = []
                
                for child in obj:
                    if len(child) != 0 and child.tag == "object" and child.get("type") == "Bridge":
                        parse_bridge(child, root_key)
        
        return bridge_map, bridge_index, root_index
    
    def _process_pci_device(self, obj: ET.Element, bridge_key: str, 
                           pci_device_index: int, nv_switch_index: int):
        """Process a PCI device and map it to components."""
        pci_device_key = f"pci_device{pci_device_index}"
        
        # Map bridge to PCI device
        self.bridge_to_pcidevice.setdefault(bridge_key, []).append(pci_device_key)
        
        # Check if NVSwitch
        if obj.get("subtype") == "NVSwitch":
            nv_switch_key = f"nvlsw{nv_switch_index}"
            self.pcidevice_is_nvslw.setdefault(pci_device_key, []).append(nv_switch_key)
        
        # Map PCI device to component
        pci_type = obj.get("pci_type", "")
        pci_code = pci_type[:4]
        pci_vendor = pci_type[6:10]
        
        if pci_code in XPU_PCI_CLASS or pci_code in NIC_PCI_CLASS:
            component_name = self._get_component_name_from_pci_device(obj, pci_vendor)
            if component_name:
                self.pcidevice_to_component.setdefault(pci_device_key, []).append(component_name)
    
    def _get_component_name_from_pci_device(self, obj: ET.Element, pci_vendor: str) -> str:
        """Extract component name from PCI device element."""
        # Check immediate PCIDevice info
        pci_device_elem = obj.find("info[@name='PCIDevice']")
        if pci_device_elem is not None:
            name = pci_device_elem.get("value").replace("[", "").replace("]", "")
            if name in set(self.gpu_models) or name in set(self.nics):
                return name
        
        # Check for GPUModel in nested info
        for info in obj.findall(".//info"):
            if info.get("name") == "GPUModel":
                return info.get("value")

        # Check for NIC by OSDev/Address
        if obj.find(".//object[@type='OSDev']/info[@name='Address']") is not None:
            return NIC_VENDOR_CLASS.get(pci_vendor)
        
        # add gpu device as vendor name if no info about PCIDevice or GPUModel 
        if pci_vendor in XPU_VENDOR_CLASS:
            return XPU_VENDOR_CLASS[pci_vendor]
        
        return None
    
    def _create_bridge_components(self, root_count: int, bridge_count: int):
        """Create bridge and PCI device components."""
        pci_device_count = sum(
            1 for obj in self.root.findall(".//object[@type='PCIDev']")
            if obj.get("pci_type", "")[:4] in XPU_PCI_CLASS or 
               obj.get("pci_type", "")[:4] in NIC_PCI_CLASS
        )
        
        self.pci = self.device.links.add(name="pci")
        
        self.root_bridge = self.device.components.add(
            name="root_bridge",
            description="root_bridge (depth = 0) closest to the cpu",
            count=root_count
        )
        self.root_bridge.choice = Component.CUSTOM
        self.root_bridge.custom.type = "root_bridge"
        
        self.pci_bridge = self.device.components.add(
            name="pci_bridge",
            description="pci_bridge (depth > 1) connects pci devices or pci_bridges",
            count=bridge_count,
        )
        self.pci_bridge.choice = Component.CUSTOM
        self.pci_bridge.custom.type = "pci_bridge"
        
        self.pci_device = self.device.components.add(
            name="pci_device",
            description="pci_device",
            count=pci_device_count,
        )
        self.pci_device.choice = Component.CUSTOM
        self.pci_device.custom.type = "pci_device"
    
    def _create_topology_edges(self, bridge_map: Dict):
        """Create all topology edges for the device."""
        self._connect_cpu_to_root_bridges()
        self._connect_bridges(bridge_map)
        self._connect_pci_devices_to_bridges()
        self._connect_pci_devices_to_components()
    
    def _connect_cpu_to_root_bridges(self):
        """Connect CPU packages to root bridges."""
        root_index_start = 0
        
        for idx, r_bridges in enumerate(self.package_to_root_map.values()):
            root_index_end = root_index_start + r_bridges
            
            for i in range(root_index_start, root_index_end):
                edge = self.device.edges.add(
                    scheme=DeviceEdge.MANY2MANY,
                    link=self.pci.name
                )
                edge.ep1.component = f"{self.cpu.name}[{idx}]"
                edge.ep2.component = f"{self.root_bridge.name}[{i}]"
            
            root_index_start = root_index_end
    
    def _connect_bridges(self, bridge_map: Dict):
        """Connect bridges according to the hierarchy."""
        for key, children in bridge_map.items():
            if key.startswith("root"):
                root_index = key[4:]
                for child in children:
                    edge = self.device.edges.add(
                        scheme=DeviceEdge.ONE2ONE,
                        link=self.pci.name
                    )
                    edge.ep1.component = f"{self.root_bridge.name}[{root_index}]"
                    edge.ep2.component = f"{self.pci_bridge.name}[{child[10:]}]"
            else:
                bridge_index = key[10:]
                for child in children:
                    edge = self.device.edges.add(
                        scheme=DeviceEdge.ONE2ONE,
                        link=self.pci.name
                    )
                    edge.ep1.component = f"{self.pci_bridge.name}[{bridge_index}]"
                    edge.ep2.component = f"{self.pci_bridge.name}[{child[10:]}]"
    
    def _connect_pci_devices_to_bridges(self):
        """Connect PCI devices to their parent bridges."""
        for bridge_key, pci_devices in self.bridge_to_pcidevice.items():
            bridge_index = bridge_key[10:]
            for pci_device_key in pci_devices:
                edge = self.device.edges.add(
                    scheme=DeviceEdge.MANY2MANY,
                    link=self.pci.name
                )
                edge.ep1.component = f"{self.pci_bridge.name}[{bridge_index}]"
                edge.ep2.component = f"{self.pci_device.name}[{pci_device_key[10:]}]"
    
    def _connect_pci_devices_to_components(self):
        """Connect PCI devices to actual NIC/GPU/NVSwitch components."""
        self._connect_to_nics()
        self._connect_to_gpus()
        self._connect_to_nvswitches()
    
    def _connect_to_nics(self):
        """Connect PCI devices to NIC components."""
        nic_indices = {}
        
        for pci_device_key, components in self.pcidevice_to_component.items():
            pci_device_index = pci_device_key[10:]
            
            for component_name in components:
                clean_name = component_name.replace("[", "").replace("]", "")
                
                if clean_name in self.nic_name_to_component:
                    nic_component = self.nic_name_to_component[clean_name]
                    
                    if clean_name not in nic_indices:
                        nic_indices[clean_name] = 0
                    
                    edge = self.device.edges.add(
                        scheme=DeviceEdge.MANY2MANY,
                        link=self.pci.name
                    )
                    edge.ep1.component = f"{self.pci_device.name}[{pci_device_index}]"
                    edge.ep2.component = f"{nic_component.name}[{nic_indices[clean_name]}]"
                    
                    nic_indices[clean_name] = (nic_indices[clean_name] + 1) % nic_component.count
    
    def _connect_to_gpus(self):
        """Connect PCI devices to GPU components."""
        gpu_indices = {}
        for pci_device_key, components in self.pcidevice_to_component.items():
            pci_device_index = pci_device_key[10:]
            
            for component_name in components:
                clean_name = component_name.replace("[", "").replace("]", "")
                
                if clean_name in self.gpu_name_to_component:
                    gpu_component = self.gpu_name_to_component[clean_name]
                    
                    if clean_name not in gpu_indices:
                        gpu_indices[clean_name] = 0
                    
                    edge = self.device.edges.add(
                        scheme=DeviceEdge.MANY2MANY,
                        link=self.pci.name
                    )
                    edge.ep1.component = f"{self.pci_device.name}[{pci_device_index}]"
                    edge.ep2.component = f"{gpu_component.name}[{gpu_indices[clean_name]}]"
                    
                    gpu_indices[clean_name] = (gpu_indices[clean_name] + 1) % gpu_component.count
    
    def _connect_to_nvswitches(self):
        """Connect PCI devices that are NVSwitches."""
        for pci_device_key, nvswitches in self.pcidevice_is_nvslw.items():
            pci_device_index = pci_device_key[10:]
            
            for nvswitch_key in nvswitches:
                edge = self.device.edges.add(
                    scheme=DeviceEdge.MANY2MANY,
                    link=self.pci.name
                )
                edge.ep1.component = f"{self.pci_device.name}[{pci_device_index}]"
                edge.ep2.component = f"{self.nvlsw.name}[{nvswitch_key[5:]}]"


def parse_lstopo_xml(file_path: str) -> Device:
    """Parse lstopo XML file and return Device object."""
    parser = LstopoParser(file_path)
    return parser.parse()

def run(input_path: str, output: str = "yaml"):
    device = parse_lstopo_xml(input_path)
    return device.serialize(output)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Parse lstopo XML and generate device topology"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="yaml",
        choices=["json", "yaml", "dict"],
        help="Output format (json, yaml, or dict)"
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to lstopo XML file"
    )
    
    args = parser.parse_args()
    print(run(args.input, args.output))