import os
import shutil
import yaml
import json
import networkx as nx
from json import JSONDecodeError
from yaml import YAMLError
from infragraph import Infrastructure
from infragraph.infragraph_service import InfraGraphService

# metadata
NODE_STYLES = {
    "switch_dev":  {"shape": "image", "image": "svg_images/switch_dev.svg", "size": 20},
    "switch":      {"shape": "image", "image": "svg_images/switch.svg",     "size": 12},
    "server":      {"shape": "image", "image": "svg_images/server.svg",     "size": 22},
    "host":        {"shape": "image", "image": "svg_images/device.svg",     "size": 22},
    "rack":         {"shape": "box",   "size": 30, "color": "#9b59b6"},
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

def _instance_edges(G, infrastructure):
    bw_map = {}
    for l in infrastructure.links:
        phys = getattr(l, "physical", None)
        bw_obj = getattr(phys, "bandwidth", None) if phys is not None else None
        gbps = getattr(bw_obj, "gigabits_per_second", None) if bw_obj else None
        bw_map[l.name] = f" ({gbps}G)" if gbps else ""

    edges = []
    for u, v, data in G.edges(data=True):
        up, vp = u.split("."), v.split(".")
        u_inst, v_inst = f"{up[0]}_{up[1]}", f"{vp[0]}_{vp[1]}"
        if u_inst == v_inst:
            continue
        link = data.get("link", "unknown")
        edges.append({
            "from": u_inst, "to": v_inst, "link": link,
            "color": _get_link_color(link),
            "title": f"Link: {link}{bw_map.get(link, '')}", "label": link,
        })
    return edges

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

def _build_instance_nodes_edges(infrastructure, service, host_names,
                                switch_names):
    """Build instance-level nodes and edges with no rack collapsing.
    This is the un-racked infrastructure view; _compute_racks consumes it,
    and _generate_instance_json wraps it with rack collapsing.
    Returns:
        tuple: (nodes, edges) -- lists of dicts. Nodes carry a 'type' field
            ('host', 'switch', 'other') used by rack grouping.
    """
    G = service.get_networkx_graph()

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
                style = NODE_STYLES.get(device_name,
                        NODE_STYLES.get(instance.name, NODE_STYLES["host"]))
            else:
                style = NODE_STYLES["custom"]

            nodes.append({
                "id": f"{instance.name}_{idx}",
                "label": f"{instance.name}[{idx}]",
                "title": (f"Device: {device_name}\n"
                          f"Instance: {instance.name}[{idx}]\nType: {node_type}"),
                "type": node_type, "device": device_name,
                "shape": style.get("shape", "dot"),
                "image": style.get("image"),
                "color": style.get("color"), "size": style.get("size", 16),
                "drillable": drillable,
                "drillTarget": f"{device_name}.json" if drillable else None,
            })

    edges = _instance_edges(G, infrastructure)
    return nodes, edges

def _compute_racks(instance_nodes, instance_edges):
    """Group each host with its directly-connected neighbours (and hosts
    sharing those neighbours) into racks. Uses the already-built instance-level
    nodes and edges, so no walking of G.
    Params:
        instance_nodes (list[dict]): instance-level nodes with a 'type' field
            ('host', 'switch', 'other') already set by the generator.
        instance_edges (list[dict]): instance-level edges with 'from'/'to'.
    Returns:
        list[dict]: each {"id": "rack_N", "members": sorted[str]}.
    """
    host_insts = {n["id"] for n in instance_nodes if n["type"] == "host"}

    # adjacency of host-incident edges only -> traversal stops at the leaf tier
    uplink = nx.Graph()
    for e in instance_edges:
        if e["from"] in host_insts or e["to"] in host_insts:
            uplink.add_edge(e["from"], e["to"])

    racks = []
    for component in nx.connected_components(uplink):
        if component & host_insts:
            racks.append({"members": sorted(component)})
    racks.sort(key=lambda r: r["members"][0])
    for i, rack in enumerate(racks):
        rack["id"] = f"rack_{i}"
    return racks

def _generate_instance_json(instance_nodes, instance_edges, racks):
    """Generate the top-level infrastructure view by collapsing racked
    instances into single rack nodes.
    Params:
        instance_nodes (list[dict]): from _build_instance_nodes_edges.
        instance_edges (list[dict]): from _build_instance_nodes_edges.
        racks (list[dict]): output of _compute_racks.
    Returns:
        dict: vis.js-ready JSON with "nodes" and "edges" keys.
    """
    member_to_rack = {m: r["id"] for r in racks for m in r["members"]}

    nodes = []

    # one node per rack
    for rack in racks:
        style = _get_style("rack")
        nodes.append({
            "id": rack["id"],
            "label": f"rack[{rack['id'].split('_')[1]}]",
            "title": f"Rack: {rack['id']}\nInstances: {len(rack['members'])}",
            "type": "rack", "device": "rack",
            "shape": style.get("shape", "dot"),
            "image": style.get("image"),
            "color": style.get("color"), "size": style.get("size", 48),
            "drillable": True,
            "drillTarget": f"{rack['id']}.json",
        })

    # pass-through: instances not absorbed into any rack
    for n in instance_nodes:
        if n["id"] not in member_to_rack:
            nodes.append(n)

    # edges: remap racked endpoints to their rack, drop intra-rack edges
    raw_edges = []
    for e in instance_edges:
        f = member_to_rack.get(e["from"], e["from"])
        t = member_to_rack.get(e["to"], e["to"])
        if f == t:
            continue
        raw_edges.append({**e, "from": f, "to": t})

    return {"nodes": nodes, "edges": _collapse_parallel_edges(raw_edges)}

def _generate_rack_json(rack, service, host_names, switch_names,
                        inst_device, rack_edge_list):
    """Generate the drill-down view JSON for one rack.
    Params:
        rack_edge_list (list[dict]): pre-filtered edges with both endpoints
            inside this rack (built once in run_visualizer, not re-walked).
    """
    members = set(rack["members"])

    nodes = []
    for inst_id in sorted(members):
        device_name = inst_device.get(inst_id, "")
        name, idx = inst_id.rsplit("_", 1)
        is_host = device_name in host_names
        is_switch = device_name in switch_names
        node_type = "host" if is_host else ("switch" if is_switch else "other")

        if is_switch:
            style = NODE_STYLES["switch_dev"]
        elif is_host:
            style = NODE_STYLES.get(device_name,
                    NODE_STYLES.get(name, NODE_STYLES["host"]))
        else:
            style = NODE_STYLES["custom"]

        drillable = device_name in service._device_data
        nodes.append({
            "id": inst_id,
            "label": f"{name}[{idx}]",
            "title": (f"Device: {device_name}\nInstance: {name}[{idx}]\n"
                      f"Type: {node_type}\nRack: {rack['id']}"),
            "type": node_type, "device": device_name,
            "shape": style.get("shape", "dot"),
            "image": style.get("image"),
            "color": style.get("color"), "size": style.get("size", 16),
            "drillable": drillable,
            "drillTarget": f"{device_name}.json" if drillable else None,
        })

    return {"nodes": nodes,
            "edges": _collapse_parallel_edges(rack_edge_list)}

def run_visualizer(input_file=None, infrastructure=None, output="./viz",
                   hosts=(), switches=()):
    """Entry point to the visualizer.
    Params:
        input_file: Path to YAML/JSON file.
        infrastructure: Infrastructure object.
        output: Output directory path.
        hosts: Host device names.
        switches: Switch device names.
    """
    host_names = _split_names(hosts)
    switch_names = _split_names(switches)

    infra = _load_infrastructure(input_file, infrastructure)
    service = InfraGraphService()
    service.set_graph(infra)

    print(f"Infrastructure: {infra.name}")

    # instance id -> device name, used when building rack drill-down nodes
    inst_device = {}
    for instance in infra.instances:
        for idx in range(instance.count):
            inst_device[f"{instance.name}_{idx}"] = instance.device

    print(f"\nGenerating graph data:")
    all_views = {}
    all_device_names = set(service._device_data.keys())

    # build instance-level data ONCE; reused for racks and the top view
    instance_nodes, instance_edges = _build_instance_nodes_edges(
        infra, service, host_names, switch_names)

    # compute racks from the instance-level data (no walking of G)
    racks = _compute_racks(instance_nodes, instance_edges)

    # bucket instance edges by rack ONCE -- no per-rack re-walking of G
    member_to_rack = {m: r["id"] for r in racks for m in r["members"]}
    rack_edges = {r["id"]: [] for r in racks}
    for e in instance_edges:
        f_rack = member_to_rack.get(e["from"])
        t_rack = member_to_rack.get(e["to"])
        if f_rack and f_rack == t_rack:
            rack_edges[f_rack].append(e)

    # infrastructure view (racks collapsed)
    infra_json = _generate_instance_json(instance_nodes, instance_edges, racks)
    all_views["infrastructure.json"] = infra_json
    print(f"  Generated: infrastructure.json "
          f"({len(infra_json['nodes'])} nodes, {len(infra_json['edges'])} edges)")

    # rack drill-down views -- each rack gets its pre-filtered edges
    for rack in racks:
        rack_json = _generate_rack_json(
            rack, service, host_names, switch_names,
            inst_device, rack_edges[rack["id"]])
        all_views[f"{rack['id']}.json"] = rack_json

    # device views (unchanged)
    for device_name, device_data in service._device_data.items():
        dev_json = _generate_component_json(device_name, device_data,
                                            all_device_names, infra)
        all_views[f"{device_name}.json"] = dev_json
        print(f"  Generated: {device_name}.json "
              f"({len(dev_json['nodes'])} nodes, {len(dev_json['edges'])} edges)")

    output_dir = os.path.abspath(output)
    os.makedirs(output_dir, exist_ok=True)
    _copy_frontend(output_dir)

    js_path = os.path.join(output_dir, "js", "graph_data.js")
    with open(js_path, "w") as f:
        f.write("// Auto-generated\n")
        f.write("const GRAPH_DATA = ")
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