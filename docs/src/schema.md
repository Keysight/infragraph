## Introducing the InfraGraph (INFRAstructure GRAPH) schema
A graph is a natural fit to describe a system of systems in a clear, intuitive, and mathematically precise manner.

![graph](./images/graph.png)

* Node or vertex represents an entity like a component, device, user, router, etc
* Edge represents a relationship between nodes
* Properties store additional information about nodes or edges

### Principles
[InfraGraph](https://github.com/Keysight/infragraph) is a `collection of APIs and Models` used to describe AI/HPC infrastructure based on the following core principles:

* logical infrastructure can be described using graph concepts such as vertexes and edges
    * vertexes are device instances
    * an edge is 2 device instances separated by a link
    * a path is a collection of connections
* there is a difference between logical infrastructure and physical definition
* logical infrastructure should be composable
* logical infrastructure is loosely coupled to physical definitions
* due to the possible scale of AI/HPC deployments, logical infrastructure needs to be scalable without duplicating content

### OpenapiArt
This repository makes use of [OpenAPIArt](https://github.com/open-traffic-generator/openapiart) to do the following:

    * create declarative intent based Models and APIs
    * auto-generate the following artifacts:
        * [Redocly documentation](openapi.html) of APIs and Models
        * `Python/Go SDKs` that allow for creating `fluent` client/server code over `REST/Protobuf` transports
