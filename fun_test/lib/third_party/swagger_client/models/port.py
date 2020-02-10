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


class Port(object):
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
        'transport': 'Transport',
        'host_nqn': 'str',
        'ip': 'str',
        'nsid': 'int',
        'remote_ip': 'str',
        'nqn': 'str',
        'fnid': 'object',
        'huid': 'object',
        'ctlid': 'object'
    }

    attribute_map = {
        'uuid': 'uuid',
        'transport': 'transport',
        'host_nqn': 'host_nqn',
        'ip': 'ip',
        'nsid': 'nsid',
        'remote_ip': 'remote_ip',
        'nqn': 'nqn',
        'fnid': 'fnid',
        'huid': 'huid',
        'ctlid': 'ctlid'
    }

    def __init__(self, uuid=None, transport=None, host_nqn=None, ip=None, nsid=None, remote_ip=None, nqn=None, fnid=None, huid=None, ctlid=None):  # noqa: E501
        """Port - a model defined in Swagger"""  # noqa: E501

        self._uuid = None
        self._transport = None
        self._host_nqn = None
        self._ip = None
        self._nsid = None
        self._remote_ip = None
        self._nqn = None
        self._fnid = None
        self._huid = None
        self._ctlid = None
        self.discriminator = None

        self.uuid = uuid
        self.transport = transport
        if host_nqn is not None:
            self.host_nqn = host_nqn
        if ip is not None:
            self.ip = ip
        if nsid is not None:
            self.nsid = nsid
        if remote_ip is not None:
            self.remote_ip = remote_ip
        if nqn is not None:
            self.nqn = nqn
        if fnid is not None:
            self.fnid = fnid
        if huid is not None:
            self.huid = huid
        if ctlid is not None:
            self.ctlid = ctlid

    @property
    def uuid(self):
        """Gets the uuid of this Port.  # noqa: E501

        assigned by FC  # noqa: E501

        :return: The uuid of this Port.  # noqa: E501
        :rtype: str
        """
        return self._uuid

    @uuid.setter
    def uuid(self, uuid):
        """Sets the uuid of this Port.

        assigned by FC  # noqa: E501

        :param uuid: The uuid of this Port.  # noqa: E501
        :type: str
        """
        if uuid is None:
            raise ValueError("Invalid value for `uuid`, must not be `None`")  # noqa: E501

        self._uuid = uuid

    @property
    def transport(self):
        """Gets the transport of this Port.  # noqa: E501


        :return: The transport of this Port.  # noqa: E501
        :rtype: Transport
        """
        return self._transport

    @transport.setter
    def transport(self, transport):
        """Sets the transport of this Port.


        :param transport: The transport of this Port.  # noqa: E501
        :type: Transport
        """
        if transport is None:
            raise ValueError("Invalid value for `transport`, must not be `None`")  # noqa: E501

        self._transport = transport

    @property
    def host_nqn(self):
        """Gets the host_nqn of this Port.  # noqa: E501


        :return: The host_nqn of this Port.  # noqa: E501
        :rtype: str
        """
        return self._host_nqn

    @host_nqn.setter
    def host_nqn(self, host_nqn):
        """Sets the host_nqn of this Port.


        :param host_nqn: The host_nqn of this Port.  # noqa: E501
        :type: str
        """

        self._host_nqn = host_nqn

    @property
    def ip(self):
        """Gets the ip of this Port.  # noqa: E501


        :return: The ip of this Port.  # noqa: E501
        :rtype: str
        """
        return self._ip

    @ip.setter
    def ip(self, ip):
        """Sets the ip of this Port.


        :param ip: The ip of this Port.  # noqa: E501
        :type: str
        """

        self._ip = ip

    @property
    def nsid(self):
        """Gets the nsid of this Port.  # noqa: E501


        :return: The nsid of this Port.  # noqa: E501
        :rtype: int
        """
        return self._nsid

    @nsid.setter
    def nsid(self, nsid):
        """Sets the nsid of this Port.


        :param nsid: The nsid of this Port.  # noqa: E501
        :type: int
        """

        self._nsid = nsid

    @property
    def remote_ip(self):
        """Gets the remote_ip of this Port.  # noqa: E501


        :return: The remote_ip of this Port.  # noqa: E501
        :rtype: str
        """
        return self._remote_ip

    @remote_ip.setter
    def remote_ip(self, remote_ip):
        """Sets the remote_ip of this Port.


        :param remote_ip: The remote_ip of this Port.  # noqa: E501
        :type: str
        """

        self._remote_ip = remote_ip

    @property
    def nqn(self):
        """Gets the nqn of this Port.  # noqa: E501


        :return: The nqn of this Port.  # noqa: E501
        :rtype: str
        """
        return self._nqn

    @nqn.setter
    def nqn(self, nqn):
        """Sets the nqn of this Port.


        :param nqn: The nqn of this Port.  # noqa: E501
        :type: str
        """

        self._nqn = nqn

    @property
    def fnid(self):
        """Gets the fnid of this Port.  # noqa: E501


        :return: The fnid of this Port.  # noqa: E501
        :rtype: object
        """
        return self._fnid

    @fnid.setter
    def fnid(self, fnid):
        """Sets the fnid of this Port.


        :param fnid: The fnid of this Port.  # noqa: E501
        :type: object
        """

        self._fnid = fnid

    @property
    def huid(self):
        """Gets the huid of this Port.  # noqa: E501


        :return: The huid of this Port.  # noqa: E501
        :rtype: object
        """
        return self._huid

    @huid.setter
    def huid(self, huid):
        """Sets the huid of this Port.


        :param huid: The huid of this Port.  # noqa: E501
        :type: object
        """

        self._huid = huid

    @property
    def ctlid(self):
        """Gets the ctlid of this Port.  # noqa: E501


        :return: The ctlid of this Port.  # noqa: E501
        :rtype: object
        """
        return self._ctlid

    @ctlid.setter
    def ctlid(self, ctlid):
        """Sets the ctlid of this Port.


        :param ctlid: The ctlid of this Port.  # noqa: E501
        :type: object
        """

        self._ctlid = ctlid

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
        if issubclass(Port, dict):
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
        if not isinstance(other, Port):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
