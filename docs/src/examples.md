These examples demonstrate `describing` a variety of devices and infrastructures using text descriptions and diagrams to `defining` them using a `standardized schema` for capturing infrastructure.

## DGX-A100 Server
This server diagram acts as an example of how multiple components can be connected to a single component such as multiple gpu components are connected to a single pcie switch.

The graph model is able to capture the asymmetric layout of the device.

### Description
![dgxa100](./images/dgxa100.png)

### Standardized Definition
<details open>
<summary><strong>DGX-A100 Device Definition using OpenAPI Device Model</strong></summary>
```yaml
{% include-markdown "./examples/dgxa100.yaml" %}
```
</details>

## GH200-MGX
### Description
#### NPU Component
![spine and leaf](./images/gh200.png)
#### Device
![spine and leaf](./images/gh200-mgx.png)

### Standardized Definition
<details open>
<summary><strong>GH200-MGX Device Definition using OpenAPI Device Model</strong></summary>
```yaml
{% include-markdown "./examples/hierarchical-device.yaml" %}
```
</details>

## ScaleUp/ScaleOut Infrastructure

### Description
![ai-ml-hpc-datacenter-networks](./images/ai-ml-hpc-datacenter-networks.png)
https://mips.com/blog/reimagining-ai-infrastructure-the-power-of-converged-back-end-networks/


- 1024 hosts
    - 1 npu/host
    - 10 nics/host
- 512 scaleup switches
    - 16 ports/switch
- 2 scaleout switches
    - 1024 ports/switch
- 64 Racks
    - 16 hosts/rack
    - 8 scale up switches/rack

![ai-ml-hpc-datacenter-networks](./images/scaleup-scaleout.png)

### Standardized Definition
<details open>
<summary><strong>ScaleUp/ScaleOut Infrastructure Definition using OpenAPI Infrastructure Model</strong></summary>
```yaml
{% include-markdown "./examples/scaleup-scaleout.yaml" %}
```
</details>
