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


class Pool(object):
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
        'name': 'str',
        'uuid': 'str',
        'dpus': 'list[str]',
        'capacity': 'int',
        'volumes': 'list[str]',
        'additional_fields': 'AdditionalFields',
        'created_at': 'datetime',
        'modified_at': 'datetime'
    }

    attribute_map = {
        'name': 'name',
        'uuid': 'uuid',
        'dpus': 'dpus',
        'capacity': 'capacity',
        'volumes': 'volumes',
        'additional_fields': 'additional_fields',
        'created_at': 'created_at',
        'modified_at': 'modified_at'
    }

    def __init__(self, name=None, uuid=None, dpus=None, capacity=None, volumes=None, additional_fields=None, created_at=None, modified_at=None):  # noqa: E501
        """Pool - a model defined in Swagger"""  # noqa: E501

        self._name = None
        self._uuid = None
        self._dpus = None
        self._capacity = None
        self._volumes = None
        self._additional_fields = None
        self._created_at = None
        self._modified_at = None
        self.discriminator = None

        self.name = name
        self.uuid = uuid
        self.dpus = dpus
        self.capacity = capacity
        self.volumes = volumes
        if additional_fields is not None:
            self.additional_fields = additional_fields
        if created_at is not None:
            self.created_at = created_at
        if modified_at is not None:
            self.modified_at = modified_at

    @property
    def name(self):
        """Gets the name of this Pool.  # noqa: E501

        Name of storage pool  # noqa: E501

        :return: The name of this Pool.  # noqa: E501
        :rtype: str
        """
        return self._name

    @name.setter
    def name(self, name):
        """Sets the name of this Pool.

        Name of storage pool  # noqa: E501

        :param name: The name of this Pool.  # noqa: E501
        :type: str
        """
        if name is None:
            raise ValueError("Invalid value for `name`, must not be `None`")  # noqa: E501

        self._name = name

    @property
    def uuid(self):
        """Gets the uuid of this Pool.  # noqa: E501

        assigned by FC  # noqa: E501

        :return: The uuid of this Pool.  # noqa: E501
        :rtype: str
        """
        return self._uuid

    @uuid.setter
    def uuid(self, uuid):
        """Sets the uuid of this Pool.

        assigned by FC  # noqa: E501

        :param uuid: The uuid of this Pool.  # noqa: E501
        :type: str
        """
        if uuid is None:
            raise ValueError("Invalid value for `uuid`, must not be `None`")  # noqa: E501

        self._uuid = uuid

    @property
    def dpus(self):
        """Gets the dpus of this Pool.  # noqa: E501

        The dpus used by this pool  # noqa: E501

        :return: The dpus of this Pool.  # noqa: E501
        :rtype: list[str]
        """
        return self._dpus

    @dpus.setter
    def dpus(self, dpus):
        """Sets the dpus of this Pool.

        The dpus used by this pool  # noqa: E501

        :param dpus: The dpus of this Pool.  # noqa: E501
        :type: list[str]
        """
        if dpus is None:
            raise ValueError("Invalid value for `dpus`, must not be `None`")  # noqa: E501

        self._dpus = dpus

    @property
    def capacity(self):
        """Gets the capacity of this Pool.  # noqa: E501


        :return: The capacity of this Pool.  # noqa: E501
        :rtype: int
        """
        return self._capacity

    @capacity.setter
    def capacity(self, capacity):
        """Sets the capacity of this Pool.


        :param capacity: The capacity of this Pool.  # noqa: E501
        :type: int
        """
        if capacity is None:
            raise ValueError("Invalid value for `capacity`, must not be `None`")  # noqa: E501

        self._capacity = capacity

    @property
    def volumes(self):
        """Gets the volumes of this Pool.  # noqa: E501

        List of uuids of user created volumes in the pool  # noqa: E501

        :return: The volumes of this Pool.  # noqa: E501
        :rtype: list[str]
        """
        return self._volumes

    @volumes.setter
    def volumes(self, volumes):
        """Sets the volumes of this Pool.

        List of uuids of user created volumes in the pool  # noqa: E501

        :param volumes: The volumes of this Pool.  # noqa: E501
        :type: list[str]
        """
        if volumes is None:
            raise ValueError("Invalid value for `volumes`, must not be `None`")  # noqa: E501

        self._volumes = volumes

    @property
    def additional_fields(self):
        """Gets the additional_fields of this Pool.  # noqa: E501


        :return: The additional_fields of this Pool.  # noqa: E501
        :rtype: AdditionalFields
        """
        return self._additional_fields

    @additional_fields.setter
    def additional_fields(self, additional_fields):
        """Sets the additional_fields of this Pool.


        :param additional_fields: The additional_fields of this Pool.  # noqa: E501
        :type: AdditionalFields
        """

        self._additional_fields = additional_fields

    @property
    def created_at(self):
        """Gets the created_at of this Pool.  # noqa: E501

        set on create  # noqa: E501

        :return: The created_at of this Pool.  # noqa: E501
        :rtype: datetime
        """
        return self._created_at

    @created_at.setter
    def created_at(self, created_at):
        """Sets the created_at of this Pool.

        set on create  # noqa: E501

        :param created_at: The created_at of this Pool.  # noqa: E501
        :type: datetime
        """

        self._created_at = created_at

    @property
    def modified_at(self):
        """Gets the modified_at of this Pool.  # noqa: E501

        set when modified  # noqa: E501

        :return: The modified_at of this Pool.  # noqa: E501
        :rtype: datetime
        """
        return self._modified_at

    @modified_at.setter
    def modified_at(self, modified_at):
        """Sets the modified_at of this Pool.

        set when modified  # noqa: E501

        :param modified_at: The modified_at of this Pool.  # noqa: E501
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
        if issubclass(Pool, dict):
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
        if not isinstance(other, Pool):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
