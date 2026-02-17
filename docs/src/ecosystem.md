
# Chakra + InfraGraph Ecosystem

MLCommons [**Chakra**](https://mlcommons.org/working-groups/research/chakra/) represents the details of any AI workload by capturing _Execution Traces (ET)_ - graphs of operators, tensors, dependencies, and timing.

**InfraGraph** represents the underlying systems and infrastructure used for AI training or inference - hosts, NICs, xPUs/accelerators, interconnects, and topologies - using programmatic system blueprints.

Together, **Chakra + InfraGraph** let you pair workload traces with infrastructure blueprints to analyze current systems and co‑design future ones, while safely sharing artifacts across teams and partners.

![InfraGraph+Chakra-Ecosystem](./images/chakra-infragraph-ecosystem.png)

## InfraGraph Helper Tools
Like **Chakra**, **InfraGraph** also proposes a set of helper tools that can help users while working with InfraGraph. 

#### 1. Converters:
Many open‑source and commercial tools model systems using their own schemas (e.g., lspci, lshw, OpenMPI tools, NetBox, etc.). InfraGraph is adding translators to ensure interoperability - import from (and export to) these formats without rewriting everything.

#### 2. Discoverers:
Discovery has two aspects:
- **Configuration discovery** - capture the attributes of each node/host device.
- **Topology discovery** - map interconnections across a distributed system.

InfraGraph aims to support dynamic discovery so infrastructure details can be captured automatically and kept up to date.

#### 3. Blueprints:
We’re building blueprint templates for commonly used systems in AI data centers (AI DCs):
- **Devices** - hosts from NVIDIA, Meta, Dell, HPE, etc. vendors, devices like NICs, XPUs/accelerators, and other components.
- **Fabrics/topologies** - standard definitions such as Clos and Dragonfly.

These blueprints help researchers quickly assemble infrastructure definitions for experimentation and serve as reference models when building new designs.

#### 4. Visualizers:
Graphical views make it easier to spot design issues:
- Drill‑down to component‑level details.
- Zoom‑out to high‑level system connectivity.
    
Visualizers assist developers in understanding structure, bottlenecks, and correctness.

>**Note:** Some of these tools are _work-in-progress_ and we invite contributions from the community.

## Privacy & Obfuscation

InfraGraph, like Chakra, supports selective disclosure and obfuscation so you can safely share only high‑level infrastructure definitions.

#### Private annotations: 
One can attach additional details to infrastructure elements or devices, links, fabrics, racks/pods - as annotations (structured fields or free text). These may include vendor‑specific information, firmware/driver versions, internal asset tags, SKUs, or configuration notes. 

- Annotations can be **kept private** for internal tools and workflows. 
- Private annotations can be **excluded or obfuscated** when exporting or sharing the InfraGraph outside your organization.

#### Safe sharing: 
When publishing to vendors or the open‑source community, you decide which fields remain, which are transformed, and which are removed - preserving the high‑level system definition while protecting sensitive details about the network and device configurations.

## Sharing & Interoperability
InfraGraph definitions can be shared with vendors and the open‑source community and used with a variety of analyzers, simulators, or emulators (open or commercial). The emphasis is on:
- **Portability:** consistent, schema‑driven artifacts.
- **Compatibility:** converters for common ecosystem tools.
- **Safety:** optional obfuscation to protect IP while enabling collaboration.
- **Composability:** components or devices defined separately can be reused across systems or inserted into different topologies, making it easy to mix, match, and assemble infrastructure from modular parts.
