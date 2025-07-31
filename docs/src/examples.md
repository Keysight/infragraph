# Infrastructure As A Graph Examples:

## CLOS Topology

### 1 tier - 8 hosts

Infrastructure As A Graph for a Rack Switch having 8 host can be defined as:


<details open>
<summary><strong>YAML Definition</strong></summary>

```yaml
inventory:
  devices:
    GENERIC_HOST:
      name: GENERIC_HOST
      components:
        nic:
          name: nic
          count: 1
          nic:
            ethernet: {}
        npu:
          name: npu
          count: 1
          npu:
            memory: MEM_UNSPECIFIED
        npu_interconnect_switch:
          name: npu_interconnect_switch
          count: 1
          switch:
            custom: {}
      connections:
        - npu.0.pcie.nic.0
        - npu.0.npu_interconnect.npu_interconnect_switch.0
      links:
        npu_interconnect:
          name: npu_interconnect
          bandwidth:
            gbps: 1600
        pcie:
          name: pcie
    TIER_0:
      name: TIER_0
      components:
        asic:
          name: asic
          count: 1
          cpu:
            memory: MEM_RAM
        port:
          name: port
          count: 8
          nic:
            ethernet: {}
      connections:
        - port.0.mii.asic.0
        - port.1.mii.asic.0
        - port.2.mii.asic.0
        - port.3.mii.asic.0
        - port.4.mii.asic.0
        - port.5.mii.asic.0
        - port.6.mii.asic.0
        - port.7.mii.asic.0
      links:
        mii:
          name: mii
  links:
    100_gbps:
      name: 100_gbps
      bandwidth:
        gbps: 100
      description: 100 Gbps Ethernet link
device_instances:
  generic:
    name: generic
    count: 8
    device: GENERIC_HOST
  tier_0:
    name: tier_0
    count: 1
    device: TIER_0
connections:
  - generic.0.nic.0.100_gbps.tier_0.0.port.0
  - generic.1.nic.0.100_gbps.tier_0.0.port.1
  - generic.2.nic.0.100_gbps.tier_0.0.port.2
  - generic.3.nic.0.100_gbps.tier_0.0.port.3
  - generic.4.nic.0.100_gbps.tier_0.0.port.4
  - generic.5.nic.0.100_gbps.tier_0.0.port.5
  - generic.6.nic.0.100_gbps.tier_0.0.port.6
  - generic.7.nic.0.100_gbps.tier_0.0.port.7


```

</details>

<br>

<details>
<summary><strong>JSON Definition</strong></summary>

