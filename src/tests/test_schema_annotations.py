import json
import pytest
import yaml
from infragraph import *
from infragraph.blueprints.devices.generic.generic_switch import Switch
from infragraph.infragraph_service import InfraGraphService, InfrastructureError

ERRORS = (ValueError, InfrastructureError)
SWITCH_NS = "fabricgym.switch.v1"
SWITCH_SCHEMA = """\
type: object
required: [role]
properties:
  role: { enum: [leaf, spine] }
  nos:  { type: string }
  mtu:  { type: integer, minimum: 1280 }
  interfaces:
    type: object
    additionalProperties:
      type: object
      properties:
        speed: { type: string }
        vlan:  { type: integer }
"""
LEAF0 = "role: leaf\nnos: sonic\nmtu: 9100\ninterfaces:\n  eth0: { speed: 100G, vlan: 10 }\n  eth1: { speed: 100G, vlan: 20 }\n"
LEAF1 = "role: leaf\nnos: sonic\nmtu: 1500\ninterfaces:\n  eth0: { speed: 25G, vlan: 10 }\n"
SPINE0 = "role: spine\nmtu: 9100\n"

OTG_OPENAPI = """\
openapi: 3.0.3
info: { title: otg, version: 1.0.0 }
paths: {}
components:
  schemas:
    Config:
      type: object
      properties:
        ports:
          type: array
          items: { $ref: '#/components/schemas/Port' }
    Port:
      type: object
      required: [name]
      properties:
        location: { type: string }
        name: { type: string }
"""


def _infrastructure(with_schema: bool = True) -> Infrastructure:
    infra = Infrastructure(name="dc-lab")
    switch = Switch(port_count=1)
    infra.devices.append(switch)
    for name, count in (("leafsw", 4), ("spine", 1), ("tgen", 2), ("controller", 1)):
        infra.instances.add(name=name, device=switch.name, count=count)
    if with_schema:
        schema = infra.schemas.add(namespace=SWITCH_NS)
        schema.jsonschema.definition = SWITCH_SCHEMA
    return infra


def _service() -> InfraGraphService:
    service = InfraGraphService()
    service.set_graph(_infrastructure())
    return service


def _annotate(service, documents=None, references=None, namespace=SWITCH_NS):
    """documents: {name: text}, references: [(node, document, pointer)]."""
    annotation = Annotation()
    if documents:
        schema = annotation.schemas.add(namespace=namespace)
        for name, value in documents.items():
            schema.documents.add(name=name, value=value)
    for node, document, pointer in references or []:
        reference = annotation.nodes.add(name=node).references.add(document=document)
        if pointer:
            reference.pointer = pointer
    service.annotate_graph(annotation)


def _lab(service):
    _annotate(
        service,
        {"leafsw0-config": LEAF0, "leafsw1-config": LEAF1, "spine0-config": SPINE0},
        [
            ("leafsw[0]", "leafsw0-config", None),
            ("leafsw[1]", "leafsw1-config", None),
            ("spine[0]", "spine0-config", None),
        ],
    )


def _query(service, path, schema=SWITCH_NS, node_identifiers=None):
    request = QueryRequest()
    request.choice = QueryRequest.ATTRIBUTE_QUERY
    node_filter = request.attribute_query.node_filters.add(name="f")
    node_filter.schema_filters.add(schema=schema, path=path)
    if node_identifiers:
        node_filter.node_identifiers = node_identifiers
    response = service.query_graph(request)
    return list(response.attribute_query.nodes[0].nodes) if len(response.attribute_query.nodes) else []


def _instances(nodes):
    return sorted({n.name.split(".")[0] + "." + n.name.split(".")[1] for n in nodes})


def test_documents_stored_as_canonical_json():
    service = _service()
    _lab(service)

    assert service._documents["spine0-config"][2] == '{"mtu":9100,"role":"spine"}'


def test_invalid_document_is_rejected_and_nothing_applied():
    service = _service()

    with pytest.raises(ERRORS):
        _annotate(service, {"good": SPINE0, "bad": "role: router\n"})

    assert service._documents == {}


