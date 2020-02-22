# coding: utf-8

"""
    Fungible Controller Intent API

    Intent based REST API for interfacing between the management/orchestration system and Fungible Controller `(FC)` Services `INTERNAL`: The API is for internal controller use only `DEBUG`: The API will not be available in production use   # noqa: E501

    OpenAPI spec version: 0.1.1
    Contact: storage@fungible.com
    Generated by: https://github.com/swagger-api/swagger-codegen.git
"""


import pprint
import re  # noqa: F401

import six


class Dpu(object):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """

    """
    Attributes:
      swagger_types (dict): The key is attribute name
                            and the value is attribute type.
      attribute_map (dict): The key is attribute name
                            and the value is json key in definition.
    """
    swagger_types = {
        'uuid': 'str',
        'name': 'str',
        'node_class': 'str',
        'mgmt_ip': 'str',
        'network_agent': 'str',
        'dataplane_ip': 'str',
        'fpg_num': 'int',
        'storage_agent': 'str',
        'drives': 'list[Drive]',
        'fault_zones': 'list[str]',
        'capacity': 'int',
        'state': 'ResourceState',
        'available': 'bool',
        'dp_ip_setup': 'DpIpSetup',
        'additional_fields': 'AdditionalFields',
        'created_at': 'datetime',
        'modified_at': 'datetime'
    }

    attribute_map = {
        'uuid': 'uuid',
        'name': 'name',
        'node_class': 'node_class',
        'mgmt_ip': 'mgmt_ip',
        'network_agent': 'network_agent',
        'dataplane_ip': 'dataplane_ip',
        'fpg_num': 'fpg_num',
        'storage_agent': 'storage_agent',
        'drives': 'drives',
        'fault_zones': 'fault_zones',
        'capacity': 'capacity',
        'state': 'state',
        'available': 'available',
        'dp_ip_setup': 'dp_ip_setup',
        'additional_fields': 'additional_fields',
        'created_at': 'created_at',
        'modified_at': 'modified_at'
    }

    def __init__(self, uuid=None, name=None, node_class=None, mgmt_ip=None, network_agent=None, dataplane_ip=None, fpg_num=None, storage_agent=None, drives=None, fault_zones=None, capacity=None, state=None, available=None, dp_ip_setup=None, additional_fields=None, created_at=None, modified_at=None):  # noqa: E501
        """Dpu - a model defined in Swagger"""  # noqa: E501

        self._uuid = None
        self._name = None
        self._node_class = None
        self._mgmt_ip = None
        self._network_agent = None
        self._dataplane_ip = None
        self._fpg_num = None
        self._storage_agent = None
        self._drives = None
        self._fault_zones = None
        self._capacity = None
        self._state = None
        self._available = None
        self._dp_ip_setup = None
        self._additional_fields = None
        self._created_at = None
        self._modified_at = None
        self.discriminator = None

        self.uuid = uuid
        self.name = name
        if node_class is not None:
            self.node_class = node_class
        if mgmt_ip is not None:
            self.mgmt_ip = mgmt_ip
        if network_agent is not None:
            self.network_agent = network_agent
        if dataplane_ip is not None:
            self.dataplane_ip = dataplane_ip
        if fpg_num is not None:
            self.fpg_num = fpg_num
        if storage_agent is not None:
            self.storage_agent = storage_agent
        if drives is not None:
            self.drives = drives
        if fault_zones is not None:
            self.fault_zones = fault_zones
        if capacity is not None:
            self.capacity = capacity
        if state is not None:
            self.state = state
        if available is not None:
            self.available = available
        if dp_ip_setup is not None:
            self.dp_ip_setup = dp_ip_setup
        if additional_fields is not None:
            self.additional_fields = additional_fields
        if created_at is not None:
            self.created_at = created_at
        if modified_at is not None:
            self.modified_at = modified_at

    @property
    def uuid(self):
        """Gets the uuid of this Dpu.  # noqa: E501

        unique id of dpu  # noqa: E501

        :return: The uuid of this Dpu.  # noqa: E501
        :rtype: str
        """
        return self._uuid

    @uuid.setter
    def uuid(self, uuid):
        """Sets the uuid of this Dpu.

        unique id of dpu  # noqa: E501

        :param uuid: The uuid of this Dpu.  # noqa: E501
        :type: str
        """
        if uuid is None:
            raise ValueError("Invalid value for `uuid`, must not be `None`")  # noqa: E501

        self._uuid = uuid

    @property
    def name(self):
        """Gets the name of this Dpu.  # noqa: E501

        Descriptive name of dpu  # noqa: E501

        :return: The name of this Dpu.  # noqa: E501
        :rtype: str
        """
        return self._name

    @name.setter
    def name(self, name):
        """Sets the name of this Dpu.

        Descriptive name of dpu  # noqa: E501

        :param name: The name of this Dpu.  # noqa: E501
        :type: str
        """
        if name is None:
            raise ValueError("Invalid value for `name`, must not be `None`")  # noqa: E501

        self._name = name

    @property
    def node_class(self):
        """Gets the node_class of this Dpu.  # noqa: E501


        :return: The node_class of this Dpu.  # noqa: E501
        :rtype: str
        """
        return self._node_class

    @node_class.setter
    def node_class(self, node_class):
        """Sets the node_class of this Dpu.


        :param node_class: The node_class of this Dpu.  # noqa: E501
        :type: str
        """

        self._node_class = node_class

    @property
    def mgmt_ip(self):
        """Gets the mgmt_ip of this Dpu.  # noqa: E501


        :return: The mgmt_ip of this Dpu.  # noqa: E501
        :rtype: str
        """
        return self._mgmt_ip

    @mgmt_ip.setter
    def mgmt_ip(self, mgmt_ip):
        """Sets the mgmt_ip of this Dpu.


        :param mgmt_ip: The mgmt_ip of this Dpu.  # noqa: E501
        :type: str
        """

        self._mgmt_ip = mgmt_ip

    @property
    def network_agent(self):
        """Gets the network_agent of this Dpu.  # noqa: E501


        :return: The network_agent of this Dpu.  # noqa: E501
        :rtype: str
        """
        return self._network_agent

    @network_agent.setter
    def network_agent(self, network_agent):
        """Sets the network_agent of this Dpu.


        :param network_agent: The network_agent of this Dpu.  # noqa: E501
        :type: str
        """

        self._network_agent = network_agent

    @property
    def dataplane_ip(self):
        """Gets the dataplane_ip of this Dpu.  # noqa: E501


        :return: The dataplane_ip of this Dpu.  # noqa: E501
        :rtype: str
        """
        return self._dataplane_ip

    @dataplane_ip.setter
    def dataplane_ip(self, dataplane_ip):
        """Sets the dataplane_ip of this Dpu.


        :param dataplane_ip: The dataplane_ip of this Dpu.  # noqa: E501
        :type: str
        """

        self._dataplane_ip = dataplane_ip

    @property
    def fpg_num(self):
        """Gets the fpg_num of this Dpu.  # noqa: E501


        :return: The fpg_num of this Dpu.  # noqa: E501
        :rtype: int
        """
        return self._fpg_num

    @fpg_num.setter
    def fpg_num(self, fpg_num):
        """Sets the fpg_num of this Dpu.


        :param fpg_num: The fpg_num of this Dpu.  # noqa: E501
        :type: int
        """

        self._fpg_num = fpg_num

    @property
    def storage_agent(self):
        """Gets the storage_agent of this Dpu.  # noqa: E501


        :return: The storage_agent of this Dpu.  # noqa: E501
        :rtype: str
        """
        return self._storage_agent

    @storage_agent.setter
    def storage_agent(self, storage_agent):
        """Sets the storage_agent of this Dpu.


        :param storage_agent: The storage_agent of this Dpu.  # noqa: E501
        :type: str
        """

        self._storage_agent = storage_agent

    @property
    def drives(self):
        """Gets the drives of this Dpu.  # noqa: E501


        :return: The drives of this Dpu.  # noqa: E501
        :rtype: list[Drive]
        """
        return self._drives

    @drives.setter
    def drives(self, drives):
        """Sets the drives of this Dpu.


        :param drives: The drives of this Dpu.  # noqa: E501
        :type: list[Drive]
        """

        self._drives = drives

    @property
    def fault_zones(self):
        """Gets the fault_zones of this Dpu.  # noqa: E501


        :return: The fault_zones of this Dpu.  # noqa: E501
        :rtype: list[str]
        """
        return self._fault_zones

    @fault_zones.setter
    def fault_zones(self, fault_zones):
        """Sets the fault_zones of this Dpu.


        :param fault_zones: The fault_zones of this Dpu.  # noqa: E501
        :type: list[str]
        """

        self._fault_zones = fault_zones

    @property
    def capacity(self):
        """Gets the capacity of this Dpu.  # noqa: E501


        :return: The capacity of this Dpu.  # noqa: E501
        :rtype: int
        """
        return self._capacity

    @capacity.setter
    def capacity(self, capacity):
        """Sets the capacity of this Dpu.


        :param capacity: The capacity of this Dpu.  # noqa: E501
        :type: int
        """

        self._capacity = capacity

    @property
    def state(self):
        """Gets the state of this Dpu.  # noqa: E501


        :return: The state of this Dpu.  # noqa: E501
        :rtype: ResourceState
        """
        return self._state

    @state.setter
    def state(self, state):
        """Sets the state of this Dpu.


        :param state: The state of this Dpu.  # noqa: E501
        :type: ResourceState
        """

        self._state = state

    @property
    def available(self):
        """Gets the available of this Dpu.  # noqa: E501


        :return: The available of this Dpu.  # noqa: E501
        :rtype: bool
        """
        return self._available

    @available.setter
    def available(self, available):
        """Sets the available of this Dpu.


        :param available: The available of this Dpu.  # noqa: E501
        :type: bool
        """

        self._available = available

    @property
    def dp_ip_setup(self):
        """Gets the dp_ip_setup of this Dpu.  # noqa: E501


        :return: The dp_ip_setup of this Dpu.  # noqa: E501
        :rtype: DpIpSetup
        """
        return self._dp_ip_setup

    @dp_ip_setup.setter
    def dp_ip_setup(self, dp_ip_setup):
        """Sets the dp_ip_setup of this Dpu.


        :param dp_ip_setup: The dp_ip_setup of this Dpu.  # noqa: E501
        :type: DpIpSetup
        """

        self._dp_ip_setup = dp_ip_setup

    @property
    def additional_fields(self):
        """Gets the additional_fields of this Dpu.  # noqa: E501


        :return: The additional_fields of this Dpu.  # noqa: E501
        :rtype: AdditionalFields
        """
        return self._additional_fields

    @additional_fields.setter
    def additional_fields(self, additional_fields):
        """Sets the additional_fields of this Dpu.


        :param additional_fields: The additional_fields of this Dpu.  # noqa: E501
        :type: AdditionalFields
        """

        self._additional_fields = additional_fields

    @property
    def created_at(self):
        """Gets the created_at of this Dpu.  # noqa: E501

        set on create  # noqa: E501

        :return: The created_at of this Dpu.  # noqa: E501
        :rtype: datetime
        """
        return self._created_at

    @created_at.setter
    def created_at(self, created_at):
        """Sets the created_at of this Dpu.

        set on create  # noqa: E501

        :param created_at: The created_at of this Dpu.  # noqa: E501
        :type: datetime
        """

        self._created_at = created_at

    @property
    def modified_at(self):
        """Gets the modified_at of this Dpu.  # noqa: E501

        set when modified  # noqa: E501

        :return: The modified_at of this Dpu.  # noqa: E501
        :rtype: datetime
        """
        return self._modified_at

    @modified_at.setter
    def modified_at(self, modified_at):
        """Sets the modified_at of this Dpu.

        set when modified  # noqa: E501

        :param modified_at: The modified_at of this Dpu.  # noqa: E501
        :type: datetime
        """

        self._modified_at = modified_at

    def to_dict(self):
        """Returns the model properties as a dict"""
        result = {}

        for attr, _ in six.iteritems(self.swagger_types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(map(
                    lambda x: x.to_dict() if hasattr(x, "to_dict") else x,
                    value
                ))
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(map(
                    lambda item: (item[0], item[1].to_dict())
                    if hasattr(item[1], "to_dict") else item,
                    value.items()
                ))
            else:
                result[attr] = value
        if issubclass(Dpu, dict):
            for key, value in self.items():
                result[key] = value

        return result

    def to_str(self):
        """Returns the string representation of the model"""
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        """For `print` and `pprint`"""
        return self.to_str()

    def __eq__(self, other):
        """Returns true if both objects are equal"""
        if not isinstance(other, Dpu):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
