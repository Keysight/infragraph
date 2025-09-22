### Weifeng Zhang comments:
- Q. Any plan to formalize the keywords (or tags) in the schema description? It looks a bit random and mixed, which makes it hard to validate the schema.
    - A. validation of a concrete definition is done using the generated sdk clients (python/go) against the openapi schema

- Q. I don't see any part to describe memory and/or storage components. Have they been defined or just skipped for simplicity of descriptions?
    - A. they have been skipped at this time

- Q. Currently, an entity is defined by "name" without specifying its "type". This also makes its subordinate component tags somewhat random.
    - A. device is just a container of components, the name gives it context. `TBD: create a secondary networkx graph of just device nodes that can be annotated`

- Q. Should the definition (abstraction) of an entity be separated from its instance? Just like the OOP programming with class and instantiation. This may help make the schema more friendly for hierarchical description, and easier to zoom in/out for a structured view.
    - A. devices, components and edges are the base model and are separate from the complete graph

- Q. The connections in the schema look like enumerated and long. It seems difficult to describe a complex system at scale. For example, if we want to describe a switch with 256 ports. The combination may be enormous.
    - A. patterns are available in the new schema, and the result is a networkx graph

- Q. How do we model the dynamic features of an entity? For example, a link may be allocated with a partial capacity/bandwidth or time shared (pipelined). This feature should help us to accurately model the system's performance.
    - A. annotate the networkx nodes with a proposed schema that can be incorporated in the schema at a later date

- Q. The compute entity currently doesn't contain any descriptions on its capacity, such as TFLOPS, or integer/floating point operations with various precisions.
    - A. TBD need to move to a choice to accomodate schema expansion

- Q. Any plan to expand the schema for modeling the management/sustainability aspects?
    - A. annotate the networkx nodes with a proposed schema that can be incorporated in the schema at a later date

- Q. Any plan to model a super node using the schema
    - A. TBD find a reference to a super node and model it

### Jascha Achterberg's comments:
- Does the SoC example I gave in my initial email make sense to you? Another context in which I believe this would be relevant is in the context of Cache hierarchies, where ideally one could model all Cache levels but I believe currently Astra-Sim does not capture these levels. A schema would ideally allow to both see Cache as one element or actually capture the more granular relationship.