@pytest.mark.parametrize("text", ["role: [", "role: leaf\nwhen: 2024-01-01\n"])
def test_document_that_is_not_json_data_is_rejected(text):
    service = _service()

    with pytest.raises(ERRORS):
        _annotate(service, {"bad": text})


def test_duplicate_document_name_is_rejected():
    service = _service()
    _annotate(service, {"a": SPINE0})

    with pytest.raises(InfrastructureError, match="Duplicate document"):
        _annotate(service, {"a": SPINE0})
    with pytest.raises(InfrastructureError, match="Duplicate document"):
        annotation = Annotation()
        schema = annotation.schemas.add(namespace=SWITCH_NS)
        schema.documents.add(name="b", value=SPINE0)
        schema.documents.add(name="b", value=SPINE0)
        service.annotate_graph(annotation)


def test_unknown_schema_is_rejected():
    service = _service()

    with pytest.raises(InfrastructureError, match="Unknown schema"):
        _annotate(service, {"a": SPINE0}, namespace="nope.v1")


def test_reference_errors_apply_nothing():
    service = _service()
    _annotate(service, {"a": LEAF0})

    for document, pointer in (("a", "/interfaces/eth9"), ("typo", None), ("a", "interfaces")):
        with pytest.raises(ERRORS):
            _annotate(
                service,
                {"fresh": SPINE0},
                [("leafsw[0]", "a", None), ("leafsw[1]", document, pointer)],
            )
        assert "fresh" not in service._documents
        assert service._node_references == {}


def test_document_and_reference_in_one_request_and_duplicate_reference():
    service = _service()
    _annotate(service, {"a": LEAF0}, [("leafsw[2:4]", "a", None)])
    _annotate(service, None, [("leafsw[2]", "a", None)])

    assert service._node_references["leafsw.2.asic.0"] == [("a", "")]
    assert "leafsw.3.asic.0" in service._node_references
    assert "leafsw.1.asic.0" not in service._node_references


def test_set_graph_discards_documents_and_references():
    service = _service()
    _lab(service)

    service.set_graph(_infrastructure())

    assert service._documents == {} and service._node_references == {}


def test_duplicate_schema_namespace_is_rejected():
    infra = _infrastructure()
    schema = infra.schemas.add(namespace=SWITCH_NS)
    schema.jsonschema.definition = SWITCH_SCHEMA

    with pytest.raises(InfrastructureError, match="Duplicate schema"):
        InfraGraphService().set_graph(infra)


def test_invalid_schema_is_rejected():
    infra = _infrastructure(with_schema=False)
    schema = infra.schemas.add(namespace="bad.v1")
    schema.jsonschema.definition = "type: 12\n"

    with pytest.raises(ERRORS):
        InfraGraphService().set_graph(infra)


def test_query_by_role_mtu_and_existence():
    service = _service()
    _lab(service)

    assert _instances(_query(service, "$[?match($.role, 'leaf')]")) == ["leafsw.0", "leafsw.1"]
    assert _instances(_query(service, "$[?$.mtu == 9100]")) == ["leafsw.0", "spine.0"]
    assert _instances(_query(service, "$.nos")) == ["leafsw.0", "leafsw.1"]
    assert len(_instances(_query(service, "$"))) == 3
    # match() is a whole match
    assert _query(service, "$[?match($.role, 'lea')]") == []
    assert _instances(_query(service, "$[?search($.role, 'lea')]")) == ["leafsw.0", "leafsw.1"]


def test_query_with_node_identifiers_and_references_in_response():
    service = _service()
    _lab(service)
    _annotate(service, None, [("leafsw[0]", "leafsw0-config", "/interfaces/eth0")])

    nodes = _query(service, "$[?$.mtu == 9100]", node_identifiers=["leafsw[0:2]"])
    assert _instances(nodes) == ["leafsw.0"]
    refs = {(r.schema, r.document, r.pointer or "") for r in nodes[0].references}
    assert refs == {(SWITCH_NS, "leafsw0-config", "")}

    nodes = _query(service, "$[?$.speed == '100G']")
    assert {r.pointer or "" for n in nodes for r in n.references} == {"/interfaces/eth0"}


