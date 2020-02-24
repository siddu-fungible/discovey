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


class AddressIpv6State(object):
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
        'ip': 'str',
        'prefix_length': 'int'
    }

    attribute_map = {
        'ip': 'ip',
        'prefix_length': 'prefix-length'
    }

    def __init__(self, ip=None, prefix_length=None):  # noqa: E501
        """AddressIpv6State - a model defined in Swagger"""  # noqa: E501

        self._ip = None
        self._prefix_length = None
        self.discriminator = None

        if ip is not None:
            self.ip = ip
        if prefix_length is not None:
            self.prefix_length = prefix_length

    @property
    def ip(self):
        """Gets the ip of this AddressIpv6State.  # noqa: E501


        :return: The ip of this AddressIpv6State.  # noqa: E501
        :rtype: str
        """
        return self._ip

    @ip.setter
    def ip(self, ip):
        """Sets the ip of this AddressIpv6State.


        :param ip: The ip of this AddressIpv6State.  # noqa: E501
        :type: str
        """

        self._ip = ip

    @property
    def prefix_length(self):
        """Gets the prefix_length of this AddressIpv6State.  # noqa: E501


        :return: The prefix_length of this AddressIpv6State.  # noqa: E501
        :rtype: int
        """
        return self._prefix_length

    @prefix_length.setter
    def prefix_length(self, prefix_length):
        """Sets the prefix_length of this AddressIpv6State.


        :param prefix_length: The prefix_length of this AddressIpv6State.  # noqa: E501
        :type: int
        """

        self._prefix_length = prefix_length

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
        if issubclass(AddressIpv6State, dict):
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
        if not isinstance(other, AddressIpv6State):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
