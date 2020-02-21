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


class VolumeStats(object):
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
        'physical_usage': 'int',
        'physical_writes': 'int',
        'read_avg_latency_nsec': 'int',
        'write_avg_latency_nsec': 'int',
        'drive_uuid': 'str',
        'write_min_latency_nsec': 'int'
    }

    attribute_map = {
        'physical_usage': 'physical_usage',
        'physical_writes': 'physical_writes',
        'read_avg_latency_nsec': 'read_avg_latency_nsec',
        'write_avg_latency_nsec': 'write_avg_latency_nsec',
        'drive_uuid': 'drive_uuid',
        'write_min_latency_nsec': 'write_min_latency_nsec'
    }

    def __init__(self, physical_usage=None, physical_writes=None, read_avg_latency_nsec=None, write_avg_latency_nsec=None, drive_uuid=None, write_min_latency_nsec=None):  # noqa: E501
        """VolumeStats - a model defined in Swagger"""  # noqa: E501

        self._physical_usage = None
        self._physical_writes = None
        self._read_avg_latency_nsec = None
        self._write_avg_latency_nsec = None
        self._drive_uuid = None
        self._write_min_latency_nsec = None
        self.discriminator = None

        if physical_usage is not None:
            self.physical_usage = physical_usage
        if physical_writes is not None:
            self.physical_writes = physical_writes
        if read_avg_latency_nsec is not None:
            self.read_avg_latency_nsec = read_avg_latency_nsec
        if write_avg_latency_nsec is not None:
            self.write_avg_latency_nsec = write_avg_latency_nsec
        if drive_uuid is not None:
            self.drive_uuid = drive_uuid
        if write_min_latency_nsec is not None:
            self.write_min_latency_nsec = write_min_latency_nsec

    @property
    def physical_usage(self):
        """Gets the physical_usage of this VolumeStats.  # noqa: E501


        :return: The physical_usage of this VolumeStats.  # noqa: E501
        :rtype: int
        """
        return self._physical_usage

    @physical_usage.setter
    def physical_usage(self, physical_usage):
        """Sets the physical_usage of this VolumeStats.


        :param physical_usage: The physical_usage of this VolumeStats.  # noqa: E501
        :type: int
        """

        self._physical_usage = physical_usage

    @property
    def physical_writes(self):
        """Gets the physical_writes of this VolumeStats.  # noqa: E501


        :return: The physical_writes of this VolumeStats.  # noqa: E501
        :rtype: int
        """
        return self._physical_writes

    @physical_writes.setter
    def physical_writes(self, physical_writes):
        """Sets the physical_writes of this VolumeStats.


        :param physical_writes: The physical_writes of this VolumeStats.  # noqa: E501
        :type: int
        """

        self._physical_writes = physical_writes

    @property
    def read_avg_latency_nsec(self):
        """Gets the read_avg_latency_nsec of this VolumeStats.  # noqa: E501


        :return: The read_avg_latency_nsec of this VolumeStats.  # noqa: E501
        :rtype: int
        """
        return self._read_avg_latency_nsec

    @read_avg_latency_nsec.setter
    def read_avg_latency_nsec(self, read_avg_latency_nsec):
        """Sets the read_avg_latency_nsec of this VolumeStats.


        :param read_avg_latency_nsec: The read_avg_latency_nsec of this VolumeStats.  # noqa: E501
        :type: int
        """

        self._read_avg_latency_nsec = read_avg_latency_nsec

    @property
    def write_avg_latency_nsec(self):
        """Gets the write_avg_latency_nsec of this VolumeStats.  # noqa: E501


        :return: The write_avg_latency_nsec of this VolumeStats.  # noqa: E501
        :rtype: int
        """
        return self._write_avg_latency_nsec

    @write_avg_latency_nsec.setter
    def write_avg_latency_nsec(self, write_avg_latency_nsec):
        """Sets the write_avg_latency_nsec of this VolumeStats.


        :param write_avg_latency_nsec: The write_avg_latency_nsec of this VolumeStats.  # noqa: E501
        :type: int
        """

        self._write_avg_latency_nsec = write_avg_latency_nsec

    @property
    def drive_uuid(self):
        """Gets the drive_uuid of this VolumeStats.  # noqa: E501


        :return: The drive_uuid of this VolumeStats.  # noqa: E501
        :rtype: str
        """
        return self._drive_uuid

    @drive_uuid.setter
    def drive_uuid(self, drive_uuid):
        """Sets the drive_uuid of this VolumeStats.


        :param drive_uuid: The drive_uuid of this VolumeStats.  # noqa: E501
        :type: str
        """

        self._drive_uuid = drive_uuid

    @property
    def write_min_latency_nsec(self):
        """Gets the write_min_latency_nsec of this VolumeStats.  # noqa: E501


        :return: The write_min_latency_nsec of this VolumeStats.  # noqa: E501
        :rtype: int
        """
        return self._write_min_latency_nsec

    @write_min_latency_nsec.setter
    def write_min_latency_nsec(self, write_min_latency_nsec):
        """Sets the write_min_latency_nsec of this VolumeStats.


        :param write_min_latency_nsec: The write_min_latency_nsec of this VolumeStats.  # noqa: E501
        :type: int
        """

        self._write_min_latency_nsec = write_min_latency_nsec

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
        if issubclass(VolumeStats, dict):
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
        if not isinstance(other, VolumeStats):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
