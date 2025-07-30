"""
The following command produces these artifacts:
    - ./artifacts/openapi.yaml
    - ./artifacts/openapi.json
    - ./artifacts/openapi.html
"""

import subprocess
import openapiart

openapiart.OpenApiArt(
    api_files=["./api/info.yaml", "./api/api.yaml"],
    protobuf_name="infra",
    artifact_dir="artifacts",
    generate_version_api=False,
).GeneratePythonSdk(package_name="infra")

subprocess.call(["redocly", "build-docs", "./artifacts/openapi.yaml", "-o", "./artifacts/openapi.html"])
