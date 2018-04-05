def get_device_template_config():
    return {
        "tagPrefix": "",
        "baseTemplateFile": "EmulatedDevice.xml",
        "modifyList": [
            {
                "operationList": [
                    {
                        "description": "Build the Network Interface Stack",
                        "buildStack":
                        {
                            "deviceTagName": "ttEmulatedDevice",
                            "stack": [
                                {
                                    "useIf": True,
                                    "className": "EthIIIf",
                                    "tagName": "ttEthIIIf",
                                    "isLowestLayer": True
                                },
                                {
                                    "useIf": False,
                                    "className": "VlanIf",
                                    "tagName": "ttVlanIf"
                                },
                                {
                                    "useIf": False,
                                    "className": "VlanIf",
                                    "tagName": "ttInnerVlanIf"
                                },
                                {
                                    "className": "Ipv4If",
                                    "isTopLevel": True,
                                    "isPrimary": True,
                                    "useIf": True,
                                    "tagName": "ttIpv4If"
                                }
                            ]
                        }
                    }
                ]
            },
            {
                "enable": True,
                "description": "Modify the IPv4If",
                "operationList": [
                    {
                        "propertyValue":
                        {
                            "className": "EmulatedDevice",
                            "tagName": "ttEmulatedDevice",
                            "propertyValueList":
                            {
                                "EnablePingResponse": "True"
                            }
                        }
                    },
                    {
                        "stmPropertyModifier":
                        {
                            "className": "EmulatedDevice",
                            "propertyName": "RouterId",
                            "parentTagName": "ttEmulatedDevice",
                            "tagName": "ttEmulatedDevice.RouterId",
                            "propertyValueList":
                            {
                                "Start": "192.0.0.1",
                                "Step": "0.0.1.0"
                            }
                        }
                    },
                    {
                        "propertyValue":
                        {
                            "className": "EmulatedDevice",
                            "tagName": "ttEmulatedDevice",
                            "propertyValueList":
                            {
                                "RouterIdStep": "0.0.0.1"
                            }
                        }
                    },
                    {
                        "stmPropertyModifier":
                        {
                            "className": "Ipv4If",
                            "propertyName": "Gateway",
                            "parentTagName": "ttIpv4If",
                            "tagName": "ttIpv4If.Gateway",
                            "propertyValueList":
                            {
                                "Start": "1.1.1.2",
                                "Step": "0.0.0.0"
                            }
                        }
                    },
                    {
                        "stmPropertyModifier":
                        {
                            "className": "Ipv4If",
                            "propertyName": "Address",
                            "parentTagName": "ttIpv4If",
                            "tagName": "ttIpv4If.Address",
                            "propertyValueList":
                            {
                                "Start": "1.1.1.1",
                                "Step": "0.0.0.0"
                            }
                        }
                    },
                    {
                        "propertyValue":
                        {
                            "className": "Ipv4If",
                            "tagName": "ttIpv4If",
                            "propertyValueList":
                            {
                                "GatewayStep": "0.0.0.0",
                                "AddrStep": "0.0.0.1",
                                "PrefixLength": "24"
                            }
                        }
                    }
                ]
            },
            {
                "enable": True,
                "description": "Modify the EthIIIf",
                "operationList": [
                    {
                        "stmPropertyModifier":
                        {
                            "className": "EthIIIf",
                            "propertyName": "SourceMac",
                            "parentTagName": "ttEthIIIf",
                            "tagName": "ttEthIIIf.SourceMac",
                            "propertyValueList":
                            {
                                "Start": "00:10:95:00:01:01",
                                "Step": "00:00:00:00:01:00"
                            }
                        }
                    },
                    {
                        "propertyValue":
                        {
                            "className": "EthIIIf",
                            "tagName": "ttEthIIIf",
                            "propertyValueList":
                            {
                                "SrcMacStep": "00:00:00:00:00:01"
                            }
                        }
                    }
                ]
            },
            {
                "enable": False,
                "description": "Modify the Outer VlanIf",
                "operationList": [
                    {
                        "stmPropertyModifier":
                        {
                            "className": "VlanIf",
                            "propertyName": "VlanId",
                            "parentTagName": "ttVlanIf",
                            "tagName": "ttVlanIf.VlanId",
                            "propertyValueList":
                            {
                                "Start": "100",
                                "Step": "100"
                            }
                        }
                    },
                    {
                        "propertyValue":
                        {
                            "className": "VlanIf",
                            "tagName": "ttVlanIf",
                            "propertyValueList":
                            {
                                "IdStep": "1"
                            }
                        }
                    }
                ]
            },
            {
                "enable": False,
                "description": "ModifytheInnerVlanIf",
                "operationList": [
                    {
                        "stmPropertyModifier":
                        {
                            "className": "VlanIf",
                            "propertyName": "VlanId",
                            "parentTagName": "ttInnerVlanIf",
                            "tagName": "ttInnerVlanIf.VlanId",
                            "propertyValueList":
                            {
                                "Start": "200",
                                "Step": "100"
                            }
                        }
                    },
                    {
                        "propertyValue":
                        {
                            "className": "VlanIf",
                            "tagName": "ttInnerVlanIf",
                            "propertyValueList":
                            {
                                "IdStep": "1"
                            }
                        }
                    }
                ]
            }
        ]
    }


