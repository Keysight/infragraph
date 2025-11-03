"""
The following command generates these artifacts:
    - ./artifacts/openapi.yaml
    - ./artifacts/openapi.json
"""

import openapiart

openapiart.OpenApiArt(
    api_files=["./api/info.yaml", "./api/api.yaml"],
    protobuf_name="infragraph",
    artifact_dir="artifacts",
    generate_version_api=True,
    strict_description_validation="all"
).GeneratePythonSdk(package_name="infragraph")