```json
{
    "inventory": {
        "devices": {
            "GENERIC_HOST": {
                "name": "GENERIC_HOST",
                "components": {
                    "npu_interconnect_switch": {
                        "name": "npu_interconnect_switch",
                        "count": 1,
                        "switch": {
                            "custom": {}
                        }
                    },
                    "nic": {
                        "name": "nic",
                        "count": 1,
                        "nic": {
                            "ethernet": {}
                        }
                    },
                    "npu": {
                        "name": "npu",
                        "count": 1,
                        "npu": {
                            "memory": "MEM_UNSPECIFIED"
                        }
                    }
                },
                "links": {
                    "pcie": {
                        "name": "pcie"
                    },
                    "npu_interconnect": {
                        "name": "npu_interconnect",
                        "bandwidth": {
                            "gbps": 1600
                        }
                    }
                },
                "connections": [
                    "npu.0.pcie.nic.0",
                    "npu.0.npu_interconnect.npu_interconnect_switch.0"
                ]
            },
            "TIER_0": {
                "name": "TIER_0",
                "components": {
                    "port": {
                        "name": "port",
                        "count": 8,
                        "nic": {
                            "ethernet": {}
                        }
                    },
                    "asic": {
                        "name": "asic",
                        "count": 1,
                        "cpu": {
                            "memory": "MEM_RAM"
                        }
                    }
                },
                "links": {
                    "mii": {
                        "name": "mii"
                    }
                },
                "connections": [
                    "port.0.mii.asic.0",
                    "port.1.mii.asic.0",
                    "port.2.mii.asic.0",
                    "port.3.mii.asic.0",
                    "port.4.mii.asic.0",
                    "port.5.mii.asic.0",
                    "port.6.mii.asic.0",
                    "port.7.mii.asic.0"
                ]
            }
        },
        "links": {
            "100_gbps": {
                "name": "100_gbps",
                "description": "100 Gbps Ethernet link",
                "bandwidth": {
                    "gbps": 100
                }
            }
        }
    },
    "device_instances": {
        "tier_0": {
            "name": "tier_0",
            "device": "TIER_0",
            "count": 1
        },
        "generic": {
            "name": "generic",
            "device": "GENERIC_HOST",
            "count": 8
        }
    },
    "connections": [
        "generic.0.nic.0.100_gbps.tier_0.0.port.0",
        "generic.1.nic.0.100_gbps.tier_0.0.port.1",
        "generic.2.nic.0.100_gbps.tier_0.0.port.2",
        "generic.3.nic.0.100_gbps.tier_0.0.port.3",
        "generic.4.nic.0.100_gbps.tier_0.0.port.4",
        "generic.5.nic.0.100_gbps.tier_0.0.port.5",
        "generic.6.nic.0.100_gbps.tier_0.0.port.6",
        "generic.7.nic.0.100_gbps.tier_0.0.port.7"
    ]
}
```

</details>

<br>

## Dragonfly Topology

### a=4, p=2, h=2

A dragonfly topology with 4 routers per group, 2 terminals per router and 2 outerlinks per every router can be represented in the following manner:


<details open>
<summary><strong>YAML Definition</strong></summary>

