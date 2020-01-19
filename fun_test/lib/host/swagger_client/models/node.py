# coding: utf-8

"""
    Fungible Storage Controller Intent API

    REST API for interfacing between the management/orchestration system and Fungible Storage Controller `(FSC)`  # noqa: E501

    OpenAPI spec version: 1.0.0
    Contact: storage@fungible.com
    Generated by: https://github.com/swagger-api/swagger-codegen.git
"""


import pprint
import re  # noqa: F401

import six


class Node(object):
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
        'node_id': 'str',
        'node_name': 'str',
        'node_class': 'str',
        'parent_id': 'str',
        'fault_zones': 'list[str]',
        'mgmt_ip': 'str',
        'mgmt_ports': 'dict(str, str)',
        'state': 'ResourceState',
        'additional_fields': 'AdditionalFields',
        'created_at': 'datetime',
        'modified_at': 'datetime'
    }

    attribute_map = {
        'node_id': 'node_id',
        'node_name': 'node_name',
        'node_class': 'node_class',
        'parent_id': 'parent_id',
        'fault_zones': 'fault_zones',
        'mgmt_ip': 'mgmt_ip',
        'mgmt_ports': 'mgmt_ports',
        'state': 'state',
        'additional_fields': 'additional_fields',
        'created_at': 'created_at',
        'modified_at': 'modified_at'
    }

    def __init__(self, node_id=None, node_name=None, node_class=None, parent_id=None, fault_zones=None, mgmt_ip=None, mgmt_ports=None, state=None, additional_fields=None, created_at=None, modified_at=None):  # noqa: E501
        """Node - a model defined in Swagger"""  # noqa: E501

        self._node_id = None
        self._node_name = None
        self._node_class = None
        self._parent_id = None
        self._fault_zones = None
        self._mgmt_ip = None
        self._mgmt_ports = None
        self._state = None
        self._additional_fields = None
        self._created_at = None
        self._modified_at = None
        self.discriminator = None

        self.node_id = node_id
        self.node_name = node_name
        self.node_class = node_class
        if parent_id is not None:
            self.parent_id = parent_id
        if fault_zones is not None:
            self.fault_zones = fault_zones
        if mgmt_ip is not None:
            self.mgmt_ip = mgmt_ip
        if mgmt_ports is not None:
            self.mgmt_ports = mgmt_ports
        if state is not None:
            self.state = state
        if additional_fields is not None:
            self.additional_fields = additional_fields
        if created_at is not None:
            self.created_at = created_at
        if modified_at is not None:
            self.modified_at = modified_at

    @property
    def node_id(self):
        """Gets the node_id of this Node.  # noqa: E501


        :return: The node_id of this Node.  # noqa: E501
        :rtype: str
        """
        return self._node_id

    @node_id.setter
    def node_id(self, node_id):
        """Sets the node_id of this Node.


        :param node_id: The node_id of this Node.  # noqa: E501
        :type: str
        """
        if node_id is None:
            raise ValueError("Invalid value for `node_id`, must not be `None`")  # noqa: E501

        self._node_id = node_id

    @property
    def node_name(self):
        """Gets the node_name of this Node.  # noqa: E501


        :return: The node_name of this Node.  # noqa: E501
        :rtype: str
        """
        return self._node_name

    @node_name.setter
    def node_name(self, node_name):
        """Sets the node_name of this Node.


        :param node_name: The node_name of this Node.  # noqa: E501
        :type: str
        """
        if node_name is None:
            raise ValueError("Invalid value for `node_name`, must not be `None`")  # noqa: E501

        self._node_name = node_name

    @property
    def node_class(self):
        """Gets the node_class of this Node.  # noqa: E501


        :return: The node_class of this Node.  # noqa: E501
        :rtype: str
        """
        return self._node_class

    @node_class.setter
    def node_class(self, node_class):
        """Sets the node_class of this Node.


        :param node_class: The node_class of this Node.  # noqa: E501
        :type: str
        """
        if node_class is None:
            raise ValueError("Invalid value for `node_class`, must not be `None`")  # noqa: E501

        self._node_class = node_class

    @property
    def parent_id(self):
        """Gets the parent_id of this Node.  # noqa: E501

        id of parent node of this node  # noqa: E501

        :return: The parent_id of this Node.  # noqa: E501
        :rtype: str
        """
        return self._parent_id

    @parent_id.setter
    def parent_id(self, parent_id):
        """Sets the parent_id of this Node.

        id of parent node of this node  # noqa: E501

        :param parent_id: The parent_id of this Node.  # noqa: E501
        :type: str
        """

        self._parent_id = parent_id

    @property
    def fault_zones(self):
        """Gets the fault_zones of this Node.  # noqa: E501


        :return: The fault_zones of this Node.  # noqa: E501
        :rtype: list[str]
        """
        return self._fault_zones

    @fault_zones.setter
    def fault_zones(self, fault_zones):
        """Sets the fault_zones of this Node.


        :param fault_zones: The fault_zones of this Node.  # noqa: E501
        :type: list[str]
        """

        self._fault_zones = fault_zones

    @property
    def mgmt_ip(self):
        """Gets the mgmt_ip of this Node.  # noqa: E501


        :return: The mgmt_ip of this Node.  # noqa: E501
        :rtype: str
        """
        return self._mgmt_ip

    @mgmt_ip.setter
    def mgmt_ip(self, mgmt_ip):
        """Sets the mgmt_ip of this Node.


        :param mgmt_ip: The mgmt_ip of this Node.  # noqa: E501
        :type: str
        """

        self._mgmt_ip = mgmt_ip

    @property
    def mgmt_ports(self):
        """Gets the mgmt_ports of this Node.  # noqa: E501


        :return: The mgmt_ports of this Node.  # noqa: E501
        :rtype: dict(str, str)
        """
        return self._mgmt_ports

    @mgmt_ports.setter
    def mgmt_ports(self, mgmt_ports):
        """Sets the mgmt_ports of this Node.


        :param mgmt_ports: The mgmt_ports of this Node.  # noqa: E501
        :type: dict(str, str)
        """

        self._mgmt_ports = mgmt_ports

    @property
    def state(self):
        """Gets the state of this Node.  # noqa: E501


        :return: The state of this Node.  # noqa: E501
        :rtype: ResourceState
        """
        return self._state

    @state.setter
    def state(self, state):
        """Sets the state of this Node.


        :param state: The state of this Node.  # noqa: E501
        :type: ResourceState
        """

        self._state = state

    @property
    def additional_fields(self):
        """Gets the additional_fields of this Node.  # noqa: E501


        :return: The additional_fields of this Node.  # noqa: E501
        :rtype: AdditionalFields
        """
        return self._additional_fields

    @additional_fields.setter
    def additional_fields(self, additional_fields):
        """Sets the additional_fields of this Node.


        :param additional_fields: The additional_fields of this Node.  # noqa: E501
        :type: AdditionalFields
        """

        self._additional_fields = additional_fields

    @property
    def created_at(self):
        """Gets the created_at of this Node.  # noqa: E501

        set on create  # noqa: E501

        :return: The created_at of this Node.  # noqa: E501
        :rtype: datetime
        """
        return self._created_at

    @created_at.setter
    def created_at(self, created_at):
        """Sets the created_at of this Node.

        set on create  # noqa: E501

        :param created_at: The created_at of this Node.  # noqa: E501
        :type: datetime
        """

        self._created_at = created_at

    @property
    def modified_at(self):
        """Gets the modified_at of this Node.  # noqa: E501

        set when modified  # noqa: E501

        :return: The modified_at of this Node.  # noqa: E501
        :rtype: datetime
        """
        return self._modified_at

    @modified_at.setter
    def modified_at(self, modified_at):
        """Sets the modified_at of this Node.

        set when modified  # noqa: E501

        :param modified_at: The modified_at of this Node.  # noqa: E501
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
        if issubclass(Node, dict):
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
        if not isinstance(other, Node):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
