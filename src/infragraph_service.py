"""

Python slice notation is a concise and powerful syntax for extracting a subset of elements from a sequence such as a list, tuple, or string. It uses square brackets with up to three optional parameters separated by colons inside: start:stop:step.
- start is the index where the slice begins (inclusive). Defaults to 0 if omitted.
- stop is the index where the slice ends (exclusive). Defaults to the length of the sequence if omitted.
- step is the interval between elements in the slice. Defaults to 1 and can be negative for reversing the sequence.

"""

import json
from typing import List, Tuple, Union
import networkx
from networkx import Graph
from networkx.readwrite import json_graph
import re
from infragraph import *
import pytest


class InfraGraphService(Api):
    """InfraGraph Services"""

    def __init__(self):
        super().__init__()
        self._graph = None
        self._infrastructure = None

    @property
    def graph(self) -> Graph:
        """Returns the current networkx graph."""
        if self._graph is None:
            raise ValueError("Graph is not set. Please call set_graph() first.")
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
        self._infrastructure = Infrastructure.deserialize(payload)
        self._graph = Graph()

        # add all device edges to the graph
        # for device in self._infrastructure.devices:
        #     for edge in device.edges:
        #         self._add_device_edge(device, edge)
        # for edge in device.edges:
        #     ep1, ep2 = self._validate_edge(edge)
        #     for device_idx in range(device.count):
        #         endpoint2 = endpoint1 = f"{device.name}.{device_idx}"
        #         for piece in edge.ep1:
        #             endpoint1 += f".{piece}"
        #         for piece in edge.ep2:
        #             endpoint2 += f".{piece}"
        #     self._graph.add_edge(endpoint1, endpoint2, link=edge.link)

        # add all infrastructure edges to the graph
        # for edge in self._infrastructure.edges:
        #     self._add_edge(self._infrastructure, edge)

        # validate the graph
        networkx.is_connected(self._graph)

    def get_graph(self) -> str:
        """Returns the current networkx graph as a serialized json string."""
        if self._graph is None:
            raise ValueError("Graph is not set. Please call set_graph() first.")
        return json.dumps(json_graph.node_link_data(self._graph))

    def get_shortest_path(self, endpoint1: str, endpoint2: str) -> list[str]:
        """Returns the shortest path between two endpoints in the graph."""
        return []

    def _add_device_edge(
        self,
        device: Device,
        edge: DeviceEdge,
    ) -> None:
        """Validate edges and add them to the graph
        edge.ep1.device = "dgx[0:8]" -> dgx.0 -> dgx.7
        edge.ep1.component = "a100[0:8]" -> a100.0 -> a100.7

        edge.ep1.device = "dgx[0:8]" -> dgx.0 -> dgx.7
        edge.ep1.component = "pciesw[0]" -> pciesw.0



        dgx.0.a100.0 -> dgx.0.pciesw.0
        dgx.0.a100.1 -> dgx.0.pciesw.0
        ...
        dgx.0.a100.7 -> dgx.0.pciesw.0

        """
        name, start, stop, step = self._split_endpoint(edge.ep1.device)
        if name != device.name and stop is None:
            stop = device.count
        for idx in range(start, stop, slice_pieces[2]):
            endpoints.append(f"{name}.{idx}")
        return endpoints

        #     if stop is None:
        #         container.devices
        #     component_ep_split = self._expand_endpoint(edge.ep1.component)
        # elif isinstance(container, Device):
        #     pass
        # else:
        #     raise ValueError(f"Cannot validate an endpoint against an object of type {type(source)}")
        # endpoints1 = self._expand_endpoint(container, edge.ep1)
        # endpoints2 = self._expand_endpoint(container, edge.ep2)
        # for endpoint1, endpoint2 in zip(endpoint1, endpoints2):
        #     self._graph.add_edge(endpoint1, endpoint2, link=edge.link)

    def _split_endpoint(self, endpoint: str) -> List[str]:
        """Given an endpoint return a list of endpoint strings.

        Assume that the list of endpoint strings will be all for the count

        - name
        - start index, None if not present
        - stop index, None if not present
        - step index, None if not present

        Pieces should be of valid python slice content:
        - e.g., "", ":", "0", "0:", "0:1", ":1"
        """
        name, slice, _ = re.split(r"[\[\]]", endpoint)
        slice_pieces = [0, None, 1]
        for idx, slice_piece in enumerate(re.split(r":", slice)):
            if slice_piece != "":
                slice_pieces[idx] = int(slice_piece)
        return (name, slice_pieces[0], slice_pieces[1], slice_pieces[2])

    def _expand_endpoint(self, name, start, stop, step):
        endpoints = []
        for idx in range(start, stop, step):
            endpoints.append(f"{name}.{idx}")
        return endpoints
