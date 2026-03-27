import os
import shutil
import yaml
import json
from json import JSONDecodeError
from yaml import YAMLError
from infragraph import Infrastructure
from infragraph.infragraph_service import InfraGraphService

# metadata
NODE_STYLES = {
    "switch_dev":  {"shape": "image", "image": "svg_images/switch_dev.svg", "size": 10},
    "switch":      {"shape": "image", "image": "svg_images/switch.svg",     "size": 12},
    "server":      {"shape": "image", "image": "svg_images/server.svg",     "size": 22},
    "host":        {"shape": "image", "image": "svg_images/device.svg",     "size": 22},
    "dgx":         {"shape": "box",   "size": 30, "color": "#9b59b6"},
    "cpu":         {"shape": "image", "image": "svg_images/cpu.svg",        "size": 32},
    "xpu":         {"shape": "image", "image": "svg_images/xpu.svg",        "size": 18},
    "nic":         {"shape": "image", "image": "svg_images/nic.svg",        "size": 18},
    "memory":      {"shape": "image", "image": "svg_images/memory.svg",     "size": 18},
    "port":        {"shape": "image", "image": "svg_images/port.svg",       "size": 12},
    "pcie_slot":   {"shape": "image", "image": "svg_images/pcie_slot.svg",  "size":  5},
    "device":      {"shape": "image", "image": "svg_images/device.svg",     "size": 18},
    "custom":      {"shape": "dot",   "color": "#7f8c8d",                   "size": 22},
    "pci_bridge":  {"shape": "image", "image": "svg_images/pci_bridge.svg", "size": 12},
    "root_bridge": {"shape": "image", "image": "svg_images/pci_bridge.svg", "size": 12},
    "pci_device":  {"shape": "image", "image": "svg_images/pcie_slot.svg",  "size":  5},
}

LINK_COLORS = {
    "pcie": "#9F7D7D", "nvlink": "#6D6A7D", "xpu_fabric": "#528578",
    "cpu_fabric": "#819EBD", "fabric": "#5395DC", "ic": "#B27C5A",
    "serdes": "#72928C", "electrical": "#C3554F", "internal_binding": "#888888",
}

# helper functions
def _get_link_color(link_name):
    """set the color of the links according to their names"""
    for key, color in LINK_COLORS.items():
        if key in link_name.lower():
            return color
    return "#CCCCCC"


def _get_style(key):
    """svg images for nodes or custom"""
    return NODE_STYLES.get(key, NODE_STYLES["custom"])


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
        e["label"] = f"\u00d7{count} {e.get('link', '')}" if count > 1 else None
        e["width"] = min(1 + count, 6) if count > 1 else 1
        result.append(e)
    return result



def _map_to_parent(node_id):
    """Map a composed device sub-component to its parent device node.
    e.g., 'cx5_100gbe.0.pcie_endpoint.0' → 'cx5_100gbe.0'"""
    parts = node_id.split(".")
    if len(parts) >= 2:
        parent = parts[0] + "." + parts[1]
    return parent


 