def test_query_combines_with_attribute_filters():
    service = _service()
    _lab(service)
    annotation = Annotation()
    annotation.nodes.add(name="leafsw[0]").attributes.add(attribute="rack", value="r12")
    service.annotate_graph(annotation)

    request = QueryRequest()
    request.choice = QueryRequest.ATTRIBUTE_QUERY
    node_filter = request.attribute_query.node_filters.add(name="f")
    node_filter.schema_filters.add(schema=SWITCH_NS, path="$[?$.role == 'leaf']")
    node_filter.attribute_filters.attributes.add(attribute="rack", value="r12")
    nodes = service.query_graph(request).attribute_query.nodes[0].nodes

    assert _instances(nodes) == ["leafsw.0"]


@pytest.mark.parametrize("path", ["", "role", "$[?"])
def test_invalid_jsonpath_and_unknown_schema_are_errors(path):
    service = _service()
    _lab(service)

    with pytest.raises(ERRORS):
        _query(service, path)
    with pytest.raises(InfrastructureError, match="Unknown schema"):
        _query(service, "$", schema="nope.v1")


def test_openapi_schema_and_descendant_query():
    infra = _infrastructure(with_schema=False)
    schema = infra.schemas.add(namespace="otg.config.v1")
    schema.openapi.root = "Config"
    schema.openapi.definition = OTG_OPENAPI
    service = InfraGraphService()
    service.set_graph(infra)

    _annotate(
        service,
        {
            "lab1": "ports:\n  - name: p1\n    location: localhost:5555\n  - name: p2\n    location: localhost:5556\n",
        },
        [("tgen[0]", "lab1", "/ports/0"), ("tgen[1]", "lab1", "/ports/1"), ("controller", "lab1", None)],
        namespace="otg.config.v1",
    )
    with pytest.raises(ERRORS):
        _annotate(service, {"lab2": "ports:\n  - location: x\n"}, namespace="otg.config.v1")

    ns = "otg.config.v1"
    assert _instances(_query(service, "$[?match($.location, 'localhost:.*')]", ns)) == ["tgen.0", "tgen.1"]
    assert _instances(_query(service, "$..[?@.location == 'localhost:5556']", ns)) == ["controller.0"]


def test_catastrophic_pattern_in_path_does_not_hang():
    service = _service()
    _annotate(service, {"a": "role: leaf\nnos: " + "a" * 40 + "\n"}, [("leafsw[0]", "a", None)])

    assert _query(service, "$[?match($.nos, '(a+)+b')]") == []


def test_get_graph_round_trip():
    service = _service()
    _lab(service)
    _annotate(service, None, [("leafsw[0]", "leafsw0-config", "/interfaces/eth0")])

    request = GraphRequest()
    request.choice = GraphRequest.INFRAGRAPH
    request.infragraph.annotations.choice = AnnotationType.PARTIAL
    result = json.loads(service.get_graph(request))

    documents = result["annotations"]["schemas"][0]
    assert documents["namespace"] == SWITCH_NS
    assert [d["name"] for d in documents["documents"]] == ["leafsw0-config", "leafsw1-config", "spine0-config"]
    assert documents["documents"][2]["value"] == '{"mtu":9100,"role":"spine"}'
    assert result["infrastructure"]["schemas"][0]["namespace"] == SWITCH_NS
    node = next(n for n in result["annotations"]["nodes"] if n["name"] == "leafsw.0.asic.0")
    assert node["references"] == [{"document": "leafsw0-config"}, {"document": "leafsw0-config", "pointer": "/interfaces/eth0"}]

    restored = InfraGraphService()
    restored.set_graph(json.dumps(result["infrastructure"]))
    restored.annotate_graph(json.dumps(result["annotations"]))
    assert restored._documents.keys() == service._documents.keys()
    assert restored._node_references == service._node_references
