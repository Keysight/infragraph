# Infragraph Versioning

Infragraph uses semantic versioning in the format MAJOR.MINOR.PATCH, where each component is a non-negative integer without leading zeroes.

* MAJOR — Increment for incompatible API changes (reset MINOR and PATCH).  
* MINOR — Increment for backward-compatible feature additions (reset PATCH).  
* PATCH — Increment for backward-compatible bug fixes.  

Once released, a versioned package must remain immutable. All changes require a new version.

A version bump occurs after every PR merge into the main branch and must be submitted as a standalone MR, never combined with other changes. This maintains strict adherence to semantic versioning rules and ensures clear traceability.

Pre-release versions use a hyphen with identifiers (e.g., 1.0.0-alpha).  
Build metadata follows a plus sign and does not affect precedence (e.g., 1.0.0+20130313144700).

## Versioning Rules

* MAJOR — Incompatible API changes.  
* MINOR — Backward-compatible additions.  
* PATCH — Backward-compatible bug fixes.  
* Pre-release — Unstable or incomplete versions.  
* Build metadata — Environment or build details only.  
* Version bumps — Done post-merge and as a dedicated MR.
