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


class BodyVolumeUpdate(object):
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
        'op': 'VolumeUpdateOp',
        'issue_rebuild': 'bool',
        'failed_vol': 'str',
        'failed_uuid': 'str',
        'dpu_id': 'str',
        'state': 'ResourceState',
        'capacity': 'int'
    }

    attribute_map = {
        'op': 'op',
        'issue_rebuild': 'issue_rebuild',
        'failed_vol': 'failed_vol',
        'failed_uuid': 'failed_uuid',
        'dpu_id': 'dpu_id',
        'state': 'state',
        'capacity': 'capacity'
    }

    def __init__(self, op=None, issue_rebuild=None, failed_vol=None, failed_uuid=None, dpu_id=None, state=None, capacity=None):  # noqa: E501
        """BodyVolumeUpdate - a model defined in Swagger"""  # noqa: E501

        self._op = None
        self._issue_rebuild = None
        self._failed_vol = None
        self._failed_uuid = None
        self._dpu_id = None
        self._state = None
        self._capacity = None
        self.discriminator = None

        self.op = op
        if issue_rebuild is not None:
            self.issue_rebuild = issue_rebuild
        if failed_vol is not None:
            self.failed_vol = failed_vol
        if failed_uuid is not None:
            self.failed_uuid = failed_uuid
        if dpu_id is not None:
            self.dpu_id = dpu_id
        if state is not None:
            self.state = state
        if capacity is not None:
            self.capacity = capacity

    @property
    def op(self):
        """Gets the op of this BodyVolumeUpdate.  # noqa: E501


        :return: The op of this BodyVolumeUpdate.  # noqa: E501
        :rtype: VolumeUpdateOp
        """
        return self._op

    @op.setter
    def op(self, op):
        """Sets the op of this BodyVolumeUpdate.


        :param op: The op of this BodyVolumeUpdate.  # noqa: E501
        :type: VolumeUpdateOp
        """
        if op is None:
            raise ValueError("Invalid value for `op`, must not be `None`")  # noqa: E501

        self._op = op

    @property
    def issue_rebuild(self):
        """Gets the issue_rebuild of this BodyVolumeUpdate.  # noqa: E501


        :return: The issue_rebuild of this BodyVolumeUpdate.  # noqa: E501
        :rtype: bool
        """
        return self._issue_rebuild

    @issue_rebuild.setter
    def issue_rebuild(self, issue_rebuild):
        """Sets the issue_rebuild of this BodyVolumeUpdate.


        :param issue_rebuild: The issue_rebuild of this BodyVolumeUpdate.  # noqa: E501
        :type: bool
        """

        self._issue_rebuild = issue_rebuild

    @property
    def failed_vol(self):
        """Gets the failed_vol of this BodyVolumeUpdate.  # noqa: E501


        :return: The failed_vol of this BodyVolumeUpdate.  # noqa: E501
        :rtype: str
        """
        return self._failed_vol

    @failed_vol.setter
    def failed_vol(self, failed_vol):
        """Sets the failed_vol of this BodyVolumeUpdate.


        :param failed_vol: The failed_vol of this BodyVolumeUpdate.  # noqa: E501
        :type: str
        """

        self._failed_vol = failed_vol

    @property
    def failed_uuid(self):
        """Gets the failed_uuid of this BodyVolumeUpdate.  # noqa: E501


        :return: The failed_uuid of this BodyVolumeUpdate.  # noqa: E501
        :rtype: str
        """
        return self._failed_uuid

    @failed_uuid.setter
    def failed_uuid(self, failed_uuid):
        """Sets the failed_uuid of this BodyVolumeUpdate.


        :param failed_uuid: The failed_uuid of this BodyVolumeUpdate.  # noqa: E501
        :type: str
        """

        self._failed_uuid = failed_uuid

    @property
    def dpu_id(self):
        """Gets the dpu_id of this BodyVolumeUpdate.  # noqa: E501

        id of dpu to which this volume is to be moved  # noqa: E501

        :return: The dpu_id of this BodyVolumeUpdate.  # noqa: E501
        :rtype: str
        """
        return self._dpu_id

    @dpu_id.setter
    def dpu_id(self, dpu_id):
        """Sets the dpu_id of this BodyVolumeUpdate.

        id of dpu to which this volume is to be moved  # noqa: E501

        :param dpu_id: The dpu_id of this BodyVolumeUpdate.  # noqa: E501
        :type: str
        """

        self._dpu_id = dpu_id

    @property
    def state(self):
        """Gets the state of this BodyVolumeUpdate.  # noqa: E501


        :return: The state of this BodyVolumeUpdate.  # noqa: E501
        :rtype: ResourceState
        """
        return self._state

    @state.setter
    def state(self, state):
        """Sets the state of this BodyVolumeUpdate.


        :param state: The state of this BodyVolumeUpdate.  # noqa: E501
        :type: ResourceState
        """

        self._state = state

    @property
    def capacity(self):
        """Gets the capacity of this BodyVolumeUpdate.  # noqa: E501


        :return: The capacity of this BodyVolumeUpdate.  # noqa: E501
        :rtype: int
        """
        return self._capacity

    @capacity.setter
    def capacity(self, capacity):
        """Sets the capacity of this BodyVolumeUpdate.


        :param capacity: The capacity of this BodyVolumeUpdate.  # noqa: E501
        :type: int
        """

        self._capacity = capacity

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
        if issubclass(BodyVolumeUpdate, dict):
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
        if not isinstance(other, BodyVolumeUpdate):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
