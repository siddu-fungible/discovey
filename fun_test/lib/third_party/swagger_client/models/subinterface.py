# coding: utf-8

"""
    Fungible Controller Intent API

    Intent based REST API for interfacing between the management/orchestration system and Fungible Controller `(FC)` Services `INTERNAL`: The API is for internal controller use only `DEBUG`: The API will not be available in production use   # noqa: E501

    OpenAPI spec version: 1.0.0
    Contact: storage@fungible.com
    Generated by: https://github.com/swagger-api/swagger-codegen.git
"""


import pprint
import re  # noqa: F401

import six


class Subinterface(object):
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
        'index': 'int',
        'openconfig_if_ipipv4': 'SubinterfaceOpenconfigifipipv4',
        'openconfig_if_ipipv6': 'SubinterfaceOpenconfigifipipv6'
    }

    attribute_map = {
        'index': 'index',
        'openconfig_if_ipipv4': 'openconfig-if-ip:ipv4',
        'openconfig_if_ipipv6': 'openconfig-if-ip:ipv6'
    }

    def __init__(self, index=None, openconfig_if_ipipv4=None, openconfig_if_ipipv6=None):  # noqa: E501
        """Subinterface - a model defined in Swagger"""  # noqa: E501

        self._index = None
        self._openconfig_if_ipipv4 = None
        self._openconfig_if_ipipv6 = None
        self.discriminator = None

        self.index = index
        if openconfig_if_ipipv4 is not None:
            self.openconfig_if_ipipv4 = openconfig_if_ipipv4
        if openconfig_if_ipipv6 is not None:
            self.openconfig_if_ipipv6 = openconfig_if_ipipv6

    @property
    def index(self):
        """Gets the index of this Subinterface.  # noqa: E501


        :return: The index of this Subinterface.  # noqa: E501
        :rtype: int
        """
        return self._index

    @index.setter
    def index(self, index):
        """Sets the index of this Subinterface.


        :param index: The index of this Subinterface.  # noqa: E501
        :type: int
        """
        if index is None:
            raise ValueError("Invalid value for `index`, must not be `None`")  # noqa: E501

        self._index = index

    @property
    def openconfig_if_ipipv4(self):
        """Gets the openconfig_if_ipipv4 of this Subinterface.  # noqa: E501


        :return: The openconfig_if_ipipv4 of this Subinterface.  # noqa: E501
        :rtype: SubinterfaceOpenconfigifipipv4
        """
        return self._openconfig_if_ipipv4

    @openconfig_if_ipipv4.setter
    def openconfig_if_ipipv4(self, openconfig_if_ipipv4):
        """Sets the openconfig_if_ipipv4 of this Subinterface.


        :param openconfig_if_ipipv4: The openconfig_if_ipipv4 of this Subinterface.  # noqa: E501
        :type: SubinterfaceOpenconfigifipipv4
        """

        self._openconfig_if_ipipv4 = openconfig_if_ipipv4

    @property
    def openconfig_if_ipipv6(self):
        """Gets the openconfig_if_ipipv6 of this Subinterface.  # noqa: E501


        :return: The openconfig_if_ipipv6 of this Subinterface.  # noqa: E501
        :rtype: SubinterfaceOpenconfigifipipv6
        """
        return self._openconfig_if_ipipv6

    @openconfig_if_ipipv6.setter
    def openconfig_if_ipipv6(self, openconfig_if_ipipv6):
        """Sets the openconfig_if_ipipv6 of this Subinterface.


        :param openconfig_if_ipipv6: The openconfig_if_ipipv6 of this Subinterface.  # noqa: E501
        :type: SubinterfaceOpenconfigifipipv6
        """

        self._openconfig_if_ipipv6 = openconfig_if_ipipv6

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
        if issubclass(Subinterface, dict):
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
        if not isinstance(other, Subinterface):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
