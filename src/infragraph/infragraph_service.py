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


class InfraGraphService(Api):
    """InfraGraph Services"""

    def __init__(self):
        super().__init__()
        self._graph: Graph = Graph()
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
        self._add_nodes()
        self._add_device_edges()
        self._validate_device_edges()
        self._add_infrastructure_edges()
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
            raise GraphError(f"Infrastructure has nodes that are not connected: {zero_degree_nodes}")
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
        _, d_start, d_stop, d_step = self._split_endpoint(instance.count, device_endpoint)
        component = self._get_component(device, component_endpoint.split("[")[0])
        _, c_start, c_stop, c_step = self._split_endpoint(component.count, endpoint.component)
        for device_idx in range(d_start, d_stop, d_step):
            qualified_endpoints = []
            for idx in range(c_start, c_stop, c_step):
                qualified_endpoints.append(f"{instance.name}.{device_idx}.{component.name}.{idx}")
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
