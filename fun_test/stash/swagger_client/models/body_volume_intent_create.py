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


class BodyVolumeIntentCreate(object):
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
        'vol_type': 'VolumeTypes',
        'capacity': 'int',
        'compression_effort': 'int',
        'data_protection': 'DataProtection',
        'encrypt': 'bool',
        'allow_expansion': 'bool',
        'stripe_count': 'int',
        'crc_enabled': 'bool',
        'is_clone': 'bool',
        'clone_source_volume_uuid': 'str',
        'additional_fields': 'AdditionalFields'
    }

    attribute_map = {
        'name': 'name',
        'vol_type': 'vol_type',
        'capacity': 'capacity',
        'compression_effort': 'compression_effort',
        'data_protection': 'data_protection',
        'encrypt': 'encrypt',
        'allow_expansion': 'allow_expansion',
        'stripe_count': 'stripe_count',
        'crc_enabled': 'crc_enabled',
        'is_clone': 'is_clone',
        'clone_source_volume_uuid': 'clone_source_volume_uuid',
        'additional_fields': 'additional_fields'
    }

    def __init__(self, name=None, vol_type=None, capacity=None, compression_effort=None, data_protection=None, encrypt=None, allow_expansion=None, stripe_count=None, crc_enabled=None, is_clone=None, clone_source_volume_uuid=None, additional_fields=None):  # noqa: E501
        """BodyVolumeIntentCreate - a model defined in Swagger"""  # noqa: E501

        self._name = None
        self._vol_type = None
        self._capacity = None
        self._compression_effort = None
        self._data_protection = None
        self._encrypt = None
        self._allow_expansion = None
        self._stripe_count = None
        self._crc_enabled = None
        self._is_clone = None
        self._clone_source_volume_uuid = None
        self._additional_fields = None
        self.discriminator = None

        self.name = name
        self.vol_type = vol_type
        self.capacity = capacity
        if compression_effort is not None:
            self.compression_effort = compression_effort
        self.data_protection = data_protection
        if encrypt is not None:
            self.encrypt = encrypt
        if allow_expansion is not None:
            self.allow_expansion = allow_expansion
        if stripe_count is not None:
            self.stripe_count = stripe_count
        if crc_enabled is not None:
            self.crc_enabled = crc_enabled
        if is_clone is not None:
            self.is_clone = is_clone
        if clone_source_volume_uuid is not None:
            self.clone_source_volume_uuid = clone_source_volume_uuid
        if additional_fields is not None:
            self.additional_fields = additional_fields

    @property
    def name(self):
        """Gets the name of this BodyVolumeIntentCreate.  # noqa: E501


        :return: The name of this BodyVolumeIntentCreate.  # noqa: E501
        :rtype: str
        """
        return self._name

    @name.setter
    def name(self, name):
        """Sets the name of this BodyVolumeIntentCreate.


        :param name: The name of this BodyVolumeIntentCreate.  # noqa: E501
        :type: str
        """
        if name is None:
            raise ValueError("Invalid value for `name`, must not be `None`")  # noqa: E501

        self._name = name

    @property
    def vol_type(self):
        """Gets the vol_type of this BodyVolumeIntentCreate.  # noqa: E501


        :return: The vol_type of this BodyVolumeIntentCreate.  # noqa: E501
        :rtype: VolumeTypes
        """
        return self._vol_type

    @vol_type.setter
    def vol_type(self, vol_type):
        """Sets the vol_type of this BodyVolumeIntentCreate.


        :param vol_type: The vol_type of this BodyVolumeIntentCreate.  # noqa: E501
        :type: VolumeTypes
        """
        if vol_type is None:
            raise ValueError("Invalid value for `vol_type`, must not be `None`")  # noqa: E501

        self._vol_type = vol_type

    @property
    def capacity(self):
        """Gets the capacity of this BodyVolumeIntentCreate.  # noqa: E501


        :return: The capacity of this BodyVolumeIntentCreate.  # noqa: E501
        :rtype: int
        """
        return self._capacity

    @capacity.setter
    def capacity(self, capacity):
        """Sets the capacity of this BodyVolumeIntentCreate.


        :param capacity: The capacity of this BodyVolumeIntentCreate.  # noqa: E501
        :type: int
        """
        if capacity is None:
            raise ValueError("Invalid value for `capacity`, must not be `None`")  # noqa: E501

        self._capacity = capacity

    @property
    def compression_effort(self):
        """Gets the compression_effort of this BodyVolumeIntentCreate.  # noqa: E501


        :return: The compression_effort of this BodyVolumeIntentCreate.  # noqa: E501
        :rtype: int
        """
        return self._compression_effort

    @compression_effort.setter
    def compression_effort(self, compression_effort):
        """Sets the compression_effort of this BodyVolumeIntentCreate.


        :param compression_effort: The compression_effort of this BodyVolumeIntentCreate.  # noqa: E501
        :type: int
        """

        self._compression_effort = compression_effort

    @property
    def data_protection(self):
        """Gets the data_protection of this BodyVolumeIntentCreate.  # noqa: E501


        :return: The data_protection of this BodyVolumeIntentCreate.  # noqa: E501
        :rtype: DataProtection
        """
        return self._data_protection

    @data_protection.setter
    def data_protection(self, data_protection):
        """Sets the data_protection of this BodyVolumeIntentCreate.


        :param data_protection: The data_protection of this BodyVolumeIntentCreate.  # noqa: E501
        :type: DataProtection
        """
        if data_protection is None:
            raise ValueError("Invalid value for `data_protection`, must not be `None`")  # noqa: E501

        self._data_protection = data_protection

    @property
    def encrypt(self):
        """Gets the encrypt of this BodyVolumeIntentCreate.  # noqa: E501


        :return: The encrypt of this BodyVolumeIntentCreate.  # noqa: E501
        :rtype: bool
        """
        return self._encrypt

    @encrypt.setter
    def encrypt(self, encrypt):
        """Sets the encrypt of this BodyVolumeIntentCreate.


        :param encrypt: The encrypt of this BodyVolumeIntentCreate.  # noqa: E501
        :type: bool
        """

        self._encrypt = encrypt

    @property
    def allow_expansion(self):
        """Gets the allow_expansion of this BodyVolumeIntentCreate.  # noqa: E501


        :return: The allow_expansion of this BodyVolumeIntentCreate.  # noqa: E501
        :rtype: bool
        """
        return self._allow_expansion

    @allow_expansion.setter
    def allow_expansion(self, allow_expansion):
        """Sets the allow_expansion of this BodyVolumeIntentCreate.


        :param allow_expansion: The allow_expansion of this BodyVolumeIntentCreate.  # noqa: E501
        :type: bool
        """

        self._allow_expansion = allow_expansion

    @property
    def stripe_count(self):
        """Gets the stripe_count of this BodyVolumeIntentCreate.  # noqa: E501


        :return: The stripe_count of this BodyVolumeIntentCreate.  # noqa: E501
        :rtype: int
        """
        return self._stripe_count

    @stripe_count.setter
    def stripe_count(self, stripe_count):
        """Sets the stripe_count of this BodyVolumeIntentCreate.


        :param stripe_count: The stripe_count of this BodyVolumeIntentCreate.  # noqa: E501
        :type: int
        """

        self._stripe_count = stripe_count

    @property
    def crc_enabled(self):
        """Gets the crc_enabled of this BodyVolumeIntentCreate.  # noqa: E501


        :return: The crc_enabled of this BodyVolumeIntentCreate.  # noqa: E501
        :rtype: bool
        """
        return self._crc_enabled

    @crc_enabled.setter
    def crc_enabled(self, crc_enabled):
        """Sets the crc_enabled of this BodyVolumeIntentCreate.


        :param crc_enabled: The crc_enabled of this BodyVolumeIntentCreate.  # noqa: E501
        :type: bool
        """

        self._crc_enabled = crc_enabled

    @property
    def is_clone(self):
        """Gets the is_clone of this BodyVolumeIntentCreate.  # noqa: E501


        :return: The is_clone of this BodyVolumeIntentCreate.  # noqa: E501
        :rtype: bool
        """
        return self._is_clone

    @is_clone.setter
    def is_clone(self, is_clone):
        """Sets the is_clone of this BodyVolumeIntentCreate.


        :param is_clone: The is_clone of this BodyVolumeIntentCreate.  # noqa: E501
        :type: bool
        """

        self._is_clone = is_clone

    @property
    def clone_source_volume_uuid(self):
        """Gets the clone_source_volume_uuid of this BodyVolumeIntentCreate.  # noqa: E501


        :return: The clone_source_volume_uuid of this BodyVolumeIntentCreate.  # noqa: E501
        :rtype: str
        """
        return self._clone_source_volume_uuid

    @clone_source_volume_uuid.setter
    def clone_source_volume_uuid(self, clone_source_volume_uuid):
        """Sets the clone_source_volume_uuid of this BodyVolumeIntentCreate.


        :param clone_source_volume_uuid: The clone_source_volume_uuid of this BodyVolumeIntentCreate.  # noqa: E501
        :type: str
        """

        self._clone_source_volume_uuid = clone_source_volume_uuid

    @property
    def additional_fields(self):
        """Gets the additional_fields of this BodyVolumeIntentCreate.  # noqa: E501


        :return: The additional_fields of this BodyVolumeIntentCreate.  # noqa: E501
        :rtype: AdditionalFields
        """
        return self._additional_fields

    @additional_fields.setter
    def additional_fields(self, additional_fields):
        """Sets the additional_fields of this BodyVolumeIntentCreate.


        :param additional_fields: The additional_fields of this BodyVolumeIntentCreate.  # noqa: E501
        :type: AdditionalFields
        """

        self._additional_fields = additional_fields

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
        if issubclass(BodyVolumeIntentCreate, dict):
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
        if not isinstance(other, BodyVolumeIntentCreate):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
