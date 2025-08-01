## Overview

Modern AI systems, comprising diverse scale-up and scale-out interconnect topologies that integrate complex heterogeneous components, connected together via diverse means, face a lack of standardized overall infrastructure description, all which hinders benchmarking, simulation, and emulation.

## Introducing GRAPHIT (Graph based Infrastructure)
[GraphIt](https://github.com/Keysight/graphit) is a schema used to describe AI/HPC infrastructure and is based on the following core principles:

* logical infrastructure can be described using graph concepts such as vertexes and edges
    * vertexes are device instances
    * an edge is 2 device instances separated by a link
    * a path is a collection of connections
* there is a difference between logical infrastructure and physical definition
* logical infrastructure should be composable
* logical infrastructure is loosely coupled to physical definitions
* due to the possible scale of AI/HPC deployments, logical infrastructure needs to be scalable without duplicating content
* use [OpenAPIArt](https://github.com/open-traffic-generator/openapiart) to create declarative APIs and Models and optionally auto-generate the following artifacts:
    * [Redocly documentation](openapi.html) of APIs and Models
    * Fluent Python/Go SDKs over REST/Protobuf transports


## [Features](model.md)

Cluster Infrastructure as a graph is an actively developed specification, with contributions from real [use cases](examples.md). The model defines the following components to define a infrastructure:
<!-- TODO add links from bold items to paragraphs in Model section -->
* **Device** definitions with ability to model its internals as a graph
* **Device Components** allowing users to define the device internal components like:
    - nic
    - ports
    - npus
* **Links** definition for:
    - components interconnect
	- device interconnect
    - Defining the bandwidth of the links
* **Connections** between:
    - internal components of a device
    - one device to another

Explore an in-depth explanation of the topology model, covering its structure, essential components, and how it supports efficient design and analysis. [This resource](model.md) provides valuable insights into the principles behind topology and how to apply them effectively.

## [Annotation](annotate.md)

This section provides a comprehensive guide on how a user can annotate various parts of infrastructre and add more details like DeviceType, Rank Identifier and so on. It covers the model description with examples for binding physical attributes with the logical infrastructure definition.


## [Getting Started With Topology Creation](create.md)

[This walkthrough](create.md) guide demonstrates how anyone can create a topology from scratch, highlighting key steps and best practices to build a solid foundation. It offers a clear, step-by-step approach that makes topology creation accessible to beginners and experts alike.

## Community

Use our community resources to get help with Infrastructure As A Graph:

* [Infrastructure As A Graph on Github](https://github.com/Keysight/graphit)
