import os
import shutil
import yaml
import json
from json import JSONDecodeError
from yaml import YAMLError
from infragraph import Infrastructure, Annotation
from infragraph.infragraph_service import InfraGraphService

class Visualizer:
    """Builds vis.js-ready view JSON for an infrastructure graph and writes
    a static visualization bundle to disk."""

    # metadata
    NODE_STYLES = {
        "switch_dev":  {"shape": "image", "image": "svg_images/switch_dev.svg", "size": 20},
        "switch":      {"shape": "image", "image": "svg_images/switch.svg",     "size": 12},
        "server":      {"shape": "image", "image": "svg_images/server.svg",     "size": 22},
        "host":        {"shape": "image", "image": "svg_images/device.svg",     "size": 22},
        "dgx":         {"shape": "box",   "size": 30, "color": "#9b59b6"},
        "cpu":         {"shape": "image", "image": "svg_images/cpu.svg",        "size": 32},
        "xpu":         {"shape": "image", "image": "svg_images/xpu.svg",        "size": 18},
        "nic":         {"shape": "image", "image": "svg_images/nic.svg",        "size": 18},
        "memory":      {"shape": "image", "image": "svg_images/memory.svg",     "size": 18},
        "port":        {"shape": "image", "image": "svg_images/port.svg",       "size": 12},
        "pcie_slot":   {"shape": "image", "image": "svg_images/pcie_slot.svg",  "size":  12},
        "device":      {"shape": "image", "image": "svg_images/device.svg",     "size": 25},
        "custom":      {"shape": "dot",   "color": "#7f8c8d",                   "size": 22},
        "pci_bridge":  {"shape": "image", "image": "svg_images/pcie_bridge.svg", "size": 12},
        "root_bridge": {"shape": "image", "image": "svg_images/pcie_bridge.svg", "size": 12},
        "pci_device":  {"shape": "image", "image": "svg_images/pcie_slot.svg",  "size":  5},
    }

    LINK_COLORS = {
        "pcie": "#9F7D7D", "nvlink": "#6D6A7D", "xpu_fabric": "#528578",
        "cpu_fabric": "#819EBD", "fabric": "#5395DC", "ic": "#B27C5A",
        "serdes": "#72928C", "electrical": "#C3554F", "internal_binding": "#888888",
    }

    def __init__(self, service=None, output="./viz", hosts=(), switches=()):
        """
        entry point to visualizer
        Params:
            infrastructure: Infrastructure object
            annotations: Optional Annotation object/dict/str applied to the graph.
            output: Output directory path
            hosts: Host names
            switches: Switch names
        """
        self.service = service
        self.output = output
        self.host_names = self._split_names(hosts)
        self.switch_names = self._split_names(switches)
        self.all_device_names = set()
        self.output_dir = None

        print(f"Infrastructure: {self.service.infrastructure.name}")
        print(f"  Devices: {list(self.service._device_data.keys())}")
        print(f"  Instances: {[(i.name, i.count) for i in self.service.infrastructure.instances]}")
        print(f"  Host devices: {self.host_names}")
        print(f"  Switch devices: {self.switch_names}")
        graph_attrs = self.service.get_networkx_graph().graph
        if graph_attrs:
            print(f"  Graph annotations: {graph_attrs}")


        # Generate all views
        print(f"\nGenerating graph data:")
        all_views = {}
        self.all_device_names = set(self.service._device_data.keys())

        #infrastructure view
        infra_json = self._generate_instance_json()
        all_views["infrastructure.json"] = infra_json
        print(f"  Generated: infrastructure.json ({len(infra_json['nodes'])} nodes, {len(infra_json['edges'])} edges)")

        #device view
        for device_name, device_data in self.service._device_data.items():
            dev_json = self._generate_component_json(device_name, device_data)
            all_views[f"{device_name}.json"] = dev_json
            print(f"  Generated: {device_name}.json ({len(dev_json['nodes'])} nodes, {len(dev_json['edges'])} edges)")

        self.output_dir = os.path.abspath(self.output)
        os.makedirs(self.output_dir, exist_ok=True)
        self._copy_frontend()

        # Write graph_data.js
        js_path = os.path.join(self.output_dir, "js", "graph_data.js")
        with open(js_path, "w") as f:
            f.write("// Auto-generated\nconst GRAPH_DATA = ")
            json.dump(all_views, f, indent=2)
            f.write(";\n")
        print(f"  Generated: js/graph_data.js ({len(all_views)} views embedded)")
        print(f"\nVisualization ready at: {self.output_dir}/index.html")

    # helper functions
    def _get_link_color(self, link_name):
        """set the color of the links according to their names"""
        for key, color in self.LINK_COLORS.items():
            if key in link_name.lower():
                return color
        return "#CCCCCC"

    def _get_style(self, key):
        """svg images for nodes or custom"""
        return self.NODE_STYLES.get(key, self.NODE_STYLES["custom"])

    @staticmethod
    def _collapse_parallel_edges(edges):
        """Collapse parallel edges between same node pair into xN labels."""
        grouped = {}
        for e in edges:
            key = (min(e["from"], e["to"]), max(e["from"], e["to"]), e.get("link", ""))     #undirected edges
            if key not in grouped:
                grouped[key] = {"edge": e.copy(), "count": 0}
            grouped[key]["count"] += 1

        result = []
        for key, val in grouped.items():
            e = val["edge"]
            count = val["count"]
            e["label"] = f"×{count} {e.get('link', '')}" if count > 1 else e.get("link","")
            e["width"] = min(1 + count, 6) if count > 1 else 1
            result.append(e)
        return result

    @staticmethod
    def _map_to_parent(node_id):
        """Map a composed device sub-component to its parent device node.
        e.g., 'cx5_100gbe.0.pcie_endpoint.0' → 'cx5_100gbe.0'"""
        parts = node_id.split(".")
        if len(parts) >= 2:
            parent = parts[0] + "." + parts[1]
        return parent

    @staticmethod
    def _split_names(names):
        """split at comma
        Params:
                names: input names of hosts and switches"""
        if isinstance(names, str):
            names = (names,)
        result = []
        for name in (names or ()):
            for part in name.split(","):
                part = part.strip()
                if part:
                    result.append(part)
        return result

    def _extra_attrs_text(self, attrs, exclude=()):
        """Format annotation attributes (i.e. everything but the immutable,
        already-shown ones) for a hover tooltip."""
        immutable = self.service._IMMUTABLE_ATTRIBUTES
        lines = [
            f"{k}: {v}" for k, v in attrs.items()
            if k not in immutable and k not in exclude
        ]
        return "\n".join(lines)

    def _generate_component_json(self, device_name, device_data):
        """Generate a device component view JSON from a DeviceData object.
        Params:
            device_name (str): Name of the device (e.g., "dgx_a100").
            device_data (DeviceData): Object with .nodes, .edges, .components attributes.
        Returns:
            dict: vis.js-ready JSON with "nodes" and "edges" keys."""
        comp_descriptions = {}
        for device in self.service.infrastructure.devices:
            if device.name == device_name:
                for comp in device.components:
                    comp_descriptions[comp.name] = comp.description
                break

        # Annotation attributes live on the real graph nodes/edges, which are
        # qualified with an instance prefix (e.g. "dgx_h100.0.xpu.0"). This view
        # is shared across all instances of device_name, so we show the first
        # instance's attributes.
        G = self.service.get_networkx_graph()
        first_instance = next((i for i in self.service.infrastructure.instances if i.device == device_name), None)
        instance_prefix = f"{first_instance.name}.0." if first_instance is not None else None

        nodes = []
        for node_id, node_type in device_data.nodes.items():
            parts = node_id.split(".")
            # Skip composed device sub-components at this level (e.g., cx5_100gbe.0.pcie_endpoint.0)
            if len(parts) > 2:
                continue

            comp_name = parts[0]
            drillable = node_type == "device" and comp_name in self.all_device_names
            style = self._get_style(node_type)
            desc = comp_descriptions.get(comp_name, "")

            title = f"Component: {node_id}\nType: {node_type}\nDescription: {desc}"
            if instance_prefix is not None:
                extra = self._extra_attrs_text(G.nodes.get(instance_prefix + node_id, {}))
                if extra:
                    title += "\n" + extra

            nodes.append({
                "id": node_id,
                "label": f"{comp_name}[{parts[1]}]",
                "title": title,
                "type": node_type,
                "shape": style.get("shape", "dot"),
                "image": style.get("image"),
                "size": style.get("size", 16),
                "drillable": drillable,
                "drillTarget": f"{comp_name}.json" if drillable else None,
            })

        # Build edges : map composed device sub-components to parent nodes
        node_ids = {n["id"] for n in nodes}
        raw_edges = []
        seen = set()

        for src, edge_list in device_data.edges.items():
            src_mapped = src if src in node_ids else self._map_to_parent(src)
            if not src_mapped or src_mapped not in node_ids:
                continue
            for dst, link in edge_list:
                dst_mapped = dst if dst in node_ids else self._map_to_parent(dst)
                if not dst_mapped or dst_mapped not in node_ids:
                    continue
                edge_key = (min(src_mapped, dst_mapped), max(src_mapped, dst_mapped), link)
                if edge_key in seen:
                    continue
                seen.add(edge_key)

                title = f"Link: {link}"
                if instance_prefix is not None:
                    edge_data = G.get_edge_data(instance_prefix + src, instance_prefix + dst, default={})
                    extra = self._extra_attrs_text(edge_data, exclude={"link"})
                    if extra:
                        title += "\n" + extra

                raw_edges.append({
                    "from": src_mapped, "to": dst_mapped, "link": link,
                    "color": self._get_link_color(link), "title": title, "label":link,
                })

        return {
            "nodes": nodes,
            "edges": self._collapse_parallel_edges(raw_edges),
        }

    def _generate_instance_json(self):
        """Generate the top-level infrastructure view JSON.
        returns:
            dict: vis.js-ready JSON with "nodes" and "edges" keys."""
        G = self.service.get_networkx_graph()

        # Instance nodes
        nodes = []
        for instance in self.service.infrastructure.instances:
            device_name = instance.device
            for idx in range(instance.count):
                is_host = device_name in self.host_names
                is_switch = device_name in self.switch_names
                node_type = "host" if is_host else ("switch" if is_switch else "other")
                drillable = device_name in self.service._device_data

                if is_switch:
                    style = self.NODE_STYLES["switch_dev"]
                elif is_host:
                    style = self.NODE_STYLES.get(device_name, self.NODE_STYLES.get(instance.name, self.NODE_STYLES["host"]))
                else:
                    style = self.NODE_STYLES["custom"]

                nodes.append({
                    "id": f"{instance.name}_{idx}",
                    "label": f"{instance.name}[{idx}]",
                    "title": f"Device: {device_name}\nInstance: {instance.name}[{idx}]\nType: {node_type}",
                    "type": node_type, "device": device_name,
                    "shape": style.get("shape", "dot"), "image": style.get("image"),
                    "color": style.get("color"), "size": style.get("size", 16),
                    "drillable": drillable,
                    "drillTarget": f"{device_name}.json" if drillable else None,
                })

        # Infrastructure edges from NetworkX graph
        raw_edges = []
        for u, v, data in G.edges(data=True):
            u_parts = u.split(".")
            v_parts = v.split(".")
            u_inst = f"{u_parts[0]}_{u_parts[1]}"
            v_inst = f"{v_parts[0]}_{v_parts[1]}"
            if u_inst == v_inst:
                continue

            link = data.get("link", "unknown")
            bw = ""
            for infra_link in self.service.infrastructure.links:
                if infra_link.name == link:
                    if hasattr(infra_link, 'physical') and infra_link.physical is not None:
                        bw_obj = infra_link.physical.bandwidth
                        if hasattr(bw_obj, 'gigabits_per_second') and bw_obj.gigabits_per_second:
                            bw = f" ({bw_obj.gigabits_per_second}G)"
                    break

            title = f"Link: {link}{bw}"
            extra = self._extra_attrs_text(data, exclude={"link"})
            if extra:
                title += "\n" + extra

            raw_edges.append({
                "from": u_inst, "to": v_inst, "link": link,
                "color": self._get_link_color(link), "title": title,"label":link,
            })

        return {
            "nodes": nodes,
            "edges": self._collapse_parallel_edges(raw_edges),
        }

    @staticmethod
    def _load_infrastructure(input_file):
        """load the yaml/json file
        Params:
                input_file: given yaml/json file
                infrastructure: infrastructure object"""
        if not input_file:
            raise ValueError("Either input_file or infrastructure must be provided")
        try:
            with open(input_file, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except (JSONDecodeError, ValueError):
                    f.seek(0)
                    data = yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Input file not found: '{input_file}'")
        except YAMLError as e:
            raise ValueError(f"Invalid YAML in '{input_file}': {e}")


        infrastructure = Infrastructure()
        annotations = None
        if "infrastructure" and "annotations" in data:
            infrastructure.deserialize(data["infrastructure"])
            if "annotations" in data and len(data["annotations"]) > 0:
                annotations = Annotation()
                annotations.deserialize(data["annotations"])
        else:
            infrastructure.deserialize(data)
        return infrastructure, annotations

    #copying the frontend files to user's output directory
    def _copy_frontend(self):
        """Copy frontend files to the output directory."""
        frontend_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
        for item in ["index.html", "css", "js", "svg_images"]:
            src = os.path.join(frontend_src, item)
            if not os.path.exists(src):
                continue
            dst = os.path.join(self.output_dir, item)
            if os.path.isdir(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)


def run_visualizer(input_file=None, infrastructure=None, annotations=None, output="./viz", hosts=(), switches=()):
    """
    entry point to visualizer
    Params:
        input_file: Path to YAML/JSON file. May hold a plain infrastructure
            definition, or the combined infrastructure+annotations structure
            returned by get_graph(INFRAGRAPH). Ignored if infrastructure is given.
        infrastructure: Infrastructure object
        annotations: Optional Annotation object/dict/str applied to the graph.
            Takes precedence over any annotations loaded from input_file.
        output: Output directory path
        hosts: Host names
        switches: Switch names
    """
    if infrastructure is None:
        # Load infrastructure (file may hold a plain infrastructure definition,
        # or the combined infrastructure+annotations structure from get_graph)
        infrastructure, loaded_annotations = Visualizer._load_infrastructure(input_file)
        if annotations is None:
            annotations = loaded_annotations

    service = InfraGraphService()
    service.set_graph(infrastructure)
        # set the annotations here
    if annotations is not None:
        service.annotate_graph(annotations)
    Visualizer(service, output=output, hosts=hosts, switches=switches)
