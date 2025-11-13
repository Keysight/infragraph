# Infragraph Versioning

Infragraph uses semantic versioning in the format MAJOR.MINOR.PATCH, where each component is a non-negative integer without leading zeroes.

* MAJOR — Increment for incompatible API changes (reset MINOR and PATCH).  
* MINOR — Increment for backward-compatible feature additions (reset PATCH).  
* PATCH — Increment for backward-compatible bug fixes.  

Once released, a versioned package must remain immutable. All changes require a new version.

## Version Update Policy

The Infragraph version is maintained in [api/info.yaml](../../api/info.yaml). Any version change must be made exclusively in this file, and the modification must be included in a dedicated merge request (MR).

## Version Bumping Rules
A version bump is required whenever there is a change to the API or models. The version follows the `MAJOR.MINOR.PATCH` format, updated according to the following rules:

- **MAJOR**: Incremented for incompatible schema or API changes, such as removing or renaming schema entities or endpoints. When the MAJOR version is incremented, both MINOR and PATCH values are reset to zero.  
- **MINOR**: Incremented for backward-compatible feature additions, such as introducing new schemas or APIs that do not break existing functionality. In this case, PATCH is reset to zero.  
- **PATCH**: Incremented for backward-compatible fixes, small corrections, or documentation adjustments that do not alter the schema interface.

## Change Management
Each schema change that requires a version bump must be submitted in a standalone MR. This separation ensures strict adherence to semantic versioning principles and maintains clear traceability of version history.

## Immutability of Releases
Once a versioned package is released, it becomes immutable. No further modifications can be made to that version. Any subsequent change must occur through a new version bump as defined above.

This process enforces strong semantic versioning discipline, ensuring version numbers accurately represent schema compatibility and that every schema or API update is clearly communicated through controlled, versioned releases.