def _generate_component_json(device_name, device_data, all_device_names,infrastructure):
    """Generate a device component view JSON from a DeviceData object.
    Params:     
        device_name (str): Name of the device (e.g., "dgx_a100").
        device_data (DeviceData): Object with .nodes, .edges, .components attributes.
        all_device_names (set[str]): All device names in the infrastructure,
            used to determine which components are drillable.
    Returns:
        dict: vis.js-ready JSON with "nodes" and "edges" keys."""
    comp_descriptions = {}
    for device in infrastructure.devices:
        if device.name == device_name:
            for comp in device.components:
                comp_descriptions[comp.name] = comp.description
            break
    nodes = []
    for node_id, node_type in device_data.nodes.items():
        parts = node_id.split(".")
        # Skip composed device sub-components at this level (e.g., cx5_100gbe.0.pcie_endpoint.0)
        if len(parts) > 2:
            continue

        comp_name = parts[0]
        drillable = node_type == "device" and comp_name in all_device_names
        style = _get_style(node_type)
        desc = comp_descriptions.get(comp_name, "")


        nodes.append({
            "id": node_id,
            "label": f"{comp_name}[{parts[1]}]",
            "title": f"Component: {node_id}\nType: {node_type}\nDescription: {desc}",
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
        src_mapped = src if src in node_ids else _map_to_parent(src)
        if not src_mapped or src_mapped not in node_ids:
            continue
        for dst, link in edge_list:
            dst_mapped = dst if dst in node_ids else _map_to_parent(dst)
            if not dst_mapped or dst_mapped not in node_ids:
                continue
            edge_key = (min(src_mapped, dst_mapped), max(src_mapped, dst_mapped), link)
            if edge_key in seen:
                continue
            seen.add(edge_key)
            raw_edges.append({
                "from": src_mapped, "to": dst_mapped, "link": link,
                "color": _get_link_color(link), "title": f"Link: {link}",
            })

    return {
        "nodes": nodes,
        "edges": _collapse_parallel_edges(raw_edges),
    }




def _generate_instance_json(infrastructure, service, host_names, switch_names):
    """Generate the top-level infrastructure view JSON.
    Params:
        infrastructure (Infrastructure): The infrastructure object.
        service (InfraGraphService): Service with graph already set.
        host_names (list[str]): Device names flagged as hosts (for styling).
        switch_names (list[str]): Device names flagged as switches (for styling).
        
    returns:
        dict: vis.js-ready JSON with "nodes" and "edges" keys."""
    G = service.get_networkx_graph() 

    # Instance nodes
    nodes = []
    for instance in infrastructure.instances:
        device_name = instance.device
        for idx in range(instance.count):
            is_host = device_name in host_names
            is_switch = device_name in switch_names
            node_type = "host" if is_host else ("switch" if is_switch else "other")
            drillable = device_name in service._device_data

            if is_switch:
                style = NODE_STYLES["switch_dev"]
            elif is_host:
                style = NODE_STYLES.get(device_name, NODE_STYLES.get(instance.name, NODE_STYLES["host"]))
            else:
                style = NODE_STYLES["custom"]

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
        for infra_link in infrastructure.links:
            if infra_link.name == link:
                if hasattr(infra_link, 'physical') and infra_link.physical is not None:
                    bw_obj = infra_link.physical.bandwidth
                    if hasattr(bw_obj, 'gigabits_per_second') and bw_obj.gigabits_per_second:
                        bw = f" ({bw_obj.gigabits_per_second}G)"
                break

        raw_edges.append({
            "from": u_inst, "to": v_inst, "link": link,
            "color": _get_link_color(link), "title": f"Link: {link}{bw}",
        })

    return {
        "nodes": nodes,
        "edges": _collapse_parallel_edges(raw_edges),
    }



def run_visualizer(input_file=None, infrastructure=None, output="./viz", hosts=(), switches=()):
    """
    entry point to visualizer
    Params:
        input_file: Path to YAML/JSON file 
        infrastructure: Infrastructure object 
        output: Output directory path
        hosts: Host names
        switches: Switch names
    """
    # Normalize host/switch names
    host_names = _split_names(hosts)
    switch_names = _split_names(switches)

    # Load infrastructure
    infra = _load_infrastructure(input_file, infrastructure)
    service = InfraGraphService()
    service.set_graph(infra)

    print(f"Infrastructure: {infra.name}")
    print(f"  Devices: {list(service._device_data.keys())}")
    print(f"  Instances: {[(i.name, i.count) for i in infra.instances]}")
    print(f"  Host devices: {host_names}")
    print(f"  Switch devices: {switch_names}")
    

    # Generate all views
    print(f"\nGenerating graph data:")
    all_views = {}
    all_device_names = set(service._device_data.keys())

    #infrastructure view
    infra_json = _generate_instance_json(infra, service, host_names, switch_names)
    all_views["infrastructure.json"] = infra_json
    print(f"  Generated: infrastructure.json ({len(infra_json['nodes'])} nodes, {len(infra_json['edges'])} edges)")

    #device view
    for device_name, device_data in service._device_data.items():
        dev_json = _generate_component_json(device_name, device_data, all_device_names,infra)
        all_views[f"{device_name}.json"] = dev_json
        print(f"  Generated: {device_name}.json ({len(dev_json['nodes'])} nodes, {len(dev_json['edges'])} edges)")

    output_dir = os.path.abspath(output)
    os.makedirs(output_dir, exist_ok=True)
    _copy_frontend(output_dir)

    # Write graph_data.js
    js_path = os.path.join(output_dir, "js", "graph_data.js")
    with open(js_path, "w") as f:
        f.write("// Auto-generated\nconst GRAPH_DATA = ")
        json.dump(all_views, f, indent=2)
        f.write(";\n")
    print(f"  Generated: js/graph_data.js ({len(all_views)} views embedded)")
    print(f"\nVisualization ready at: {output_dir}/index.html")



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


def _load_infrastructure(input_file, infrastructure):
    """load the yaml/json file
    Params: 
            input_file: given yaml/json file
            infrastructure: infrastructure object"""
    if infrastructure is not None:
        return infrastructure
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
    infra = Infrastructure()
    infra.deserialize(data)
    return infra


#copying the frontend files to user's output directory
def _copy_frontend(output_dir):
    """Copy frontend files to the output directory.
    Params: 
            output_dir: given output path"""
    frontend_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
    for item in ["index.html", "css", "js", "svg_images"]:
        src = os.path.join(frontend_src, item)
        if not os.path.exists(src):
            continue
        dst = os.path.join(output_dir, item)
        if os.path.isdir(src):
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)