def get_traffic_mix_config():
    return {
        "load": 10,
        "loadUnits": "PERCENT_LINE_RATE",
        "table": [
            {
                "baseTemplateFile": "Ipv4_Stream.xml",
                "weight": "100 %",
                "postExpandModify": [
                    {
                        "streamBlockExpand":
                        {
                            "endpointMapping":
                            {
                                "srcBindingTagList": [
                                    "West_ttIpv4If"
                                ],
                                "dstBindingTagList": [
                                    "East_ttIpv4If"
                                ],
                                "bidirectional": True
                            }
                        }
                    }
                ]
            }
        ]
    }


def get_traffic_mix_component():
    return {
        "baseTemplateFile": "Ipv4_Stream.xml",
        "weight": "100 %",
        "modifyList": [
            {
                "enable": True,
                "description": "Modify the IPv4If",
                "operationList": [
                    {
                        "propertyValue":
                        {
                            "className": "StreamBlock",
                            "tagName": "ttStreamBlock",
                            "propertyValueList":
                            {
                                "Name": "StreamBlock"
                            }
                        }
                    }
                ]
            }
        ],
        "postExpandModify": [
            {
                "streamBlockExpand":
                {
                    "endpointMapping":
                    {
                        "srcBindingTagList": [],
                        "dstBindingTagList": [],
                        "bidirectional": False
                    }
                }
            }
        ]
    }


def get_init_rt_traffic():
    return {
        "definition":
        {
            "subtitle":
            {
                "text": "Tx/Rx L1 Rate (bps) Over Time"
            },
            "yAxis":
            {
                "minPadding": 0.2,
                "maxPadding": 0.2,
                "title":
                {
                    "text": "L1 Rate (bps)"
                }
            },
            "series": [],
            "title":
            {
                "text": "Traffic Streams"
            },
            "chart":
            {
                "type": "line"
            },
            "tooltip":
            {
                "headerFormat": "<span style=\"font-size: 10px\">{point.key}s</span><br/>"
            },
            "plotOptions":
            {
                "series":
                {
                    "lineWidth": 1
                }
            },
            "xAxis":
            {
                "minPadding": 0.2,
                "gridLineWidth": 1,
                "title":
                {
                    "text": "Time (s)"
                },
                "maxPadding": 0.2
            },
            "legend":
            {
                "enabled": True
            }
        },
        "enable": True,
        "subscribe": [
            {
                "view_attribute_list": [
                    "L1BitRate"
                ],
                "result_parent_tags": [
                ],
                "legend": [
                    "Rx Rate"
                ],
                "config_type": "StreamBlock",
                "result_type": "RxStreamSummaryResults"
            },
            {
                "view_attribute_list": [
                    "L1BitRate"
                ],
                "result_parent_tags": [
                ],
                "legend": [
                    "Tx Rate"
                ],
                "config_type": "StreamBlock",
                "result_type": "TxStreamResults"
            }
        ],
        "type": "chart",
        "source_type": "RESULTS_SUBSCRIBE",
        "result_id": "chart_traffic"
    }