```yaml
inventory:
  devices:
    generic_host:
      name: generic_host
      components:
        nic:
          name: nic
          count: 1
          nic:
            ethernet: {}
        npu:
          name: npu
          count: 1
          npu: {}
      connections:
        - npu.0.pcie.nic.0
      links:
        pcie:
          name: pcie
          type: LINK_PCIE
    generic_switch:
      name: generic_switch
      components:
        asic:
          name: asic
          count: 1
          cpu:
            memory: MEM_RAM
        nic:
          name: nic
          count: 7
          nic:
            ethernet: {}
      connections:
        - nic.0.mii.asic.0
        - nic.1.mii.asic.0
        - nic.2.mii.asic.0
        - nic.3.mii.asic.0
        - nic.4.mii.asic.0
        - nic.5.mii.asic.0
        - nic.6.mii.asic.0
      links:
        mii:
          name: mii
          type: LINK_CUSTOM
  links:
    100Gbps:
      bandwidth:
        gbps: 100
      name: 100Gbps
      type: LINK_ETHERNET

deviceInstances:
  host:
    name: host
    device: generic_host
    count: 72
  switch:
    name: switch
    device: generic_switch
    count: 36
connections:
  - switch.0.nic.0.100Gbps.host.0.nic.0
  - switch.0.nic.1.100Gbps.host.1.nic.0
  - switch.1.nic.0.100Gbps.host.2.nic.0
  - switch.1.nic.1.100Gbps.host.3.nic.0
  - switch.2.nic.0.100Gbps.host.4.nic.0
  - switch.2.nic.1.100Gbps.host.5.nic.0
  - switch.3.nic.0.100Gbps.host.6.nic.0
  - switch.3.nic.1.100Gbps.host.7.nic.0
  - switch.0.nic.2.100Gbps.switch.1.nic.2
  - switch.0.nic.3.100Gbps.switch.2.nic.2
  - switch.0.nic.4.100Gbps.switch.3.nic.2
  - switch.1.nic.3.100Gbps.switch.2.nic.3
  - switch.1.nic.4.100Gbps.switch.3.nic.3
  - switch.2.nic.4.100Gbps.switch.3.nic.4
  - switch.4.nic.0.100Gbps.host.8.nic.0
  - switch.4.nic.1.100Gbps.host.9.nic.0
  - switch.5.nic.0.100Gbps.host.10.nic.0
  - switch.5.nic.1.100Gbps.host.11.nic.0
  - switch.6.nic.0.100Gbps.host.12.nic.0
  - switch.6.nic.1.100Gbps.host.13.nic.0
  - switch.7.nic.0.100Gbps.host.14.nic.0
  - switch.7.nic.1.100Gbps.host.15.nic.0
  - switch.4.nic.2.100Gbps.switch.5.nic.2
  - switch.4.nic.3.100Gbps.switch.6.nic.2
  - switch.4.nic.4.100Gbps.switch.7.nic.2
  - switch.5.nic.3.100Gbps.switch.6.nic.3
  - switch.5.nic.4.100Gbps.switch.7.nic.3
  - switch.6.nic.4.100Gbps.switch.7.nic.4
  - switch.8.nic.0.100Gbps.host.16.nic.0
  - switch.8.nic.1.100Gbps.host.17.nic.0
  - switch.9.nic.0.100Gbps.host.18.nic.0
  - switch.9.nic.1.100Gbps.host.19.nic.0
  - switch.10.nic.0.100Gbps.host.20.nic.0
  - switch.10.nic.1.100Gbps.host.21.nic.0
  - switch.11.nic.0.100Gbps.host.22.nic.0
  - switch.11.nic.1.100Gbps.host.23.nic.0
  - switch.8.nic.2.100Gbps.switch.9.nic.2
  - switch.8.nic.3.100Gbps.switch.10.nic.2
  - switch.8.nic.4.100Gbps.switch.11.nic.2
  - switch.9.nic.3.100Gbps.switch.10.nic.3
  - switch.9.nic.4.100Gbps.switch.11.nic.3
  - switch.10.nic.4.100Gbps.switch.11.nic.4
  - switch.12.nic.0.100Gbps.host.24.nic.0
  - switch.12.nic.1.100Gbps.host.25.nic.0
  - switch.13.nic.0.100Gbps.host.26.nic.0
  - switch.13.nic.1.100Gbps.host.27.nic.0
  - switch.14.nic.0.100Gbps.host.28.nic.0
  - switch.14.nic.1.100Gbps.host.29.nic.0
  - switch.15.nic.0.100Gbps.host.30.nic.0
  - switch.15.nic.1.100Gbps.host.31.nic.0
  - switch.12.nic.2.100Gbps.switch.13.nic.2
  - switch.12.nic.3.100Gbps.switch.14.nic.2
  - switch.12.nic.4.100Gbps.switch.15.nic.2
  - switch.13.nic.3.100Gbps.switch.14.nic.3
  - switch.13.nic.4.100Gbps.switch.15.nic.3
  - switch.14.nic.4.100Gbps.switch.15.nic.4
  - switch.16.nic.0.100Gbps.host.32.nic.0
  - switch.16.nic.1.100Gbps.host.33.nic.0
  - switch.17.nic.0.100Gbps.host.34.nic.0
  - switch.17.nic.1.100Gbps.host.35.nic.0
  - switch.18.nic.0.100Gbps.host.36.nic.0
  - switch.18.nic.1.100Gbps.host.37.nic.0
  - switch.19.nic.0.100Gbps.host.38.nic.0
  - switch.19.nic.1.100Gbps.host.39.nic.0
  - switch.16.nic.2.100Gbps.switch.17.nic.2
  - switch.16.nic.3.100Gbps.switch.18.nic.2
  - switch.16.nic.4.100Gbps.switch.19.nic.2
  - switch.17.nic.3.100Gbps.switch.18.nic.3
  - switch.17.nic.4.100Gbps.switch.19.nic.3
  - switch.18.nic.4.100Gbps.switch.19.nic.4
  - switch.20.nic.0.100Gbps.host.40.nic.0
  - switch.20.nic.1.100Gbps.host.41.nic.0
  - switch.21.nic.0.100Gbps.host.42.nic.0
  - switch.21.nic.1.100Gbps.host.43.nic.0
  - switch.22.nic.0.100Gbps.host.44.nic.0
  - switch.22.nic.1.100Gbps.host.45.nic.0
  - switch.23.nic.0.100Gbps.host.46.nic.0
  - switch.23.nic.1.100Gbps.host.47.nic.0
  - switch.20.nic.2.100Gbps.switch.21.nic.2
  - switch.20.nic.3.100Gbps.switch.22.nic.2
  - switch.20.nic.4.100Gbps.switch.23.nic.2
  - switch.21.nic.3.100Gbps.switch.22.nic.3
  - switch.21.nic.4.100Gbps.switch.23.nic.3
  - switch.22.nic.4.100Gbps.switch.23.nic.4
  - switch.24.nic.0.100Gbps.host.48.nic.0
  - switch.24.nic.1.100Gbps.host.49.nic.0
  - switch.25.nic.0.100Gbps.host.50.nic.0
  - switch.25.nic.1.100Gbps.host.51.nic.0
  - switch.26.nic.0.100Gbps.host.52.nic.0
  - switch.26.nic.1.100Gbps.host.53.nic.0
  - switch.27.nic.0.100Gbps.host.54.nic.0
  - switch.27.nic.1.100Gbps.host.55.nic.0
  - switch.24.nic.2.100Gbps.switch.25.nic.2
  - switch.24.nic.3.100Gbps.switch.26.nic.2
  - switch.24.nic.4.100Gbps.switch.27.nic.2
  - switch.25.nic.3.100Gbps.switch.26.nic.3
  - switch.25.nic.4.100Gbps.switch.27.nic.3
  - switch.26.nic.4.100Gbps.switch.27.nic.4
  - switch.28.nic.0.100Gbps.host.56.nic.0
  - switch.28.nic.1.100Gbps.host.57.nic.0
  - switch.29.nic.0.100Gbps.host.58.nic.0
  - switch.29.nic.1.100Gbps.host.59.nic.0
  - switch.30.nic.0.100Gbps.host.60.nic.0
  - switch.30.nic.1.100Gbps.host.61.nic.0
  - switch.31.nic.0.100Gbps.host.62.nic.0
  - switch.31.nic.1.100Gbps.host.63.nic.0
  - switch.28.nic.2.100Gbps.switch.29.nic.2
  - switch.28.nic.3.100Gbps.switch.30.nic.2
  - switch.28.nic.4.100Gbps.switch.31.nic.2
  - switch.29.nic.3.100Gbps.switch.30.nic.3
  - switch.29.nic.4.100Gbps.switch.31.nic.3
  - switch.30.nic.4.100Gbps.switch.31.nic.4
  - switch.32.nic.0.100Gbps.host.64.nic.0
  - switch.32.nic.1.100Gbps.host.65.nic.0
  - switch.33.nic.0.100Gbps.host.66.nic.0
  - switch.33.nic.1.100Gbps.host.67.nic.0
  - switch.34.nic.0.100Gbps.host.68.nic.0
  - switch.34.nic.1.100Gbps.host.69.nic.0
  - switch.35.nic.0.100Gbps.host.70.nic.0
  - switch.35.nic.1.100Gbps.host.71.nic.0
  - switch.32.nic.2.100Gbps.switch.33.nic.2
  - switch.32.nic.3.100Gbps.switch.34.nic.2
  - switch.32.nic.4.100Gbps.switch.35.nic.2
  - switch.33.nic.3.100Gbps.switch.34.nic.3
  - switch.33.nic.4.100Gbps.switch.35.nic.3
  - switch.34.nic.4.100Gbps.switch.35.nic.4
  - switch.0.nic.5.100Gbps.switch.7.nic.5
  - switch.0.nic.6.100Gbps.switch.11.nic.5
  - switch.1.nic.5.100Gbps.switch.14.nic.5
  - switch.1.nic.6.100Gbps.switch.18.nic.5
  - switch.2.nic.5.100Gbps.switch.21.nic.5
  - switch.2.nic.6.100Gbps.switch.25.nic.5
  - switch.3.nic.5.100Gbps.switch.28.nic.5
  - switch.3.nic.6.100Gbps.switch.32.nic.5
  - switch.4.nic.5.100Gbps.switch.11.nic.6
  - switch.4.nic.6.100Gbps.switch.15.nic.5
  - switch.5.nic.5.100Gbps.switch.18.nic.6
  - switch.5.nic.6.100Gbps.switch.22.nic.5
  - switch.6.nic.5.100Gbps.switch.25.nic.6
  - switch.6.nic.6.100Gbps.switch.29.nic.5
  - switch.7.nic.6.100Gbps.switch.32.nic.6
  - switch.8.nic.5.100Gbps.switch.15.nic.6
  - switch.8.nic.6.100Gbps.switch.19.nic.5
  - switch.9.nic.5.100Gbps.switch.22.nic.6
  - switch.9.nic.6.100Gbps.switch.26.nic.5
  - switch.10.nic.5.100Gbps.switch.29.nic.6
  - switch.10.nic.6.100Gbps.switch.33.nic.5
  - switch.12.nic.5.100Gbps.switch.19.nic.6
  - switch.12.nic.6.100Gbps.switch.23.nic.5
  - switch.13.nic.5.100Gbps.switch.26.nic.6
  - switch.13.nic.6.100Gbps.switch.30.nic.5
  - switch.14.nic.6.100Gbps.switch.33.nic.6
  - switch.16.nic.5.100Gbps.switch.23.nic.6
  - switch.16.nic.6.100Gbps.switch.27.nic.5
  - switch.17.nic.5.100Gbps.switch.30.nic.6
  - switch.17.nic.6.100Gbps.switch.34.nic.5
  - switch.20.nic.5.100Gbps.switch.27.nic.6
  - switch.20.nic.6.100Gbps.switch.31.nic.5
  - switch.21.nic.6.100Gbps.switch.34.nic.6
  - switch.24.nic.5.100Gbps.switch.31.nic.6
  - switch.24.nic.6.100Gbps.switch.35.nic.5
  - switch.28.nic.6.100Gbps.switch.35.nic.6

```

