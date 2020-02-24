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


class ResponseDataWithSinglePool(object):
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
        'status': 'bool',
        'message': 'str',
        'error_message': 'str',
        'warning': 'str',
        'data': 'Pool'
    }

    attribute_map = {
        'status': 'status',
        'message': 'message',
        'error_message': 'error_message',
        'warning': 'warning',
        'data': 'data'
    }

    def __init__(self, status=None, message=None, error_message=None, warning=None, data=None):  # noqa: E501
        """ResponseDataWithSinglePool - a model defined in Swagger"""  # noqa: E501

        self._status = None
        self._message = None
        self._error_message = None
        self._warning = None
        self._data = None
        self.discriminator = None

        self.status = status
        if message is not None:
            self.message = message
        if error_message is not None:
            self.error_message = error_message
        if warning is not None:
            self.warning = warning
        self.data = data

    @property
    def status(self):
        """Gets the status of this ResponseDataWithSinglePool.  # noqa: E501


        :return: The status of this ResponseDataWithSinglePool.  # noqa: E501
        :rtype: bool
        """
        return self._status

    @status.setter
    def status(self, status):
        """Sets the status of this ResponseDataWithSinglePool.


        :param status: The status of this ResponseDataWithSinglePool.  # noqa: E501
        :type: bool
        """
        if status is None:
            raise ValueError("Invalid value for `status`, must not be `None`")  # noqa: E501

        self._status = status

    @property
    def message(self):
        """Gets the message of this ResponseDataWithSinglePool.  # noqa: E501


        :return: The message of this ResponseDataWithSinglePool.  # noqa: E501
        :rtype: str
        """
        return self._message

    @message.setter
    def message(self, message):
        """Sets the message of this ResponseDataWithSinglePool.


        :param message: The message of this ResponseDataWithSinglePool.  # noqa: E501
        :type: str
        """

        self._message = message

    @property
    def error_message(self):
        """Gets the error_message of this ResponseDataWithSinglePool.  # noqa: E501


        :return: The error_message of this ResponseDataWithSinglePool.  # noqa: E501
        :rtype: str
        """
        return self._error_message

    @error_message.setter
    def error_message(self, error_message):
        """Sets the error_message of this ResponseDataWithSinglePool.


        :param error_message: The error_message of this ResponseDataWithSinglePool.  # noqa: E501
        :type: str
        """

        self._error_message = error_message

    @property
    def warning(self):
        """Gets the warning of this ResponseDataWithSinglePool.  # noqa: E501


        :return: The warning of this ResponseDataWithSinglePool.  # noqa: E501
        :rtype: str
        """
        return self._warning

    @warning.setter
    def warning(self, warning):
        """Sets the warning of this ResponseDataWithSinglePool.


        :param warning: The warning of this ResponseDataWithSinglePool.  # noqa: E501
        :type: str
        """

        self._warning = warning

    @property
    def data(self):
        """Gets the data of this ResponseDataWithSinglePool.  # noqa: E501


        :return: The data of this ResponseDataWithSinglePool.  # noqa: E501
        :rtype: Pool
        """
        return self._data

    @data.setter
    def data(self, data):
        """Sets the data of this ResponseDataWithSinglePool.


        :param data: The data of this ResponseDataWithSinglePool.  # noqa: E501
        :type: Pool
        """
        if data is None:
            raise ValueError("Invalid value for `data`, must not be `None`")  # noqa: E501

        self._data = data

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
        if issubclass(ResponseDataWithSinglePool, dict):
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
        if not isinstance(other, ResponseDataWithSinglePool):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
