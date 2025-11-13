# Infragraph Versioning

Infragraph uses semantic versioning in the format MAJOR.MINOR.PATCH, where each component is a non-negative integer without leading zeroes.

* MAJOR — Increment for incompatible API changes (reset MINOR and PATCH).  
* MINOR — Increment for backward-compatible feature additions (reset PATCH).  
* PATCH — Increment for backward-compatible bug fixes.  

Once released, a versioned package must remain immutable. All changes require a new version.

A version bump occurs whenever there is a change in the api or models. If the change is a major incompatible modification to the schema (e.g., removing or renaming schema or api), the MAJOR version must be incremented, and the MINOR and PATCH versions reset to zero. For backward-compatible feature additions to the schema, such as adding new schema or apis without breaking existing compatibility, the MINOR version is incremented and PATCH reset. For backward-compatible bug fixes or minor corrections that do not affect the schema interface, the PATCH version is incremented.

Furthermore, after every change to the schema, the corresponding version bump must be made in a standalone merge request (MR) separate from other changes. This ensures strict adherence to semantic versioning rules and clear traceability. Once a versioned package is released, it must remain immutable, and no changes can be made without a subsequent version bump.

This approach aligns with strict semantic versioning, emphasizing the importance of version changes reflecting actual schema compatibility impacts and ensuring that all schema changes are communicated through clearly versioned releases.

Pre-release versions use a hyphen with identifiers (e.g., 1.0.0-alpha).  
Build metadata follows a plus sign and does not affect precedence (e.g., 1.0.0+20130313144700).

## Versioning Rules

* MAJOR — Incompatible API changes.  
* MINOR — Backward-compatible additions.  
* PATCH — Backward-compatible bug fixes.  
* Pre-release — Unstable or incomplete versions.  
* Build metadata — Environment or build details only.  
* Version bumps — Done post-merge and as a dedicated MR.