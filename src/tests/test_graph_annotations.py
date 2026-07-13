import json
import pytest
import yaml
from infragraph import *
from infragraph.blueprints.fabrics.closfabric import ClosFabric
from infragraph.infragraph_service import InfraGraphService


def _make_service():
    service = InfraGraphService()
    service.set_graph(ClosFabric())
    return service


def _annotate_graph(service, **kwargs):
    annotation = Annotation()
    for attr, value in kwargs.items():
        annotation.graph.add(attribute=attr, value=str(value))
    service.annotate_graph(annotation)
    return annotation


@pytest.mark.asyncio
async def test_graph_annotation_stored():
    """Graph-level attributes are written into networkx graph.graph dict."""
    service = _make_service()
    _annotate_graph(service, cluster="rack-a", region="us-east")

    assert service._graph.graph["cluster"] == "rack-a"
    assert service._graph.graph["region"] == "us-east"


@pytest.mark.asyncio
async def test_graph_annotation_infragraph_output():
    """Graph-level attributes appear in infragraph get_graph response."""
    service = _make_service()
    _annotate_graph(service, experiment="run-42")

    request = GraphRequest()
    request.choice = GraphRequest.INFRAGRAPH
    request.infragraph.annotations.choice = AnnotationType.FULL
    result = json.loads(service.get_graph(request))

    graph_attrs = {a["attribute"]: a["value"] for a in result["annotations"]["graph"]}
    assert graph_attrs["experiment"] == "run-42"


@pytest.mark.asyncio
async def test_graph_annotation_networkx_output():
    """Graph-level attributes appear in networkx get_graph response."""
    service = _make_service()
    _annotate_graph(service, topology="fat-tree")

    request = GraphRequest()
    request.choice = GraphRequest.NETWORKX
    request.networkx.annotations.choice = AnnotationType.FULL
    result = yaml.safe_load(service.get_graph(request))

    assert result["graph"]["topology"] == "fat-tree"


@pytest.mark.asyncio
async def test_graph_annotation_multiple_attributes():
    """Multiple graph-level attributes are all stored and returned."""
    service = _make_service()
    attrs = {"owner": "team-infra", "version": "2", "env": "staging"}
    _annotate_graph(service, **attrs)

    request = GraphRequest()
    request.choice = GraphRequest.INFRAGRAPH
    request.infragraph.annotations.choice = AnnotationType.FULL
    result = json.loads(service.get_graph(request))

    graph_attrs = {a["attribute"]: a["value"] for a in result["annotations"]["graph"]}
    for k, v in attrs.items():
        assert graph_attrs[k] == v


@pytest.mark.asyncio
async def test_graph_annotation_overwrite():
    """Annotating the same attribute twice overwrites the previous value."""
    service = _make_service()
    _annotate_graph(service, status="init")
    _annotate_graph(service, status="ready")

    assert service._graph.graph["status"] == "ready"


@pytest.mark.asyncio
async def test_graph_annotation_immutable_rejected():
    """Annotating an immutable attribute warns and is skipped, not raised."""
    service = _make_service()
    annotation = Annotation()
    annotation.graph.add(attribute="type", value="custom")
    with pytest.warns(UserWarning):
        service.annotate_graph(annotation)
    assert service._graph.graph.get("type") != "custom"


@pytest.mark.asyncio
async def test_graph_annotation_partial_excludes_immutable():
    """Partial infragraph output excludes immutable attributes from graph annotations."""
    service = _make_service()
    _annotate_graph(service, label="visible")
    # manually inject an immutable key to simulate immutable state
    service._graph.graph["type"] = "should-be-hidden"

    request = GraphRequest()
    request.choice = GraphRequest.INFRAGRAPH
    request.infragraph.annotations.choice = AnnotationType.PARTIAL
    result = json.loads(service.get_graph(request))

    graph_attrs = {a["attribute"]: a["value"] for a in result["annotations"]["graph"]}
    assert "label" in graph_attrs
    assert "type" not in graph_attrs


if __name__ == "__main__":
    pytest.main(["-s", __file__])