def get_proto_mix_component():
    return {
        "devicesPerBlock": 1,
        "weight": "1",
        "tagPrefix": "",
        "baseTemplateFile": "EmulatedDevice.xml",
        "modifyList": [
            {
                "operationList": [
                    {
                        "description": "Build the Network Interface Stack",
                        "buildStack":
                        {
                            "deviceTagName": "ttEmulatedDevice",
                            "stack": [
                                {
                                    "useIf": True,
                                    "className": "EthIIIf",
                                    "tagName": "ttEthIIIf",
                                    "isLowestLayer": True
                                },
                                {
                                    "useIf": False,
                                    "className": "VlanIf",
                                    "tagName": "ttVlanIf"
                                },
                                {
                                    "useIf": False,
                                    "className": "VlanIf",
                                    "tagName": "ttInnerVlanIf"
                                },
                                {
                                    "className": "Ipv4If",
                                    "isTopLevel": True,
                                    "isPrimary": True,
                                    "useIf": True,
                                    "tagName": "ttIpv4If"
                                }
                            ]
                        }
                    }
                ]
            },
            {
                "enable": True,
                "description": "Modify the IPv4If",
                "operationList": [
                    {
                        "propertyValue":
                        {
                            "className": "EmulatedDevice",
                            "tagName": "ttEmulatedDevice",
                            "propertyValueList":
                            {
                                "EnablePingResponse": "True"
                            }
                        }
                    },
                    {
                        "stmPropertyModifier":
                        {
                            "className": "EmulatedDevice",
                            "propertyName": "RouterId",
                            "parentTagName": "ttEmulatedDevice",
                            "tagName": "ttEmulatedDevice.RouterId",
                            "propertyValueList":
                            {
                                "Start": "192.0.0.1",
                                "Step": "0.0.1.0"
                            }
                        }
                    },
                    {
                        "propertyValue":
                        {
                            "className": "EmulatedDevice",
                            "tagName": "ttEmulatedDevice",
                            "propertyValueList":
                            {
                                "RouterIdStep": "0.0.0.1"
                            }
                        }
                    },
                    {
                        "stmPropertyModifier":
                        {
                            "className": "Ipv4If",
                            "propertyName": "Gateway",
                            "parentTagName": "ttIpv4If",
                            "tagName": "ttIpv4If.Gateway",
                            "propertyValueList":
                            {
                                "Start": "1.1.1.2",
                                "Step": "0.0.0.0"
                            }
                        }
                    },
                    {
                        "stmPropertyModifier":
                        {
                            "className": "Ipv4If",
                            "propertyName": "Address",
                            "parentTagName": "ttIpv4If",
                            "tagName": "ttIpv4If.Address",
                            "propertyValueList":
                            {
                                "Start": "1.1.1.1",
                                "Step": "0.0.0.0"
                            }
                        }
                    },
                    {
                        "propertyValue":
                        {
                            "className": "Ipv4If",
                            "tagName": "ttIpv4If",
                            "propertyValueList":
                            {
                                "GatewayStep": "0.0.0.0",
                                "AddrStep": "0.0.0.1",
                                "PrefixLength": "24"
                            }
                        }
                    }
                ]
            },
            {
                "enable": True,
                "description": "Modify the EthIIIf",
                "operationList": [
                    {
                        "stmPropertyModifier":
                        {
                            "className": "EthIIIf",
                            "propertyName": "SourceMac",
                            "parentTagName": "ttEthIIIf",
                            "tagName": "ttEthIIIf.SourceMac",
                            "propertyValueList":
                            {
                                "Start": "00:10:95:00:01:01",
                                "Step": "00:00:00:00:00:00"
                            }
                        }
                    },
                    {
                        "propertyValue":
                        {
                            "className": "EthIIIf",
                            "tagName": "ttEthIIIf",
                            "propertyValueList":
                            {
                                "SrcMacStep": "00:00:00:00:00:01"
                            }
                        }
                    }
                ]
            },
            {
                "enable": False,
                "description": "Modify the Outer VlanIf",
                "operationList": [
                    {
                        "stmPropertyModifier":
                        {
                            "className": "VlanIf",
                            "propertyName": "VlanId",
                            "parentTagName": "ttVlanIf",
                            "tagName": "ttVlanIf.VlanId",
                            "propertyValueList":
                            {
                                "Start": "100",
                                "Step": "0"
                            }
                        }
                    },
                    {
                        "propertyValue":
                        {
                            "className": "VlanIf",
                            "tagName": "ttVlanIf",
                            "propertyValueList":
                            {
                                "IdStep": "1"
                            }
                        }
                    }
                ]
            },
            {
                "enable": False,
                "description": "ModifytheInnerVlanIf",
                "operationList": [
                    {
                        "stmPropertyModifier":
                        {
                            "className": "VlanIf",
                            "propertyName": "VlanId",
                            "parentTagName": "ttInnerVlanIf",
                            "tagName": "ttInnerVlanIf.VlanId",
                            "propertyValueList":
                            {
                                "Start": "200",
                                "Step": "0"
                            }
                        }
                    },
                    {
                        "propertyValue":
                        {
                            "className": "VlanIf",
                            "tagName": "ttInnerVlanIf",
                            "propertyValueList":
                            {
                                "IdStep": "1"
                            }
                        }
                    }
                ]
            },
            {
                "enable": True,
                "description": "Modify the Device Name",
                "operationList": [
                    {
                        "propertyValue":
                        {
                            "className": "EmulatedDevice",
                            "tagName": "ttEmulatedDevice",
                            "propertyValueList":
                            {
                                "Name": "Device"
                            }
                        }
                    }
                ]
            }
        ]
    }
