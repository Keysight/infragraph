"""

Python slice notation is a concise and powerful syntax for extracting a subset of elements from a sequence such as a list, tuple, or string. It uses square brackets with up to three optional parameters separated by colons inside: start:stop:step.
- start is the index where the slice begins (inclusive). Defaults to 0 if omitted.
- stop is the index where the slice ends (exclusive). Defaults to the length of the sequence if omitted.
- step is the interval between elements in the slice. Defaults to 1 and can be negative for reversing the sequence.

"""

import json
from typing import List, Optional, Tuple, Union
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

    def set_graph(self, payload: str) -> None:
        """Generates a networkx graph, validates it and if there are no problems
        returns the networkx graph as a serialized json string.

        - adds component attributes as node attributes
            - for example a component with a name of "a100" and type of "npu" will be added
            to a fully qualified endpoint node of "dgxa100.0.npu.0" with attribute "npu"="a100"
            allowing for a lookup using networkx.get_node_attributes(graph, 'npu')
        - adds annotations as node attributes if applicable
            - if an annotation has an endpoint, the data is added to the node as attributes
        """
        self._infrastructure = Infrastructure()
        self._infrastructure.deserialize(serialized_object=payload)
        self._graph = Graph()
        self._add_nodes()
        self._add_device_edges()
        self._validate_graph()

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
        for device in self._infrastructure.devices:
            if device.name == device_name:
                return device
        raise InfrastructureError(f"Device {device_name} does not exist in Infrastructure.devices")

    def _add_nodes(self):
        """Add all device instances to the graph"""
        for instance in self._infrastructure.instances:
            if self._isa_component(instance.device):
                continue
            device = self._get_device(instance.device)
            for device_idx in range(instance.count):
                for component in device.components:
                    for component_idx in range(component.count):
                        name = f"{instance.name}.{device_idx}.{component.name}.{component_idx}"
                        self._graph.add_node(name, type=component.choice)

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
            if edge.many2many is True:  # cartesion product
                for src, dst in [(x, y) for x in endpoints1 for y in endpoints2]:
                    if src == dst:
                        continue
                    self._graph.add_edge(src, dst, link=edge.link)
            else:  # meshed product
                for src, dst in [(x, y) for x, y in zip(endpoints1, endpoints2)]:
                    if src == dst:
                        continue
                    self._graph.add_edge(src, dst, link=edge.link)

    def _split_endpoint(self, device: Device, endpoint: str) -> Tuple[str, int, int, int]:
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
        component = self._get_component(device, name)
        slice_pieces = [0, component.count, 1]
        if len(endpoint_pieces) > 1:
            for idx, slice_piece in enumerate(re.split(r":", endpoint_pieces[1])):
                if slice_piece != "":
                    slice_pieces[idx] = int(slice_piece)
        return (name, slice_pieces[0], slice_pieces[1], slice_pieces[2])

    def _expand_endpoint(self, instance: Instance, device: Device, endpoint: DeviceEndpoint) -> List[str]:
        """Return a list of fully qualified endpoint names"""
        endpoints = []
        name, start, stop, step = self._split_endpoint(device, endpoint.component)
        for device_idx in range(instance.count):
            for idx in range(start, stop, step):
                endpoints.append(f"{instance.name}.{device_idx}.{name}.{idx}")
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

        type: Literal[cpu, npu, nic, custom, port, device]
        """
        for component in device.components:
            if component.choice == type:
                return component
        raise InfrastructureError(f"Device {device.name} does not have a component of type {type}")

    def get_endpoints(self, name: str, value: str) -> List[str]:
        """Given an attribute name and value return all endpoint names that match"""
        endpoints = []
        for name, data in self._graph.nodes(data=True):
            if data.get(name) == value:
                endpoints.append(name)
        return endpoints
