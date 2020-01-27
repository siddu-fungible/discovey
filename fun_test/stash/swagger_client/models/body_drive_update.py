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


class BodyDriveUpdate(object):
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
        'op': 'DriveUpdateOp',
        'dpu': 'str',
        'state': 'ResourceState',
        'plugged': 'bool',
        'slot_id': 'int',
        'inject_error': 'bool'
    }

    attribute_map = {
        'op': 'op',
        'dpu': 'dpu',
        'state': 'state',
        'plugged': 'plugged',
        'slot_id': 'slot_id',
        'inject_error': 'inject_error'
    }

    def __init__(self, op=None, dpu=None, state=None, plugged=None, slot_id=None, inject_error=None):  # noqa: E501
        """BodyDriveUpdate - a model defined in Swagger"""  # noqa: E501

        self._op = None
        self._dpu = None
        self._state = None
        self._plugged = None
        self._slot_id = None
        self._inject_error = None
        self.discriminator = None

        self.op = op
        if dpu is not None:
            self.dpu = dpu
        if state is not None:
            self.state = state
        if plugged is not None:
            self.plugged = plugged
        if slot_id is not None:
            self.slot_id = slot_id
        if inject_error is not None:
            self.inject_error = inject_error

    @property
    def op(self):
        """Gets the op of this BodyDriveUpdate.  # noqa: E501


        :return: The op of this BodyDriveUpdate.  # noqa: E501
        :rtype: DriveUpdateOp
        """
        return self._op

    @op.setter
    def op(self, op):
        """Sets the op of this BodyDriveUpdate.


        :param op: The op of this BodyDriveUpdate.  # noqa: E501
        :type: DriveUpdateOp
        """
        if op is None:
            raise ValueError("Invalid value for `op`, must not be `None`")  # noqa: E501

        self._op = op

    @property
    def dpu(self):
        """Gets the dpu of this BodyDriveUpdate.  # noqa: E501

        id of dpu to which this drive is to be moved  # noqa: E501

        :return: The dpu of this BodyDriveUpdate.  # noqa: E501
        :rtype: str
        """
        return self._dpu

    @dpu.setter
    def dpu(self, dpu):
        """Sets the dpu of this BodyDriveUpdate.

        id of dpu to which this drive is to be moved  # noqa: E501

        :param dpu: The dpu of this BodyDriveUpdate.  # noqa: E501
        :type: str
        """

        self._dpu = dpu

    @property
    def state(self):
        """Gets the state of this BodyDriveUpdate.  # noqa: E501


        :return: The state of this BodyDriveUpdate.  # noqa: E501
        :rtype: ResourceState
        """
        return self._state

    @state.setter
    def state(self, state):
        """Sets the state of this BodyDriveUpdate.


        :param state: The state of this BodyDriveUpdate.  # noqa: E501
        :type: ResourceState
        """

        self._state = state

    @property
    def plugged(self):
        """Gets the plugged of this BodyDriveUpdate.  # noqa: E501


        :return: The plugged of this BodyDriveUpdate.  # noqa: E501
        :rtype: bool
        """
        return self._plugged

    @plugged.setter
    def plugged(self, plugged):
        """Sets the plugged of this BodyDriveUpdate.


        :param plugged: The plugged of this BodyDriveUpdate.  # noqa: E501
        :type: bool
        """

        self._plugged = plugged

    @property
    def slot_id(self):
        """Gets the slot_id of this BodyDriveUpdate.  # noqa: E501

        dpu slot to which drive is now connected  # noqa: E501

        :return: The slot_id of this BodyDriveUpdate.  # noqa: E501
        :rtype: int
        """
        return self._slot_id

    @slot_id.setter
    def slot_id(self, slot_id):
        """Sets the slot_id of this BodyDriveUpdate.

        dpu slot to which drive is now connected  # noqa: E501

        :param slot_id: The slot_id of this BodyDriveUpdate.  # noqa: E501
        :type: int
        """

        self._slot_id = slot_id

    @property
    def inject_error(self):
        """Gets the inject_error of this BodyDriveUpdate.  # noqa: E501


        :return: The inject_error of this BodyDriveUpdate.  # noqa: E501
        :rtype: bool
        """
        return self._inject_error

    @inject_error.setter
    def inject_error(self, inject_error):
        """Sets the inject_error of this BodyDriveUpdate.


        :param inject_error: The inject_error of this BodyDriveUpdate.  # noqa: E501
        :type: bool
        """

        self._inject_error = inject_error

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
        if issubclass(BodyDriveUpdate, dict):
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
        if not isinstance(other, BodyDriveUpdate):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
