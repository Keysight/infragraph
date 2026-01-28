"""

Python slice notation is a concise and powerful syntax for extracting a subset of elements from a sequence such as a list, tuple, or string. It uses square brackets with up to three optional parameters separated by colons inside: start:stop:step.
- start is the index where the slice begins (inclusive). Defaults to 0 if omitted.
- stop is the index where the slice ends (exclusive). Defaults to the length of the sequence if omitted.
- step is the interval between elements in the slice. Defaults to 1 and can be negative for reversing the sequence.

"""

from typing import Any, Dict, Iterator, List, Optional, Tuple, Union
import networkx
from networkx import Graph
from networkx.readwrite import json_graph
import re
import yaml
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
    
    def add_edge(self, ep1, ep2, link):
        if ep1 in self.edges:
            self.edges[ep1].append((ep2, link))
        else:
            self.edges[ep1] = [(ep2, link)]

class InfraGraphService(Api):
    """InfraGraph Services"""

    def __init__(self):
        super().__init__()
        self._graph: Graph = Graph()
        self._device_data = {}
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

    def _expand_device_endpoint(
        self,
        device_name: str,
        endpoint: DeviceEndpoint,
    ) -> List[List[str]]:
        """Return a list for every instance index to a list of fully qualified instance endpoint names"""
        endpoints = []
        qualified_endpoints = []
        if isinstance(endpoint, DeviceEndpoint):
            component_endpoint = endpoint.component
        else:
            raise InfrastructureError(f"Endpoint {type(endpoint)} is not valid")
        
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
            self._device_data[device.name] = dd
            
    def _parse_device_edges(self):
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
        for edge in self._infrastructure.edges:
            instance1 = self._parse_edge_instance(edge.ep1)
            endpoints1 = self._expand_instance_endpoint(instance1, edge.ep1)
            instance2 = self._parse_edge_instance(edge.ep2)
            endpoints2 = self._expand_instance_endpoint(instance2, edge.ep2)
            for src_eps, dst_eps in [(x, y) for x, y in zip(endpoints1, endpoints2)]:
                if edge.scheme == InfrastructureEdge.MANY2MANY:  # cartesion product
                    for src, dst in [(x, y) for x in src_eps for y in dst_eps]:
                        if src == dst:
                            continue
                        self._graph.add_edge(src, dst, link=edge.link)
                elif edge.scheme == InfrastructureEdge.ONE2ONE:  # meshed product
                    for src, dst in [(x, y) for x, y in zip(src_eps, dst_eps, strict=False)]:
                        if src == dst:
                            continue
                        self._graph.add_edge(src, dst, link=edge.link)
                else:
                    raise NotImplementedError(f"Edge creation scheme {edge.scheme} is not supported")

    def _generate_device_data(self):
        # get all the devices
        self._parse_device_components()
        self._parse_device_edges()    
    
    def _generate_device_nodes(self, instance_name, device_name):
        device_data = self._device_data[device_name]
        # get the nodes
        for component_name, component_type in device_data.nodes.items():
            if component_type == Component.DEVICE:
                # recursive call here
                self._generate_device_nodes(instance_name=instance_name + "." + component_name, device_name=component_name.split(".")[0])
            # we add others
            else:
                self._graph.add_node(
                    instance_name + "." + component_name,
                    type=component_type,
                    instance=instance_name.split(".")[0],
                    instance_idx=int(instance_name.split(".")[1]),
                    device=device_name,
                )
    
    def _generate_composed_edges(self, instance_name, device_name):
        device_data = self._device_data[device_name]
        for component_name, component_type in device_data.nodes.items():
            if component_type == Component.DEVICE:
                self._generate_composed_edges(instance_name=instance_name + "." + component_name, device_name=component_name.split(".")[0])

                for endpoint_1, endpoint_list in device_data.edges.items():
                    for dest_endpoint_tuple in endpoint_list:
                        source = instance_name + "." + endpoint_1
                        destination = instance_name + "." + dest_endpoint_tuple[0]
                        link = dest_endpoint_tuple[1]
                        self._graph.add_edge(source, destination, link=link)

    def _generate_device_edges(self, instance_name, device_name):
        device_data = self._device_data[device_name]
        for src_endpoint, endpoint_list in device_data.edges.items():
            for dest_endpoint in endpoint_list:
                source = instance_name + "." + src_endpoint
                destination = instance_name + "." + dest_endpoint[0]
                link = dest_endpoint[1]
                self._graph.add_edge(source, destination, link=link)
        self._generate_composed_edges(instance_name, device_name)

    def print_graph(self):
        with open("graph_dump.txt", "w", encoding="utf-8") as f:
            for node, attrs in self._graph.nodes(data=True):
                f.write(f"Node: {node}, Attributes: {attrs}\n")
                print(f"Node: {node}, Attributes: {attrs}")

            f.write("\n")  # blank line between nodes and edges

            for u, v, attrs in self._graph.edges(data=True):
                f.write(f"Edge: ({u}, {v}), Attributes: {attrs}\n")
                print(f"Edge: ({u}, {v}), Attributes: {attrs}")

            
    def _generate_instance_data(self):
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
            
        self.print_graph()   
        pass


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
        self._graph = Graph()
        self._generate_device_data()
        self._generate_instance_data()
        # self._add_nodes()
        # self._add_device_edges()
        self._validate_device_edges()
        self._parse_infrastructure_edges()
        self._validate_graph()

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

    def get_graph(self) -> str:
        """Returns the current networkx graph as a serialized json string."""
        if self._graph is None:
            raise ValueError("Graph is not set. Please call set_graph() first.")
        return yaml.dump(json_graph.node_link_data(self._graph, edges="edges"))

    def _isa_component(self, device_name: str):
        """Return whether or not the device is a component of another device"""
        for device in self._infrastructure.devices:
            for component in device.components:
                if component.name == device_name and component.choice == Component.DEVICE:
                    return True
        return False

    def get_shortest_path(self, endpoint1: str, endpoint2: str) -> list[str]:
        """Returns the shortest path between two endpoints in the graph."""
        return networkx.shortest_path(self._graph, endpoint1, endpoint2)

    def _get_device(self, device_name: str) -> Device:
        """Given a device name return the device object"""
        for device in self._infrastructure.devices:
            if device.name == device_name:
                return device
        raise InfrastructureError(f"Device {device_name} does not exist in Infrastructure.devices")

    def _add_nodes(self):
        """Add all device instances as nodes to the graph
        - add component type, instance name, instance index, device name as attributes
        """
        for instance in self._infrastructure.instances:
            if self._isa_component(instance.device):
                continue
            device = self._get_device(instance.device)
            for device_idx in range(instance.count):
                for component in device.components:
                    for component_idx in range(component.count):
                        name = f"{instance.name}.{device_idx}.{component.name}.{component_idx}"
                        type = (
                            component.custom.type
                            if component.choice == Component.CUSTOM
                            else component.choice
                        )
                        self._graph.add_node(
                            name,
                            type=type,
                            instance=instance.name,
                            instance_idx=device_idx,
                            device=instance.device,
                        )

    def _resolve_instance(self, endpoint: InfrastructureEndpoint) -> Tuple[Instance, Device]:
        """Given an infrastructure endpoint return the Instance and Device"""
        instance_name = endpoint.instance.split("[")[0]
        for instance in self._infrastructure.instances:
            if instance.name == instance_name:
                device = self._get_device(instance.device)
                return (instance, device)
        raise InfrastructureError(f"Instance '{instance_name}' does not exist in infrastructure instances")

    def _add_infrastructure_edges(self):
        """Generate infrastructure edges and add them to the graph"""
        for edge in self._infrastructure.edges:
            instance1, device1 = self._resolve_instance(edge.ep1)
            endpoints1 = self._expand_endpoint(instance1, device1, edge.ep1)
            instance2, device2 = self._resolve_instance(edge.ep2)
            endpoints2 = self._expand_endpoint(instance2, device2, edge.ep2)
            for src_eps, dst_eps in [(x, y) for x, y in zip(endpoints1, endpoints2)]:
                if edge.scheme == InfrastructureEdge.MANY2MANY:  # cartesion product
                    for src, dst in [(x, y) for x in src_eps for y in dst_eps]:
                        if src == dst:
                            continue
                        self._graph.add_edge(src, dst, link=edge.link)
                elif edge.scheme == InfrastructureEdge.ONE2ONE:  # meshed product
                    for src, dst in [(x, y) for x, y in zip(src_eps, dst_eps, strict=False)]:
                        if src == dst:
                            continue
                        self._graph.add_edge(src, dst, link=edge.link)
                else:
                    raise NotImplementedError(f"Edge creation scheme {edge.scheme} is not supported")

    def _add_device_edges(self):
        """Add all device edges to the graph.

        - Do not add edges when the device is referenced as a component in another device.
        """
        for instance in self._infrastructure.instances:
            if self._isa_component(instance.device):
                continue
            device = self._get_device(instance.device)
            for edge in device.edges:
                self._add_device_edge(instance, device, edge)

    def _add_device_edge(self, instance: Instance, device: Device, edge: DeviceEdge) -> None:
        """Validate edges and add them to the graph

        Substitute the instance name for the device name.

        instance.name = "test"
        instance.device = "dgx"
        edge.ep1.device = "dgx[0:8]" -> test.0 -> test.7
        edge.ep1.component = "a100[0:8]" -> a100.0 -> a100.7

        edge.ep1.device = "dgx[0:8]" -> dgx.0 -> dgx.7
        edge.ep1.component = "pciesw[0]" -> pciesw.0
        """
        for edge in device.edges:
            endpoints1 = self._expand_endpoint(instance, device, edge.ep1)
            endpoints2 = self._expand_endpoint(instance, device, edge.ep2)
            for src_eps, dst_eps in [(x, y) for x, y in zip(endpoints1, endpoints2)]:
                if edge.scheme == DeviceEdge.MANY2MANY:  # cartesion product
                    for src, dst in [(x, y) for x in src_eps for y in dst_eps]:
                        if src == dst:
                            continue
                        self._graph.add_edge(src, dst, link=edge.link)
                elif edge.scheme == DeviceEdge.ONE2ONE:  # meshed product
                    for src, dst in [(x, y) for x, y in zip(src_eps, dst_eps)]:
                        if src == dst:
                            continue
                        self._graph.add_edge(src, dst, link=edge.link)
                else:
                    raise NotImplementedError(f"Edge creation scheme {edge.scheme} is not supported")

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

    def _expand_endpoint(
        self,
        instance: Instance,
        device: Device,
        endpoint: Union[InfrastructureEndpoint, DeviceEndpoint],
    ) -> List[List[str]]:
        """Return a list for every instance index to a list of fully qualified instance endpoint names"""
        endpoints = []
        if isinstance(endpoint, InfrastructureEndpoint):
            device_endpoint = endpoint.instance
            component_endpoint = endpoint.component
        elif isinstance(endpoint, DeviceEndpoint):
            device_endpoint = device.name if endpoint.device is None else endpoint.device
            component_endpoint = endpoint.component
        else:
            raise InfrastructureError(f"Endpoint {type(endpoint)} is not valid")
        
        # expansion of device
        d_start, d_stop, d_step = 0, 1, 1
        if instance is not None:
            _, d_start, d_stop, d_step = self._split_endpoint(instance.count, device_endpoint)
        
        # expansion of component
        component = self._get_component(device, component_endpoint.split("[")[0])
        _, c_start, c_stop, c_step = self._split_endpoint(component.count, endpoint.component)
        
        # add device and component together here
        for device_idx in range(d_start, d_stop, d_step):
            qualified_endpoints = []
            for idx in range(c_start, c_stop, c_step):
                if instance is not None:
                    qualified_endpoints.append(f"{instance.name}.{device_idx}.{component.name}.{idx}")
                else:
                    qualified_endpoints.append(f"{component.name}.{idx}")
            endpoints.append(qualified_endpoints)
        return endpoints

    def _get_component(self, device: Device, name: str) -> Component:
        """Return a component given a name"""
        for component in device.components:
            if component.name == name:
                return component
        raise ValueError(f"Component {name} does not exist in Device {device.name}")

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

    def annotate_graph(self, payload: Union[str, AnnotateRequest]):
        """Annotation the graph using the data provided in the payload"""
        if isinstance(payload, str):
            annotate_request = AnnotateRequest().deserialize(payload)
        else:
            annotate_request: AnnotateRequest = payload
        for annotation_node in annotate_request.nodes:
            endpoint = self._graph.nodes[annotation_node.name]
            endpoint[annotation_node.attribute] = annotation_node.value

    def query_graph(self, payload: Union[str, QueryRequest]) -> QueryResponseContent:
        """Query the graph"""
        if isinstance(payload, str):
            query_request = QueryRequest().deserialize(payload)
        else:
            query_request: QueryRequest = payload
        query_response_content = QueryResponseContent()
        if query_request.choice == QueryRequest.NODE_FILTERS:
            node_matches = self._graph.nodes(data=True)
            for node_filter in query_request.node_filters:
                if node_filter.choice == QueryNodeFilter.ID_FILTER:
                    node_matches = self._node_id_filter(node_matches, node_filter.id_filter)  # type: ignore
                elif node_filter.choice == QueryNodeFilter.ATTRIBUTE_FILTER:
                    node_matches = self._attribute_filter(node_matches, node_filter.attribute_filter)  # type: ignore
                else:
                    raise InfrastructureError(f"Invalid node query filter {node_filter.choice}")
            for node in node_matches:
                match = query_response_content.node_matches.add()
                match.id = node[0]
                for k, v in node[1].items():
                    match.attributes.add(name=k, value=v if isinstance(v, str) else str(v))
            return query_response_content
        else:
            raise NotImplementedError("Query edges not implemented")

    def _node_id_filter(self, nodes: List[Any], query: QueryNodeId) -> List[Any]:
        results = []
        for node in nodes:
            id = node[0]
            if query.operator == QueryNodeId.EQ and query.value == id:
                results.append(node)
            elif query.operator == QueryNodeId.CONTAINS and query.value in id:
                results.append(node)
            elif query.operator == QueryNodeId.REGEX and re.match(query.value, id) is not None:
                results.append(node)
        return results

    def _attribute_filter(self, nodes: List[Any], query: QueryAttribute) -> List[Any]:
        results = []
        for node in nodes:
            for k, v in node[1].items():
                if k != query.name:
                    continue
                if query.operator == QueryNodeId.EQ and query.value == v:
                    results.append(node)
                elif query.operator == QueryNodeId.CONTAINS and query.value in v:
                    results.append(node)
                elif query.operator == QueryNodeId.REGEX and re.match(query.value, v) is not None:
                    results.append(node)
        return results
