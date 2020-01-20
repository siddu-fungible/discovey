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


class AdditionalFields(object):
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
        'field_type': 'str',
        'field': 'object'
    }

    attribute_map = {
        'field_type': 'field_type',
        'field': 'field'
    }

    def __init__(self, field_type=None, field=None):  # noqa: E501
        """AdditionalFields - a model defined in Swagger"""  # noqa: E501

        self._field_type = None
        self._field = None
        self.discriminator = None

        self.field_type = field_type
        if field is not None:
            self.field = field

    @property
    def field_type(self):
        """Gets the field_type of this AdditionalFields.  # noqa: E501


        :return: The field_type of this AdditionalFields.  # noqa: E501
        :rtype: str
        """
        return self._field_type

    @field_type.setter
    def field_type(self, field_type):
        """Sets the field_type of this AdditionalFields.


        :param field_type: The field_type of this AdditionalFields.  # noqa: E501
        :type: str
        """
        if field_type is None:
            raise ValueError("Invalid value for `field_type`, must not be `None`")  # noqa: E501

        self._field_type = field_type

    @property
    def field(self):
        """Gets the field of this AdditionalFields.  # noqa: E501


        :return: The field of this AdditionalFields.  # noqa: E501
        :rtype: object
        """
        return self._field

    @field.setter
    def field(self, field):
        """Sets the field of this AdditionalFields.


        :param field: The field of this AdditionalFields.  # noqa: E501
        :type: object
        """

        self._field = field

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
        if issubclass(AdditionalFields, dict):
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
        if not isinstance(other, AdditionalFields):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