</details>

<br>

<details>
<summary><strong>JSON Definition</strong></summary>

```json
{
    "inventory": {
        "devices": {
            "generic_switch": {
                "name": "generic_switch",
                "components": {
                    "asic": {
                        "name": "asic",
                        "count": 1,
                        "cpu": {
                            "memory": "MEM_RAM"
                        }
                    },
                    "nic": {
                        "name": "nic",
                        "count": 7,
                        "nic": {
                            "ethernet": { }
                        }
                    }
                },
                "links": {
                    "mii": {
                        "name": "mii",
                        "type": "LINK_CUSTOM"
                    }
                },
                "connections": [
                    "nic.0.mii.asic.0",
                    "nic.1.mii.asic.0",
                    "nic.2.mii.asic.0",
                    "nic.3.mii.asic.0",
                    "nic.4.mii.asic.0",
                    "nic.5.mii.asic.0",
                    "nic.6.mii.asic.0"
                ]
            },
            "generic_host": {
                "name": "generic_host",
                "components": {
                    "npu": {
                        "name": "npu",
                        "count": 1,
                        "npu": { }
                    },
                    "nic": {
                        "name": "nic",
                        "count": 1,
                        "nic": {
                            "ethernet": { }
                        }
                    }
                },
                "links": {
                    "pcie": {
                        "name": "pcie",
                        "type": "LINK_PCIE"
                    }
                },
                "connections": [
                    "npu.0.pcie.nic.0"
                ]
            }
        },
        "links": {
            "100Gbps": {
                "name": "100Gbps",
                "type": "LINK_ETHERNET",
                "bandwidth": {
                    "gbps": 100
                }
            }
        }
    },
    "deviceInstances": {
        "switch": {
            "name": "switch",
            "device": "generic_switch",
            "count": 36
        },
        "host": {
            "name": "host",
            "device": "generic_host",
            "count": 72
        }
    },
    "connections": [
        "switch.0.nic.0.100Gbps.host.0.nic.0",
        "switch.0.nic.1.100Gbps.host.1.nic.0",
        "switch.1.nic.0.100Gbps.host.2.nic.0",
        "switch.1.nic.1.100Gbps.host.3.nic.0",
        "switch.2.nic.0.100Gbps.host.4.nic.0",
        "switch.2.nic.1.100Gbps.host.5.nic.0",
        "switch.3.nic.0.100Gbps.host.6.nic.0",
        "switch.3.nic.1.100Gbps.host.7.nic.0",
        "switch.0.nic.2.100Gbps.switch.1.nic.2",
        "switch.0.nic.3.100Gbps.switch.2.nic.2",
        "switch.0.nic.4.100Gbps.switch.3.nic.2",
        "switch.1.nic.3.100Gbps.switch.2.nic.3",
        "switch.1.nic.4.100Gbps.switch.3.nic.3",
        "switch.2.nic.4.100Gbps.switch.3.nic.4",
        "switch.4.nic.0.100Gbps.host.8.nic.0",
        "switch.4.nic.1.100Gbps.host.9.nic.0",
        "switch.5.nic.0.100Gbps.host.10.nic.0",
        "switch.5.nic.1.100Gbps.host.11.nic.0",
        "switch.6.nic.0.100Gbps.host.12.nic.0",
        "switch.6.nic.1.100Gbps.host.13.nic.0",
        "switch.7.nic.0.100Gbps.host.14.nic.0",
        "switch.7.nic.1.100Gbps.host.15.nic.0",
        "switch.4.nic.2.100Gbps.switch.5.nic.2",
        "switch.4.nic.3.100Gbps.switch.6.nic.2",
        "switch.4.nic.4.100Gbps.switch.7.nic.2",
        "switch.5.nic.3.100Gbps.switch.6.nic.3",
        "switch.5.nic.4.100Gbps.switch.7.nic.3",
        "switch.6.nic.4.100Gbps.switch.7.nic.4",
        "switch.8.nic.0.100Gbps.host.16.nic.0",
        "switch.8.nic.1.100Gbps.host.17.nic.0",
        "switch.9.nic.0.100Gbps.host.18.nic.0",
        "switch.9.nic.1.100Gbps.host.19.nic.0",
        "switch.10.nic.0.100Gbps.host.20.nic.0",
        "switch.10.nic.1.100Gbps.host.21.nic.0",
        "switch.11.nic.0.100Gbps.host.22.nic.0",
        "switch.11.nic.1.100Gbps.host.23.nic.0",
        "switch.8.nic.2.100Gbps.switch.9.nic.2",
        "switch.8.nic.3.100Gbps.switch.10.nic.2",
        "switch.8.nic.4.100Gbps.switch.11.nic.2",
        "switch.9.nic.3.100Gbps.switch.10.nic.3",
        "switch.9.nic.4.100Gbps.switch.11.nic.3",
        "switch.10.nic.4.100Gbps.switch.11.nic.4",
        "switch.12.nic.0.100Gbps.host.24.nic.0",
        "switch.12.nic.1.100Gbps.host.25.nic.0",
        "switch.13.nic.0.100Gbps.host.26.nic.0",
        "switch.13.nic.1.100Gbps.host.27.nic.0",
        "switch.14.nic.0.100Gbps.host.28.nic.0",
        "switch.14.nic.1.100Gbps.host.29.nic.0",
        "switch.15.nic.0.100Gbps.host.30.nic.0",
        "switch.15.nic.1.100Gbps.host.31.nic.0",
        "switch.12.nic.2.100Gbps.switch.13.nic.2",
        "switch.12.nic.3.100Gbps.switch.14.nic.2",
        "switch.12.nic.4.100Gbps.switch.15.nic.2",
        "switch.13.nic.3.100Gbps.switch.14.nic.3",
        "switch.13.nic.4.100Gbps.switch.15.nic.3",
        "switch.14.nic.4.100Gbps.switch.15.nic.4",
        "switch.16.nic.0.100Gbps.host.32.nic.0",
        "switch.16.nic.1.100Gbps.host.33.nic.0",
        "switch.17.nic.0.100Gbps.host.34.nic.0",
        "switch.17.nic.1.100Gbps.host.35.nic.0",
        "switch.18.nic.0.100Gbps.host.36.nic.0",
        "switch.18.nic.1.100Gbps.host.37.nic.0",
        "switch.19.nic.0.100Gbps.host.38.nic.0",
        "switch.19.nic.1.100Gbps.host.39.nic.0",
        "switch.16.nic.2.100Gbps.switch.17.nic.2",
        "switch.16.nic.3.100Gbps.switch.18.nic.2",
        "switch.16.nic.4.100Gbps.switch.19.nic.2",
        "switch.17.nic.3.100Gbps.switch.18.nic.3",
        "switch.17.nic.4.100Gbps.switch.19.nic.3",
        "switch.18.nic.4.100Gbps.switch.19.nic.4",
        "switch.20.nic.0.100Gbps.host.40.nic.0",
        "switch.20.nic.1.100Gbps.host.41.nic.0",
        "switch.21.nic.0.100Gbps.host.42.nic.0",
        "switch.21.nic.1.100Gbps.host.43.nic.0",
        "switch.22.nic.0.100Gbps.host.44.nic.0",
        "switch.22.nic.1.100Gbps.host.45.nic.0",
        "switch.23.nic.0.100Gbps.host.46.nic.0",
        "switch.23.nic.1.100Gbps.host.47.nic.0",
        "switch.20.nic.2.100Gbps.switch.21.nic.2",
        "switch.20.nic.3.100Gbps.switch.22.nic.2",
        "switch.20.nic.4.100Gbps.switch.23.nic.2",
        "switch.21.nic.3.100Gbps.switch.22.nic.3",
        "switch.21.nic.4.100Gbps.switch.23.nic.3",
        "switch.22.nic.4.100Gbps.switch.23.nic.4",
        "switch.24.nic.0.100Gbps.host.48.nic.0",
        "switch.24.nic.1.100Gbps.host.49.nic.0",
        "switch.25.nic.0.100Gbps.host.50.nic.0",
        "switch.25.nic.1.100Gbps.host.51.nic.0",
        "switch.26.nic.0.100Gbps.host.52.nic.0",
        "switch.26.nic.1.100Gbps.host.53.nic.0",
        "switch.27.nic.0.100Gbps.host.54.nic.0",
        "switch.27.nic.1.100Gbps.host.55.nic.0",
        "switch.24.nic.2.100Gbps.switch.25.nic.2",
        "switch.24.nic.3.100Gbps.switch.26.nic.2",
        "switch.24.nic.4.100Gbps.switch.27.nic.2",
        "switch.25.nic.3.100Gbps.switch.26.nic.3",
        "switch.25.nic.4.100Gbps.switch.27.nic.3",
        "switch.26.nic.4.100Gbps.switch.27.nic.4",
        "switch.28.nic.0.100Gbps.host.56.nic.0",
        "switch.28.nic.1.100Gbps.host.57.nic.0",
        "switch.29.nic.0.100Gbps.host.58.nic.0",
        "switch.29.nic.1.100Gbps.host.59.nic.0",
        "switch.30.nic.0.100Gbps.host.60.nic.0",
        "switch.30.nic.1.100Gbps.host.61.nic.0",
        "switch.31.nic.0.100Gbps.host.62.nic.0",
        "switch.31.nic.1.100Gbps.host.63.nic.0",
        "switch.28.nic.2.100Gbps.switch.29.nic.2",
        "switch.28.nic.3.100Gbps.switch.30.nic.2",
        "switch.28.nic.4.100Gbps.switch.31.nic.2",
        "switch.29.nic.3.100Gbps.switch.30.nic.3",
        "switch.29.nic.4.100Gbps.switch.31.nic.3",
        "switch.30.nic.4.100Gbps.switch.31.nic.4",
        "switch.32.nic.0.100Gbps.host.64.nic.0",
        "switch.32.nic.1.100Gbps.host.65.nic.0",
        "switch.33.nic.0.100Gbps.host.66.nic.0",
        "switch.33.nic.1.100Gbps.host.67.nic.0",
        "switch.34.nic.0.100Gbps.host.68.nic.0",
        "switch.34.nic.1.100Gbps.host.69.nic.0",
        "switch.35.nic.0.100Gbps.host.70.nic.0",
        "switch.35.nic.1.100Gbps.host.71.nic.0",
        "switch.32.nic.2.100Gbps.switch.33.nic.2",
        "switch.32.nic.3.100Gbps.switch.34.nic.2",
        "switch.32.nic.4.100Gbps.switch.35.nic.2",
        "switch.33.nic.3.100Gbps.switch.34.nic.3",
        "switch.33.nic.4.100Gbps.switch.35.nic.3",
        "switch.34.nic.4.100Gbps.switch.35.nic.4",
        "switch.0.nic.5.100Gbps.switch.7.nic.5",
        "switch.0.nic.6.100Gbps.switch.11.nic.5",
        "switch.1.nic.5.100Gbps.switch.14.nic.5",
        "switch.1.nic.6.100Gbps.switch.18.nic.5",
        "switch.2.nic.5.100Gbps.switch.21.nic.5",
        "switch.2.nic.6.100Gbps.switch.25.nic.5",
        "switch.3.nic.5.100Gbps.switch.28.nic.5",
        "switch.3.nic.6.100Gbps.switch.32.nic.5",
        "switch.4.nic.5.100Gbps.switch.11.nic.6",
        "switch.4.nic.6.100Gbps.switch.15.nic.5",
        "switch.5.nic.5.100Gbps.switch.18.nic.6",
        "switch.5.nic.6.100Gbps.switch.22.nic.5",
        "switch.6.nic.5.100Gbps.switch.25.nic.6",
        "switch.6.nic.6.100Gbps.switch.29.nic.5",
        "switch.7.nic.6.100Gbps.switch.32.nic.6",
        "switch.8.nic.5.100Gbps.switch.15.nic.6",
        "switch.8.nic.6.100Gbps.switch.19.nic.5",
        "switch.9.nic.5.100Gbps.switch.22.nic.6",
        "switch.9.nic.6.100Gbps.switch.26.nic.5",
        "switch.10.nic.5.100Gbps.switch.29.nic.6",
        "switch.10.nic.6.100Gbps.switch.33.nic.5",
        "switch.12.nic.5.100Gbps.switch.19.nic.6",
        "switch.12.nic.6.100Gbps.switch.23.nic.5",
        "switch.13.nic.5.100Gbps.switch.26.nic.6",
        "switch.13.nic.6.100Gbps.switch.30.nic.5",
        "switch.14.nic.6.100Gbps.switch.33.nic.6",
        "switch.16.nic.5.100Gbps.switch.23.nic.6",
        "switch.16.nic.6.100Gbps.switch.27.nic.5",
        "switch.17.nic.5.100Gbps.switch.30.nic.6",
        "switch.17.nic.6.100Gbps.switch.34.nic.5",
        "switch.20.nic.5.100Gbps.switch.27.nic.6",
        "switch.20.nic.6.100Gbps.switch.31.nic.5",
        "switch.21.nic.6.100Gbps.switch.34.nic.6",
        "switch.24.nic.5.100Gbps.switch.31.nic.6",
        "switch.24.nic.6.100Gbps.switch.35.nic.5",
        "switch.28.nic.6.100Gbps.switch.35.nic.6"
    ]
}

```

</details>

<br>