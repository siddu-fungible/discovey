# coding: utf-8

"""
    Fungible Storage Controller Intent API

    REST API for interfacing between the management/orchestration system and Fungible Storage Controller `(FSC)` `INTERNAL`: The API is for internal controller use only `DEBUG`: The API will not be available in production use   # noqa: E501

    OpenAPI spec version: 1.0.0
    Contact: storage@fungible.com
    Generated by: https://github.com/swagger-api/swagger-codegen.git
"""


import pprint
import re  # noqa: F401

import six


class VolumeInjectFault(object):
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
        'dpu': 'str'
    }

    attribute_map = {
        'uuid': 'uuid',
        'dpu': 'dpu'
    }

    def __init__(self, uuid=None, dpu=None):  # noqa: E501
        """VolumeInjectFault - a model defined in Swagger"""  # noqa: E501

        self._uuid = None
        self._dpu = None
        self.discriminator = None

        if uuid is not None:
            self.uuid = uuid
        if dpu is not None:
            self.dpu = dpu

    @property
    def uuid(self):
        """Gets the uuid of this VolumeInjectFault.  # noqa: E501


        :return: The uuid of this VolumeInjectFault.  # noqa: E501
        :rtype: str
        """
        return self._uuid

    @uuid.setter
    def uuid(self, uuid):
        """Sets the uuid of this VolumeInjectFault.


        :param uuid: The uuid of this VolumeInjectFault.  # noqa: E501
        :type: str
        """

        self._uuid = uuid

    @property
    def dpu(self):
        """Gets the dpu of this VolumeInjectFault.  # noqa: E501


        :return: The dpu of this VolumeInjectFault.  # noqa: E501
        :rtype: str
        """
        return self._dpu

    @dpu.setter
    def dpu(self, dpu):
        """Sets the dpu of this VolumeInjectFault.


        :param dpu: The dpu of this VolumeInjectFault.  # noqa: E501
        :type: str
        """

        self._dpu = dpu

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
        if issubclass(VolumeInjectFault, dict):
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
        if not isinstance(other, VolumeInjectFault):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
