These examples demonstrate how to go `from describing` a device/infrastructure using text/schematics/diagrams etc., `to defining` it using the standardized Device/Infrastructure models `to visualizing` it using open source available tools.

## DGX-A100 Server
This server diagram acts as an example of how multiple components can be connected to a single component such as multiple gpu components are connected to a single pcie switch.

The graph model is able to capture the asymmetric layout of the device.
<img src="./images/dgxa100.png" />
<details closed>
<summary><strong>Device Definition using OpenAPI Device Model</strong></summary>
```yaml
{% include-markdown "./examples/dgxa100.yaml" %}
```
</details>
### TBD: add visualization using mermaid? or svg? of the device

## H200-NVL2
### TBD: add schematic image of device
<details closed>
<summary><strong>Device Definition using OpenAPI Device Model</strong></summary>
```yaml
{% include-markdown "./examples/hierarchical-device.yaml" %}
```
</details>
### TBD: add visualization using mermaid? or svg? of the device

## ScaleUp/ScaleOut Infrastructure
### TBD: add schematic image of infrastructure (svg)
<details closed>
<summary><strong>Infrastructure Definition using OpenAPI Infrastructure Model</strong></summary>
```yaml
{% include-markdown "./examples/scaleup-scaleout.yaml" %}
```
</details>
### TBD: add visualization using mermaid? or svg? of the device
