These examples demonstrate `describing` a variety of device/infrastructure using text/schematics/diagrams etc., to `defining` them using a standardized schema to `visualizing` them using readily available open source tools.

## DGX-A100 Server
This server diagram acts as an example of how multiple components can be connected to a single component such as multiple gpu components are connected to a single pcie switch.

The graph model is able to capture the asymmetric layout of the device.

### Description
<img src="./images/dgxa100.png" />

### Standardized Definition
<details open>
<summary><strong>DGX-A100 Device Definition using OpenAPI Device Model</strong></summary>
```yaml
{% include-markdown "./examples/dgxa100.yaml" %}
```
</details>

### Visualization
Add an svg/mermaid visualization here...

## GH200-MGX
### Description
<img src="./images/gh200.png" />
<img src="./images/gh200-mgx.png" />

### Standardized Definition
<details open>
<summary><strong>GH200-MGX Device Definition using OpenAPI Device Model</strong></summary>
```yaml
{% include-markdown "./examples/hierarchical-device.yaml" %}
```
</details>

### Visualization
Add an svg/mermaid visualization here...

## ScaleUp/ScaleOut Infrastructure

### Description
<img src="./images/scaleup-scaleout.png" />

### Standardized Definition
<details open>
<summary><strong>ScaleUp/ScaleOut Infrastructure Definition using OpenAPI Infrastructure Model</strong></summary>
```yaml
{% include-markdown "./examples/scaleup-scaleout.yaml" %}
```
</details>

### Visualization
Add an svg/mermaid visualization here...
