"""

Python slice notation is a concise and powerful syntax for extracting a subset of elements from a sequence such as a list, tuple, or string. It uses square brackets with up to three optional parameters separated by colons inside: start:stop:step.
- start is the index where the slice begins (inclusive). Defaults to 0 if omitted.
- stop is the index where the slice ends (exclusive). Defaults to the length of the sequence if omitted.
- step is the interval between elements in the slice. Defaults to 1 and can be negative for reversing the sequence.

"""

import re
import json
import yaml
import warnings
import networkx
from networkx import Graph
from networkx.readwrite import json_graph
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union
from itertools import product as iterproduct
from infragraph import *


class GraphError(Exception):
    """Custom exception for graph-related errors."""
    pass

class InfrastructureError(Exception):
    """Custom exception for infrastructure related errors"""
    pass

class DeviceData:
    def __init__(self):
        self.nodes = {}
        self.components = {}
        self.edges = {}
        self.links = {}
    
    def add_edge(self, ep1, ep2, link):
        if ep1 in self.edges:
            self.edges[ep1].append((ep2, link))
        else:
            self.edges[ep1] = [(ep2, link)]

class InfraGraphService(Api):
    """InfraGraph Services"""

    _IMMUTABLE_ATTRIBUTES: frozenset[str] = frozenset(
        {"type", "instance", "instance_idx", "device", "composed_device", "link"}
    )

    # Short forms for physical link unit choices used in edge attribute strings.
    _UNIT_ABBREVIATIONS: Dict[str, str] = {
        "gigabits_per_second": "Gbps",
        "gigabytes_per_second": "GBps",
        "gigatransfers_per_second": "GT/s",
        "ms": "ms",
        "us": "us",
        "ns": "ns",
    }

    def __init__(self):
        super().__init__()
        self._graph: Graph = Graph()
        self._device_data = {}
        self._graph_node_prefix_map: Dict[str, List[str]] = {}
        self._link_to_edges_map: Dict[str, List[Tuple[str, str]]] = {}
        self._infrastructure: Infrastructure = Infrastructure()

    @property
    def infrastructure(self) -> Infrastructure:
        """Return the current backing store infrastructure"""
        return self._infrastructure

    def get_openapi_schema(self) -> str:
        """Returns the InfraGraph openapi.yaml schema definition"""
        with open("docs/openapi.yaml", "rt", encoding="utf-8") as fp:
            return fp.read()

    def get_networkx_graph(self) -> Graph:
        """Returns the current infrastructure as a networkx graph object."""
        if self._graph is None:
            raise ValueError("The networkx graph has not been created. Please call set_graph() first.")
        return self._graph

    def _expand_node_string(self, s: str) -> List[str]:
        """Expand a device/component string with slice notation into dot-notation paths.

        Format: name[start:stop]name[start:stop]...
        Each [start:stop] expands like range(start, stop). Segments without a slice
        are kept as-is. Results are the cartesian product of all segment expansions,
        joined with '.'.

        Examples:
            "dgx"              -> ["dgx"]
            "dgx[0:3]"         -> ["dgx.0", "dgx.1", "dgx.2"]
            "dgx[0:2]cpu[0:2]" -> ["dgx.0.cpu.0", "dgx.0.cpu.1",
                                    "dgx.1.cpu.0", "dgx.1.cpu.1"]
        """
        if not s:
            return []


        if "." in s:
            return [s]
        # Parse the input string into (name, start, stop) tuples.
        # The regex matches a name (alphanumeric/underscore/hyphen) optionally
        # followed by a slice in the form [start:stop].
        # If no slice is present, start and stop are empty strings.
        pattern = r'([A-Za-z0-9_-]+)(?:\[(\d+):(\d+)\])?'
        matches = re.findall(pattern, s)

        if not matches:
            return [s]

        # For each matched segment, build a list of expanded strings.
        # A segment with a slice expands to: ["name.0", "name.1", ..., "name.(stop-1)"]
        # A segment without a slice expands to just: ["name"]
        segments: List[List[str]] = []

        for match in matches:
            name = match[0]
            start = match[1]
            stop = match[2]

            if start and stop:
                # Expand the slice range into individual indexed entries
                expanded = []
                for i in range(int(start), int(stop)):
                    expanded.append(name + "." + str(i))
                segments.append(expanded)
            else:
                # No slice — segment is a single plain name
                segments.append([name])

        # Compute the cartesian product across all segments and join with '.'
        # e.g. ["dgx.0", "dgx.1"] x ["cpu.0", "cpu.1"]
        #   -> ["dgx.0.cpu.0", "dgx.0.cpu.1", "dgx.1.cpu.0", "dgx.1.cpu.1"]
        result: List[str] = []

        for combo in iterproduct(*segments):
            result.append(".".join(combo))

        return result

    def _expand_device_endpoint(
        self,
        device_name: str,
        endpoint: DeviceEndpoint,
    ) -> List[List[str]]:
        """
        Expand a device endpoint into its fully qualified dot-notation representation.

        Args:
            device_name (str): Name of the root device.
            endpoint (DeviceEndpoint): Endpoint expression to expand.

        General Process:
        - Split the endpoint string by "." to obtain individual endpoint elements.
        - Retrieve the corresponding DeviceData object from `device_dict`
        using `device_name`.
        - For each endpoint element:
            - Validate that the component exists in the current DeviceData.
            - Validate index ranges (including single index and slice syntax).
            - Expand the component into dot notation (e.g., "<component>.<index>").
            - Store the expanded results.
            - If the component represents a DEVICE-type component, update
            `device_name` and retrieve the nested DeviceData for the next iteration.
        - Continue iterating until all endpoint elements are processed.
        - Return the fully expanded list of dot-notation endpoint paths.

        Example 1:
            device_name = "server"
            endpoint = "nic[0]"

            - Split into: ["nic[0]"]
            - Validate "nic" against server DeviceData.
            - Expand to: ["nic.0"]
            - Return: ["nic.0"]

        Example 2:
            device_name = "server"
            endpoint = "cx5[0:2].pcie_endpoint[0]"

            - Split into: ["cx5[0:2]", "pcie_endpoint[0]"]
            - Expand "cx5[0:2]" → ["cx5.0", "cx5.1"]
            (component is of type DEVICE, so device_name becomes "cx5")
            - Retrieve DeviceData for "cx5"
            - Expand "pcie_endpoint[0]" → ["pcie_endpoint.0"]
            - Compute cartesian product with previous expansions:
                ["cx5.0.pcie_endpoint.0",
                "cx5.1.pcie_endpoint.0"]

        Returns:
            List[str]: Fully expanded endpoint paths in dot notation.
        """
        endpoints = []
        qualified_endpoints = []
        if isinstance(endpoint, DeviceEndpoint):
            device_endpoint = endpoint.device
            component_endpoint = endpoint.component
        else:
            raise InfrastructureError(f"Endpoint {type(endpoint)} is not valid")
        
        ce = component_endpoint
        if device_endpoint is not None:
            ce = device_endpoint + "." + ce
        for endpoint_element in ce.split("."):
            # if element is component
            component_name = endpoint_element.split("[")[0]
            if component_name in self._device_data[device_name].components:
                component_count = self._device_data[device_name].components[component_name]
                _, c_start, c_stop, c_step = self._split_endpoint(component_count, endpoint_element)
                generated_endpoints = []
                for idx in range(c_start, c_stop, c_step):
                    generated_endpoints.append(f"{component_name}.{idx}")
                
                if len(qualified_endpoints) == 0:
                    qualified_endpoints.extend(generated_endpoints)
                
                else:
                    temp_endpoints = qualified_endpoints.copy()
                    qualified_endpoints = []
                    for parent_endpoint in temp_endpoints:
                        for child_endpoint in generated_endpoints:
                            qualified_endpoints.append(parent_endpoint + "." + child_endpoint)
            device_name = component_name
        endpoints.append(qualified_endpoints)
        return endpoints
    
    def _expand_instance_endpoint(
        self,
        instance: Instance,
        endpoint: InfrastructureEndpoint,
    ) -> List[List[str]]:
        """Return a list for every instance index to a list of fully qualified instance endpoint names"""
        endpoints = []
        qualified_endpoints = []
        if isinstance(endpoint, InfrastructureEndpoint):
            device_endpoint = endpoint.instance
            component_endpoint = endpoint.component
            device_name = instance.device
        else:
            raise InfrastructureError(f"Endpoint {type(endpoint)} is not valid")
        
        # device endpoint here:
        _, d_start, d_stop, d_step = self._split_endpoint(instance.count, device_endpoint)
        
        for endpoint_element in component_endpoint.split("."):
            # if element is component
            component_name = endpoint_element.split("[")[0]
            if component_name in self._device_data[device_name].components:
                component_count = self._device_data[device_name].components[component_name]
                _, c_start, c_stop, c_step = self._split_endpoint(component_count, endpoint_element)
                generated_endpoints = []
                for idx in range(c_start, c_stop, c_step):
                    generated_endpoints.append(f"{component_name}.{idx}")
                if len(qualified_endpoints) == 0:
                    qualified_endpoints.extend(generated_endpoints)
                else:
                    temp_endpoints = qualified_endpoints.copy()
                    qualified_endpoints = []
                    for parent_endpoint in temp_endpoints:
                        for child_endpoint in generated_endpoints:
                            qualified_endpoints.append(parent_endpoint + "." + child_endpoint)
            device_name = component_name
        # before we add we can expand device endpoint here:
        device_endpoints = []
        for device_idx in range(d_start, d_stop, d_step):
            device_endpoints.append(f"{instance.name}.{device_idx}")
        
        temp_endpoints = qualified_endpoints.copy()
        qualified_endpoints = []
        for device_endpoint in device_endpoints:
            for child_endpoint in temp_endpoints:
                qualified_endpoints.append(device_endpoint + "." + child_endpoint)
        # merge them
        endpoints.append(qualified_endpoints)
        return endpoints

    def _parse_device_components(self):
        """
        Parse infrastructure devices and their components, and construct a DeviceData
        object for each device.

        For every parsed device:
        - A DeviceData instance is created.
        - All device components are stored in the `nodes` dictionary of the DeviceData
        object, where:
            - Key: "<component_name>.<index>"
            - Value: Component type (e.g., "switch", "cpu", "xpu", "nic", "custom", etc.)

        Each DeviceData object is then stored in `self._device_data`, where:
        - Key: device.name
        - Value: Corresponding DeviceData instance
        """

        for device in self._infrastructure.devices:
            # iterate the components and generate component-node information
            dd = DeviceData()
            for component in device.components:
                for index in range(component.count):
                    
                    if component.choice == Component.CUSTOM:
                        component_type = component.custom.type
                    else:
                        component_type = component.choice
                    dd.nodes[component.name + "." + str(index)] = component_type
                dd.components[component.name] = component.count
            for link in device.links:
                dd.links[link.name] = link
            self._device_data[device.name] = dd
            
    def _parse_device_edges(self):
        """
        Parse infrastructure devices and their edges.

        For each device:
        - Parse all defined edges between components.
        - Expand each edge into dot notation (e.g., "<component>.<index>").
        - Store the expanded edge information in the corresponding DeviceData object.

        The resulting edges are associated with their respective device’s DeviceData
        instance for further processing.
        """
        for device in self._infrastructure.devices:
            # iterate the devices and generate - expand edges
            # expand edges here:
            dd = self._device_data[device.name]
            for edge in device.edges:
                endpoints1 = self._expand_device_endpoint(device.name, edge.ep1)
                endpoints2 = self._expand_device_endpoint(device.name, edge.ep2)
                for src_eps, dst_eps in [(x, y) for x, y in zip(endpoints1, endpoints2)]:
                    if edge.scheme == DeviceEdge.MANY2MANY:  # cartesion product
                        for src, dst in [(x, y) for x in src_eps for y in dst_eps]:
                            if src == dst:
                                continue
                            dd.add_edge(src, dst, edge.link)
                            
                    elif edge.scheme == DeviceEdge.ONE2ONE:  # meshed product
                        for src, dst in [(x, y) for x, y in zip(src_eps, dst_eps)]:
                            if src == dst:
                                continue
                            dd.add_edge(src, dst, edge.link)
                    else:
                        raise NotImplementedError(f"Edge creation scheme {edge.scheme} is not supported")

    def _parse_edge_instance(self, endpoint: InfrastructureEndpoint) -> Tuple[Instance, Device]:
        """Given an infrastructure endpoint return the Instance and Device"""
        device_instance = endpoint.instance.split(".")[0] 
        instance_name = device_instance.split("[")[0]
        for instance in self._infrastructure.instances:
            if instance.name == instance_name:
                return instance
        raise InfrastructureError(f"Instance '{instance_name}' does not exist in infrastructure instances")

    def _parse_infrastructure_edges(self):
        """
        This parses the global infrastructure edges and expands the instances and endpoints
        """
        infrastructure_links = {link.name: link for link in self._infrastructure.links}
        for edge in self._infrastructure.edges:
            instance1 = self._parse_edge_instance(edge.ep1)
            endpoints1 = self._expand_instance_endpoint(instance1, edge.ep1)
            instance2 = self._parse_edge_instance(edge.ep2)
            endpoints2 = self._expand_instance_endpoint(instance2, edge.ep2)
            edge_attrs = self._link_edge_attrs(edge.link, infrastructure_links.get(edge.link))
            for src_eps, dst_eps in [(x, y) for x, y in zip(endpoints1, endpoints2)]:
                if edge.scheme == InfrastructureEdge.MANY2MANY:  # cartesion product
                    for src, dst in [(x, y) for x in src_eps for y in dst_eps]:
                        if src == dst:
                            continue 
                        self._graph.add_edge(src, dst, **edge_attrs)
                elif edge.scheme == InfrastructureEdge.ONE2ONE:  # meshed product
                    for src, dst in [(x, y) for x, y in zip(src_eps, dst_eps, strict=False)]:
                        if src == dst:
                            continue
                        self._graph.add_edge(src, dst, **edge_attrs)
                else:
                    raise NotImplementedError(f"Edge creation scheme {edge.scheme} is not supported")

    def _link_edge_attrs(self, link_name: str, link_obj) -> Dict[str, Any]:
        """Build the edge attribute dict for a link.

        Always includes the link name. For each physical property that is
        set (bandwidth, latency), the value and its unit are attached as a
        "<value> <unit>" string using the short-form unit, e.g.:
            {"link": "ici", "bandwidth": "1400 Gbps", "latency": "5 ns"}
        """
        attrs: Dict[str, Any] = {"link": link_name}
        if link_obj is not None and link_obj.physical is not None:
            for property_name in ("bandwidth", "latency"):
                physical_property = getattr(link_obj.physical, property_name)
                if physical_property is None or physical_property.choice is None:
                    continue
                value = getattr(physical_property, physical_property.choice)
                if value is None:
                    continue
                unit = self._UNIT_ABBREVIATIONS.get(physical_property.choice, physical_property.choice)
                attrs[property_name] = f"{value} {unit}"
        return attrs

    def _generate_device_data(self):
        """
        Generate device data, including all components and edges defined within a
        device definition.

        This method:
        - Parses and constructs all components belonging to the device.
        - Parses and registers all edges between components.
        - Creates a dict in self: _device_data with key as device name and value as the DeviceData obj
        that holds the nodes and edges present inside a device
        """

        self._parse_device_components()
        self._parse_device_edges()
    
    def _generate_device_nodes(self, instance_name: str, device_name: str):
        """
        Generate NetworkX nodes for a given device instance.

        Args:
            device_name (str): Name of the device definition.
            instance_name (str): Fully qualified instance name used as prefix
                for graph node creation.

        Process:
        - Retrieve the corresponding DeviceData object using `device_name`.
        - Iterate over the `nodes` dictionary of the DeviceData object:
            - Key: "<component_name>.<component_index>"
            - Value: Component type (e.g., DEVICE, CPU, NIC, SWITCH, etc.)

        For each component:
        - If the component type is DEVICE:
            - Perform a recursive call to expand the nested device.
            - The new instance name is constructed as:
                instance_name + "." + component_name
            - The new device name is derived from:
                component_name (without the index)
        - If the component is any non-DEVICE type:
            - Add the node to the NetworkX graph.
            - Prefix the node name with `instance_name` to ensure uniqueness.

        This method recursively expands all nested DEVICE components
        and adds leaf-level components as graph nodes.
        """
        device_data = self._device_data[device_name]
        # get the nodes
        for component_name, component_type in device_data.nodes.items():
            if component_type == Component.DEVICE:
                # recursive call here
                self._generate_device_nodes(instance_name=instance_name + "." + component_name, device_name=component_name.split(".")[0])
            # we add others
            else:
                instance, index = instance_name.rsplit(".", 1)
                self._graph.add_node(
                    instance_name + "." + component_name,
                    type=component_type,
                    instance=instance,
                    instance_idx=int(index),
                    device=device_name,
                    composed_device=instance_name,
                )
    
    def _generate_composed_edges(self, instance_name, device_name):
        """
        Recursively generate composed (nested) device edges using a depth-first strategy.

        Process:
        - Retrieve the corresponding DeviceData object from `_device_data`
        using the provided `device_name`.
        - Iterate over the `nodes` dictionary (components) of the device.
        - For each component:
            - If the component type is DEVICE:
                - Construct the new instance prefix by appending the component
                name to the current `instance_name`.
                - Perform a recursive call using:
                    - The nested device name
                    - The updated instance prefix
                - Continue this process until a component is reached that
                does not contain further DEVICE definitions.

        Traversal Strategy:
        - This method follows a Depth-First Search (DFS) approach.
        - Recursion continues down the hierarchy until leaf components
        (non-DEVICE types) are reached.

        Edge Generation:
        - Once the recursion reaches the deepest level (no further DEVICE
        components), iterate over the `edges` dictionary of that device.
        - Add each edge to the NetworkX graph.
        - During each recursive level, the `instance_name` prefix is extended,
        ensuring that all generated edges are fully qualified
        (e.g., parent.child.subchild.component).

        This guarantees that all nested device edges are expanded and added
        to the graph with correct hierarchical instance naming.
        """
        device_data = self._device_data[device_name]
        for component_name, component_type in device_data.nodes.items():
            if component_type == Component.DEVICE:
                self._generate_composed_edges(instance_name=instance_name + "." + component_name, device_name=component_name.split(".")[0])

            for endpoint_1, endpoint_list in device_data.edges.items():
                for dest_endpoint_tuple in endpoint_list:
                    source = instance_name + "." + endpoint_1
                    destination = instance_name + "." + dest_endpoint_tuple[0]
                    link = dest_endpoint_tuple[1]
                    self._graph.add_edge(source, destination, **self._link_edge_attrs(link, device_data.links.get(link)))

    def _generate_device_edges(self, instance_name: str, device_name: str):
        """
        Generate and add edges to the NetworkX graph for a given device instance.

        Args:
            device_name (str): Name of the device definition.
            instance_name (str): Fully qualified instance name used as prefix
                for graph edge creation.

        Process:
        - Retrieve the corresponding DeviceData object using `device_name`.
        - Iterate over the `edges` dictionary of the DeviceData object:
            - Key: ep1 (e.g., "nic.0")
            - Value: Tuple of (ep2, link_name)
            (e.g., ("cpu.0", "pcie"))

        For each edge:
        - Prefix both endpoints with `instance_name` to construct the fully
        qualified graph edge.
        - Add the edge to the NetworkX graph, preserving the link metadata
        (e.g., link name).

        Composed Devices:
        - If a component is of type DEVICE, recursively call
        `_generate_composed_edges` to:
            - Retrieve the nested device’s DeviceData.
            - Generate and add all internal edges of that composed device.
        - This ensures that both top-level and nested device edges are
        fully expanded into the graph.

        Examples:

        1) Simple Component Edge
        Device: server
        Edge definition:
            nic[0] - cpu[0] (link: pcie)

        Stored in edges dict as (from device - edge expansion):
            "nic.0" -> ("cpu.0", "pcie")

        For instance "server.0", the resulting graph edge:
            "server.0.nic.0" -- "server.0.cpu.0"
            (link="pcie")

        2) Composed Device Edge
        Device: server
        Edge definition:
            cx5[0].pcie_endpoint[0] - pcie_slot[0] (link: pcie)

        Stored in edges dict as (from device - edge expansion):
            "cx5.0.pcie_endpoint.0" -> ("pcie_slot.0", "pcie")

        For instance "server.0", partial expanded edge:
            "server.0.cx5.0.pcie_endpoint.0"
                --
            "server.0.pcie_slot.0"
            (link="pcie")

        A recursive call then retrieves all internal edges of device "cx5"
        and adds them to the graph with the appropriate instance prefix.

        This method ensures that all direct and recursively composed device
        edges are fully represented in the NetworkX graph.
        """
        device_data = self._device_data[device_name]
        for src_endpoint, endpoint_list in device_data.edges.items():
            for dest_endpoint in endpoint_list:
                source = instance_name + "." + src_endpoint
                destination = instance_name + "." + dest_endpoint[0]
                link = dest_endpoint[1]
                self._graph.add_edge(source, destination, **self._link_edge_attrs(link, device_data.links.get(link)))
        self._generate_composed_edges(instance_name, device_name)
         
    def _generate_instance_data(self):
        """
        Iterate over all infrastructure instances and generate their expanded
        topology (nodes and edges).

        This method:
        - Iterates through each infrastructure definition.
        - For each infrastructure item, iterates over the declared instance count.
        - For every instance, recursively generates all nodes and edges of the device.
        - Uses the corresponding DeviceData object from the `_device_data` dictionary
        as the source of component and edge definitions.

        The result is a fully expanded representation of all infrastructure
        instances, including their recursively resolved components and
        interconnections.
        """
        for instance in self._infrastructure.instances:
            # get the device name
            device_name = instance.device
            count = instance.count
            instance_name = instance.name
            for index in range(0, count):
                # call the specific class
                
                instance_name = instance.name + "." + str(index)
                # generate node and edges
                self._generate_device_nodes(instance_name, device_name)
                self._generate_device_edges(instance_name, device_name)
            
    def set_graph(self, payload: Union[str, Infrastructure]) -> None:
        """Generates a networkx graph, validates it and if there are no problems
        returns the networkx graph as a serialized json string.

        - adds component attributes as node attributes
            - for example a component with a name of "a100" and type of "xpu" will be added
            to a fully qualified endpoint node of "dgxa100.0.xpu.0" with attribute "xpu"="a100"
            allowing for a lookup using networkx.get_node_attributes(graph, 'xpu')
        - adds annotations as node attributes if applicable
            - if an annotation has an endpoint, the data is added to the node as attributes
        """
        if isinstance(payload, str):
            self._infrastructure = Infrastructure().deserialize(payload)
        else:
            self._infrastructure = payload
        # Initialize an empty graph, populate it with device and instance nodes, validate the resulting device edges and infrastructure edges, run final graph-wide validation, and then build the prefix and link lookup maps used for fast endpoint resolution.
        self._graph = Graph()
        if self._infrastructure.name:
            self._graph.graph["name"] = self._infrastructure.name
        if self._infrastructure.description:
            self._graph.graph["description"] = self._infrastructure.description
        self._generate_device_data()
        self._generate_instance_data()
        self._validate_device_edges()
        self._parse_infrastructure_edges()
        self._validate_graph()
        self._build_prefix_map()
        self._build_link_map()

    def _validate_device_edges(self):
        """Ensure that there are no edges between device instances
        - TBD: in the case of device within device?"""
        for ep1, ep2 in self._graph.edges():
            if ep1.split(".")[0:2] != ep2.split(".")[0:2]:
                raise InfrastructureError(f"Edge not allowed between endpoint {ep1} and endpoint {ep2}")

    def _validate_graph(self):
        """Validate the network graph

        - the "degree" of a node refers to the number of edges connected to that node
            - the infrastructure requires all component nodes within a device be connected
            - not all devices need to be connected to another device which allows for under utilization to be identified
        """
        networkx.is_connected(self._graph)
        zero_degree_nodes = [n for n, d in self._graph.degree() if d == 0]
        if len(zero_degree_nodes) > 0:
            print(f"Infrastructure has nodes that are not connected: {zero_degree_nodes}")
        self_loops = list(networkx.nodes_with_selfloops(self._graph))
        if len(self_loops) > 0:
            raise GraphError(f"Infrastructure has nodes with self loops: {self_loops}")
        
    def _build_partial_graph(self) -> Graph:
        partial_graph = Graph(**self._graph.graph)
        for node, data in self._graph.nodes(data=True):
            filtered = {k: v for k, v in data.items() if k not in self._IMMUTABLE_ATTRIBUTES}
            partial_graph.add_node(node, **filtered)
        for ep1, ep2, data in self._graph.edges(data=True):
            filtered = {k: v for k, v in data.items() if k not in self._IMMUTABLE_ATTRIBUTES}
            partial_graph.add_edge(ep1, ep2, **filtered)
        return partial_graph

    def get_graph(self, request: GraphRequest) -> str:
        """Returns the current networkx graph as a serialized json string."""
        if self._graph is None:
            raise ValueError("The networkx graph has not been created. Please call set_graph() first.")

        if request.choice == request.INFRAGRAPH:
            return self.populate_infragraph_dict(self._graph, request.infragraph.annotations.choice)

        is_full = request.networkx.annotations.choice == "full"
        graph = self._graph if is_full else self._build_partial_graph()
        return yaml.dump(json_graph.node_link_data(graph, edges="edges"))

    @staticmethod
    def _stringify(v):
        return v if isinstance(v, str) else str(v)

    def populate_infragraph_dict(self, source_graph, attr_type):
        infragraph_dict = {
            "infrastructure": self._infrastructure.serialize('dict'),
            "annotations": {}
        }

        is_full = attr_type == "full"

        def node_attrs_filter(attrs):
            return attrs.items() if is_full else (
                (k, v) for k, v in attrs.items()
                if k not in self._IMMUTABLE_ATTRIBUTES
            )

        def edge_attrs_filter(attrs):
            return attrs.items() if is_full else (
                (k, v) for k, v in attrs.items()
                if k not in self._IMMUTABLE_ATTRIBUTES
            )

        annotation_nodes = [
            {
                "name": node_name,
                "attributes": [
                    {"attribute": k, "value": InfraGraphService._stringify(v)}
                    for k, v in node_attrs_filter(node_attrs)
                ]
            }
            for node_name, node_attrs in source_graph.nodes(data=True)
            if node_attrs
        ]

        annotation_edges = []
        seen_links = {}
        for ep1, ep2, edge_attrs in source_graph.edges(data=True):
            if not edge_attrs:
                continue
            filtered = list(edge_attrs_filter(edge_attrs))
            annotation_edges.append({
                "ep1": ep1,
                "ep2": ep2,
                "attributes": [{"attribute": k, "value": InfraGraphService._stringify(v)} for k, v in filtered]
            })
            link_name = edge_attrs.get("link")
            if link_name and link_name not in seen_links:
                seen_links[link_name] = {
                    "name": link_name,
                    "attributes": [{"attribute": k, "value": InfraGraphService._stringify(v)} for k, v in filtered]
                }

        graph_attrs = source_graph.graph
        annotation_graph = [
            {"attribute": k, "value": InfraGraphService._stringify(v)}
            for k, v in graph_attrs.items()
            if is_full or k not in self._IMMUTABLE_ATTRIBUTES
        ]

        infragraph_dict["annotations"] = {
            "nodes": annotation_nodes,
            "edges": annotation_edges,
            "links": list(seen_links.values()),
            "graph": annotation_graph
        }

        return json.dumps(infragraph_dict, indent=2)

    def _split_endpoint(self, count: int, endpoint: str) -> Tuple[str, int, int, int]:
        """Given an endpoint return a list of endpoint strings.

        Assume that the list of endpoint strings will be all for the count

        - name, must be present
        - start index, 0 if not present
        - stop index, None if not present
        - step index, 1 if not present

        Pieces should be of valid python slice content:
        - e.g., "", ":", "0", "0:", "0:1", ":1"
        """
        endpoint_pieces = re.split(r"[\[\]]", endpoint)
        name = endpoint_pieces[0]
        slice_pieces = [0, count, 1]
        if len(endpoint_pieces) > 1:
            if ":" not in endpoint_pieces[1]:
                slice_pieces[0] = int(endpoint_pieces[1])
                slice_pieces[1] = slice_pieces[0] + 1
            else:
                for idx, slice_piece in enumerate(re.split(r":", endpoint_pieces[1])):
                    if slice_piece != "":
                        slice_pieces[idx] = int(slice_piece)
        return (name, slice_pieces[0], slice_pieces[1], slice_pieces[2])

    @staticmethod
    def get_component(device: Device, type: str) -> Component:
        """Return a component from the device that matches the type

        type: Literal[cpu, xpu, nic, custom, port, device]
        """
        for component in device.components:
            if component.choice == type:
                return component
        raise InfrastructureError(f"Device {device.name} does not have a component of type {type}")

    def get_endpoints(self, name: str, value: Optional[str] = None) -> List[str]:
        """Given an attribute name and value return all node ids that match"""
        endpoints = []
        for node, data in self._graph.nodes(data=name):
            if data is None:
                continue
            elif value is None:
                endpoints.append(node)
            elif data == value:
                endpoints.append(node)
        return endpoints

    def _build_prefix_map(self):
        """Build a prefix-to-nodes lookup map from all nodes in the graph.

        Each graph node is a dot-separated path (e.g. "dgx.0.cpu.1.port.2").
        This method indexes every prefix of that path so that a caller can
        look up all nodes that live under a given prefix without scanning the
        full node list each time.

        Example:
            Node "dgx.0.cpu.1" produces three entries:
                "dgx"         -> [..., "dgx.0.cpu.1"]
                "dgx.0"       -> [..., "dgx.0.cpu.1"]
                "dgx.0.cpu.1" -> [..., "dgx.0.cpu.1"]

        The result is stored in `self._graph_node_prefix_map` as a
        dict[str, List[str]], where each key is a prefix and the value is
        the list of fully qualified node names that share that prefix.

        This map is consumed by lookups that resolve a partial node name
        (e.g. "dgx.0") to all of its descendants in the graph.
        """

        for node in self._graph.nodes:
            parts = node.split(".")
            for i in range(1, len(parts) + 1):
                prefix = ".".join(parts[:i])
                self._graph_node_prefix_map.setdefault(prefix, []).append(node)

    def _build_link_map(self):
        """Build a lookup of link name -> list of (ep1, ep2) edge tuples.

        Lets annotate_graph resolve a link annotation to all edges sharing
        that link name in O(1) instead of scanning every edge. Stays valid
        across annotate_graph calls because annotations never add edges or
        mutate the "link" attribute (it's in _IMMUTABLE_ATTRIBUTES).
        """
        self._link_to_edges_map = {}
        for ep1, ep2, data in self._graph.edges(data=True):
            link_name = data.get("link")
            if link_name is not None:
                self._link_to_edges_map.setdefault(link_name, []).append((ep1, ep2))

    def annotate_graph(self, payload: Union[str, Annotation]):
        """Annotation the graph using the data provided in the payload"""
        if isinstance(payload, str):
            annotate_request = Annotation().deserialize(payload)
        else:
            annotate_request: Annotation = payload
        
        for annotation_node in annotate_request.nodes:
            # expand the nodes
            nodes = self._expand_node_string(annotation_node.name)
            matched = set()
            for node in nodes:
                list_from_prefix_map = self._graph_node_prefix_map.get(node, [])
                if list_from_prefix_map: 
                    matched.update(list_from_prefix_map)
                else:
                    raise ValueError(f"{node} not present in networx graph")
            for attribute_kvp in annotation_node.attributes:
                if attribute_kvp.attribute not in self._IMMUTABLE_ATTRIBUTES:
                    networkx.set_node_attributes(self._graph, {n: {attribute_kvp.attribute: attribute_kvp.value} for n in matched})
                else:
                    warnings.warn(f"Skipping immutable attribute {attribute_kvp.attribute} for {annotation_node.name}")
            
        # edges
        for annotation_edge in annotate_request.edges:
            # expand the nodes
            expanded_source_edges = self._expand_node_string(annotation_edge.ep1)
            expanded_destination_edges = self._expand_node_string(annotation_edge.ep2)
            # expand it further
            # get the expanded source edges
            source_edges= []
            for edge_node in expanded_source_edges:
                list_from_prefix_map = self._graph_node_prefix_map.get(edge_node, [])
                if list_from_prefix_map: 
                    source_edges.extend(list_from_prefix_map)
                else:
                    raise ValueError(f"{node} not present in networx graph") 
            # get the expanded destination edges
            destination_edges = []
            for edge_node in expanded_destination_edges:
                list_from_prefix_map = self._graph_node_prefix_map.get(edge_node, [])
                if list_from_prefix_map: 
                    destination_edges.extend(list_from_prefix_map)
                else:
                    raise ValueError(f"{node} not present in networx graph")    
                        
            matched_edges = [
                edge
                for a, b in iterproduct(source_edges, destination_edges)
                for edge in ((a, b), (b, a))
                if self._graph.has_edge(*edge)
            ]

            for attribute_kvp in annotation_edge.attributes:
                if attribute_kvp.attribute not in self._IMMUTABLE_ATTRIBUTES:
                    networkx.set_edge_attributes(self._graph, {(u, v): {attribute_kvp.attribute: attribute_kvp.value} for u, v in matched_edges})
                else:
                    warnings.warn(f"Skipping immutable attribute {attribute_kvp.attribute} for edge")
        # links
        for annotation_link in annotate_request.links:
            edges_for_link = self._link_to_edges_map.get(annotation_link.name, [])
            for link_annotation in annotation_link.attributes:
                if link_annotation.attribute in self._IMMUTABLE_ATTRIBUTES:
                    warnings.warn(f"Skipping immutable attribute {link_annotation.attribute} for {annotation_link.name}")
                    continue
                for ep1, ep2 in edges_for_link:
                    self._graph[ep1][ep2][link_annotation.attribute] = link_annotation.value

        # graph
        for attribute_kvp in annotate_request.graph:
            if attribute_kvp.attribute in self._IMMUTABLE_ATTRIBUTES:
                warnings.warn(f"Skipping immutable attribute {attribute_kvp.attribute} for graph")
                continue
            self._graph.graph[attribute_kvp.attribute] = attribute_kvp.value
    
    def query_graph(self, payload: Union[str, Query]) -> QueryResponse:
        """Query the graph"""
        if isinstance(payload, str):
            query_request = Query().deserialize(payload)
        else:
            query_request: Query = payload

        query_response = QueryResponse()
        
        if query_request.choice == "shortest_path":
            if query_request.shortest_path.source not in self._graph:
                raise InfrastructureError(f"Queried source node does not exist in graph {query_request.shortest_path.source}")
            if query_request.shortest_path.destination not in self._graph:
                raise InfrastructureError(f"Queried destination node does not exist in graph {query_request.shortest_path.destination}")
            
            path = networkx.shortest_path(self._graph, query_request.shortest_path.source, query_request.shortest_path.destination)
            for p in path:
                # add all the nodes in sequence
                query_response.nodes.add(p)
            return query_response
        
        else:
            # process attributes or create a map?
            matched_nodes = []
            matched_edges = []
            print(query_request.filter.choice)
            logic = query_request.filter.attribute_filter.logic
            attribute_map = {}
            for attribute in query_request.filter.attribute_filter.attributes:
                attribute_map[attribute.attribute] = attribute.value

            # now check for nodes, edges first before we move to generic?
            if query_request.filter.choice == "node_filter":
                # get all the nodes?
                query_nodes = self._expand_node_string(query_request.filter.node_filter)
                
                for node in query_nodes:
                    list_from_prefix_map = self._graph_node_prefix_map.get(node, [])
                    if list_from_prefix_map: 
                        matched_nodes.extend(list_from_prefix_map)
                    else:
                        raise ValueError(f"{node} not present in networx graph")
                # process nodes here
                if len(matched_nodes) == 0:
                    raise InfrastructureError(f"{query_request.filter.node_filter} did not match any of the node in graph")
        
            elif query_request.filter.choice == "edge_filter":
                source_edges = self._expand_node_string(query_request.filter.edge_filter.ep1)
                destination_edges = self._expand_node_string(query_request.filter.edge_filter.ep2)

                adj = {n: set(self._graph.neighbors(n)) for n in self._graph.nodes}
                for s in source_edges:
                    # only check neighbors of s (not all edges)
                    for d in adj[s]:
                        if d in destination_edges:
                            matched_edges.append((s, d))        
                # process nodes here
                if len(matched_edges) == 0:
                    raise InfrastructureError(f"{query_request.filter.edge_filter.ep1} and {query_request.filter.edge_filter.ep2} did not match any of the edges in graph")
                # process here

            else:
                # everything here
                matched_nodes = list(self._graph.nodes)
                matched_edges = list(self._graph.edges)
            
            # process attributes for each of them
            # maybe the list is empty?
            if len(attribute_map) == 0:
                # return the matched nodes and edges
                # should we add attributes?
                for node in matched_nodes:
                    query_response.nodes.add(name=node)
                
                for edge in matched_edges:
                    query_response.edges.add(ep1=edge[0], ep2=edge[1])
            else:
                for node in matched_nodes:
                    # get attrs:
                    attrs = self._get_networkx_node_attrs(node)
                    if InfraGraphService._match_attrs(attrs, attribute_map, logic):
                        query_response_node = query_response.nodes.add(name=node)
                        for k, v in attrs.items():
                            query_response_node.attributes.add(attribute=k, value=str(v))

                for edge in matched_edges:
                    # get attrs:
                    attrs = self._get_networkx_edge_attrs(edge[0], edge[1])
                    if InfraGraphService._match_attrs(attrs, attribute_map, logic):
                        query_response_edge = query_response.edges.add(ep1=edge[0], ep2=edge[1])
                        for k, v in attrs.items():
                            query_response_edge.attributes.add(attribute=k, value=str(v))

                # get graph attributes and match with attrs?
                if InfraGraphService._match_attrs(self._graph.graph, attribute_map, logic):
                    for k, v in self._graph.graph.items():
                        query_response.graph.add(attribute=k, value=str(v))

            return query_response

    def _get_networkx_node_attrs(self, node):
        if node not in self._graph:
            raise ValueError(f"Node '{node}' does not exist.")
        return self._graph.nodes[node] 

    def _get_networkx_edge_attrs(self, ep1, ep2):
        if not self._graph.has_edge(ep1, ep2):
            raise ValueError(f"Edge ({ep1}, {ep2}) does not exist.")
        return self._graph.edges[ep1, ep2]

    @staticmethod
    def _match_attrs(master_dict, query_dict, logic="and", case_sensitive=False):

        def value_matches(master_value, query_value):
            if master_value is None:
                return False
            master = str(master_value)
            query = str(query_value)
            master = master.lower()
            query = query.lower()
            return query in master
        
        matches = []

        for key, query_value in query_dict.items():
            if key not in master_dict:
                matches.append(False)
                continue

            matches.append(value_matches(master_dict[key], query_value))
        return all(matches) if logic == "and" else any(matches)