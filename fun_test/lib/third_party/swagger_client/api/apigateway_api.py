# coding: utf-8

"""
    Fungible Controller Intent API

    Intent based REST API for interfacing between the management/orchestration system and Fungible Controller `(FC)` Services `INTERNAL`: The API is for internal controller use only `DEBUG`: The API will not be available in production use   # noqa: E501

    OpenAPI spec version: 1.0.0
    Contact: storage@fungible.com
    Generated by: https://github.com/swagger-api/swagger-codegen.git
"""


from __future__ import absolute_import

import re  # noqa: F401

# python 2 and python 3 compatibility library
import six

from swagger_client.api_client import ApiClient


class ApigatewayApi(object):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    Ref: https://github.com/swagger-api/swagger-codegen
    """

    def __init__(self, api_client=None):
        if api_client is None:
            api_client = ApiClient()
        self.api_client = api_client

    def download_fc_logs(self, **kwargs):  # noqa: E501
        """(INTERNAL) Download controller logs  # noqa: E501

        Download controller logs (and only in single node case also the system logs)  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.download_fc_logs(async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :return: file
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs['_return_http_data_only'] = True
        if kwargs.get('async_req'):
            return self.download_fc_logs_with_http_info(**kwargs)  # noqa: E501
        else:
            (data) = self.download_fc_logs_with_http_info(**kwargs)  # noqa: E501
            return data

    def download_fc_logs_with_http_info(self, **kwargs):  # noqa: E501
        """(INTERNAL) Download controller logs  # noqa: E501

        Download controller logs (and only in single node case also the system logs)  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.download_fc_logs_with_http_info(async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :return: file
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = []  # noqa: E501
        all_params.append('async_req')
        all_params.append('_return_http_data_only')
        all_params.append('_preload_content')
        all_params.append('_request_timeout')

        params = locals()
        for key, val in six.iteritems(params['kwargs']):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method download_fc_logs" % key
                )
            params[key] = val
        del params['kwargs']

        collection_formats = {}

        path_params = {}

        query_params = []

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        # HTTP header `Accept`
        header_params['Accept'] = self.api_client.select_header_accept(
            ['application/octet-stream'])  # noqa: E501

        # HTTP header `Content-Type`
        header_params['Content-Type'] = self.api_client.select_header_content_type(  # noqa: E501
            ['application/json'])  # noqa: E501

        # Authentication setting
        auth_settings = ['ApiKeyAuth', 'basicAuth']  # noqa: E501

        return self.api_client.call_api(
            '/apigateway/download', 'GET',
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type='file',  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get('async_req'),
            _return_http_data_only=params.get('_return_http_data_only'),
            _preload_content=params.get('_preload_content', True),
            _request_timeout=params.get('_request_timeout'),
            collection_formats=collection_formats)

    def download_logs_deprecate(self, **kwargs):  # noqa: E501
        """Download controller logs (to be deprecated)  # noqa: E501

        Download controller logs (and only in single node case also the system logs)  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.download_logs_deprecate(async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :return: file
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs['_return_http_data_only'] = True
        if kwargs.get('async_req'):
            return self.download_logs_deprecate_with_http_info(**kwargs)  # noqa: E501
        else:
            (data) = self.download_logs_deprecate_with_http_info(**kwargs)  # noqa: E501
            return data

    def download_logs_deprecate_with_http_info(self, **kwargs):  # noqa: E501
        """Download controller logs (to be deprecated)  # noqa: E501

        Download controller logs (and only in single node case also the system logs)  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.download_logs_deprecate_with_http_info(async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :return: file
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = []  # noqa: E501
        all_params.append('async_req')
        all_params.append('_return_http_data_only')
        all_params.append('_preload_content')
        all_params.append('_request_timeout')

        params = locals()
        for key, val in six.iteritems(params['kwargs']):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method download_logs_deprecate" % key
                )
            params[key] = val
        del params['kwargs']

        collection_formats = {}

        path_params = {}

        query_params = []

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        # HTTP header `Accept`
        header_params['Accept'] = self.api_client.select_header_accept(
            ['application/octet-stream'])  # noqa: E501

        # HTTP header `Content-Type`
        header_params['Content-Type'] = self.api_client.select_header_content_type(  # noqa: E501
            ['application/json'])  # noqa: E501

        # Authentication setting
        auth_settings = ['ApiKeyAuth', 'basicAuth']  # noqa: E501

        return self.api_client.call_api(
            '/logs/download', 'GET',
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type='file',  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get('async_req'),
            _return_http_data_only=params.get('_return_http_data_only'),
            _preload_content=params.get('_preload_content', True),
            _request_timeout=params.get('_request_timeout'),
            collection_formats=collection_formats)

    def fc_bundle_version(self, **kwargs):  # noqa: E501
        """(INTERNAL) Build version of software bundle  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.fc_bundle_version(async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :return: ResponseDataWithBldVersion
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs['_return_http_data_only'] = True
        if kwargs.get('async_req'):
            return self.fc_bundle_version_with_http_info(**kwargs)  # noqa: E501
        else:
            (data) = self.fc_bundle_version_with_http_info(**kwargs)  # noqa: E501
            return data

    def fc_bundle_version_with_http_info(self, **kwargs):  # noqa: E501
        """(INTERNAL) Build version of software bundle  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.fc_bundle_version_with_http_info(async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :return: ResponseDataWithBldVersion
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = []  # noqa: E501
        all_params.append('async_req')
        all_params.append('_return_http_data_only')
        all_params.append('_preload_content')
        all_params.append('_request_timeout')

        params = locals()
        for key, val in six.iteritems(params['kwargs']):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method fc_bundle_version" % key
                )
            params[key] = val
        del params['kwargs']

        collection_formats = {}

        path_params = {}

        query_params = []

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        # HTTP header `Accept`
        header_params['Accept'] = self.api_client.select_header_accept(
            ['application/json'])  # noqa: E501

        # HTTP header `Content-Type`
        header_params['Content-Type'] = self.api_client.select_header_content_type(  # noqa: E501
            ['application/json'])  # noqa: E501

        # Authentication setting
        auth_settings = ['ApiKeyAuth', 'basicAuth']  # noqa: E501

        return self.api_client.call_api(
            '/apigateway/version', 'GET',
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type='ResponseDataWithBldVersion',  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get('async_req'),
            _return_http_data_only=params.get('_return_http_data_only'),
            _preload_content=params.get('_preload_content', True),
            _request_timeout=params.get('_request_timeout'),
            collection_formats=collection_formats)

    def fc_restart(self, **kwargs):  # noqa: E501
        """(INTERNAL) Restart apigateway and controller services  # noqa: E501

        To shut down and restart the API gateway, controller services  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.fc_restart(async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :return: None
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs['_return_http_data_only'] = True
        if kwargs.get('async_req'):
            return self.fc_restart_with_http_info(**kwargs)  # noqa: E501
        else:
            (data) = self.fc_restart_with_http_info(**kwargs)  # noqa: E501
            return data

    def fc_restart_with_http_info(self, **kwargs):  # noqa: E501
        """(INTERNAL) Restart apigateway and controller services  # noqa: E501

        To shut down and restart the API gateway, controller services  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.fc_restart_with_http_info(async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :return: None
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = []  # noqa: E501
        all_params.append('async_req')
        all_params.append('_return_http_data_only')
        all_params.append('_preload_content')
        all_params.append('_request_timeout')

        params = locals()
        for key, val in six.iteritems(params['kwargs']):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method fc_restart" % key
                )
            params[key] = val
        del params['kwargs']

        collection_formats = {}

        path_params = {}

        query_params = []

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        # HTTP header `Accept`
        header_params['Accept'] = self.api_client.select_header_accept(
            ['application/json'])  # noqa: E501

        # HTTP header `Content-Type`
        header_params['Content-Type'] = self.api_client.select_header_content_type(  # noqa: E501
            ['application/json'])  # noqa: E501

        # Authentication setting
        auth_settings = ['ApiKeyAuth', 'basicAuth']  # noqa: E501

        return self.api_client.call_api(
            '/apigateway/restart', 'POST',
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type=None,  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get('async_req'),
            _return_http_data_only=params.get('_return_http_data_only'),
            _preload_content=params.get('_preload_content', True),
            _request_timeout=params.get('_request_timeout'),
            collection_formats=collection_formats)

    def get_fc_health(self, **kwargs):  # noqa: E501
        """Get health of apigateway  # noqa: E501

        Check health of apigateway  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.get_fc_health(async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :return: CommonResponseFields
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs['_return_http_data_only'] = True
        if kwargs.get('async_req'):
            return self.get_fc_health_with_http_info(**kwargs)  # noqa: E501
        else:
            (data) = self.get_fc_health_with_http_info(**kwargs)  # noqa: E501
            return data

    def get_fc_health_with_http_info(self, **kwargs):  # noqa: E501
        """Get health of apigateway  # noqa: E501

        Check health of apigateway  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.get_fc_health_with_http_info(async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :return: CommonResponseFields
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = []  # noqa: E501
        all_params.append('async_req')
        all_params.append('_return_http_data_only')
        all_params.append('_preload_content')
        all_params.append('_request_timeout')

        params = locals()
        for key, val in six.iteritems(params['kwargs']):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method get_fc_health" % key
                )
            params[key] = val
        del params['kwargs']

        collection_formats = {}

        path_params = {}

        query_params = []

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        # HTTP header `Accept`
        header_params['Accept'] = self.api_client.select_header_accept(
            ['application/json'])  # noqa: E501

        # HTTP header `Content-Type`
        header_params['Content-Type'] = self.api_client.select_header_content_type(  # noqa: E501
            ['application/json'])  # noqa: E501

        # Authentication setting
        auth_settings = ['ApiKeyAuth', 'basicAuth']  # noqa: E501

        return self.api_client.call_api(
            '/api_server/health', 'GET',
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type='CommonResponseFields',  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get('async_req'),
            _return_http_data_only=params.get('_return_http_data_only'),
            _preload_content=params.get('_preload_content', True),
            _request_timeout=params.get('_request_timeout'),
            collection_formats=collection_formats)

    def get_kafka_health(self, **kwargs):  # noqa: E501
        """(INTERNAL) Get health of kafka service running in apigateway  # noqa: E501

        Check health of kafka by issuing a \"async\" produce operation on a topic  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.get_kafka_health(async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :return: CommonResponseFields
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs['_return_http_data_only'] = True
        if kwargs.get('async_req'):
            return self.get_kafka_health_with_http_info(**kwargs)  # noqa: E501
        else:
            (data) = self.get_kafka_health_with_http_info(**kwargs)  # noqa: E501
            return data

    def get_kafka_health_with_http_info(self, **kwargs):  # noqa: E501
        """(INTERNAL) Get health of kafka service running in apigateway  # noqa: E501

        Check health of kafka by issuing a \"async\" produce operation on a topic  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.get_kafka_health_with_http_info(async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :return: CommonResponseFields
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = []  # noqa: E501
        all_params.append('async_req')
        all_params.append('_return_http_data_only')
        all_params.append('_preload_content')
        all_params.append('_request_timeout')

        params = locals()
        for key, val in six.iteritems(params['kwargs']):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method get_kafka_health" % key
                )
            params[key] = val
        del params['kwargs']

        collection_formats = {}

        path_params = {}

        query_params = []

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        # HTTP header `Accept`
        header_params['Accept'] = self.api_client.select_header_accept(
            ['application/json'])  # noqa: E501

        # HTTP header `Content-Type`
        header_params['Content-Type'] = self.api_client.select_header_content_type(  # noqa: E501
            ['application/json'])  # noqa: E501

        # Authentication setting
        auth_settings = ['ApiKeyAuth', 'basicAuth']  # noqa: E501

        return self.api_client.call_api(
            '/apigateway/kafka_health', 'GET',
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type='CommonResponseFields',  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get('async_req'),
            _return_http_data_only=params.get('_return_http_data_only'),
            _preload_content=params.get('_preload_content', True),
            _request_timeout=params.get('_request_timeout'),
            collection_formats=collection_formats)

    def get_kafka_timeout(self, **kwargs):  # noqa: E501
        """(DEBUG) Test rest-mq service timeout handling  # noqa: E501

        Test bahavior in case of timeout  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.get_kafka_timeout(async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :return: CommonResponseFields
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs['_return_http_data_only'] = True
        if kwargs.get('async_req'):
            return self.get_kafka_timeout_with_http_info(**kwargs)  # noqa: E501
        else:
            (data) = self.get_kafka_timeout_with_http_info(**kwargs)  # noqa: E501
            return data

    def get_kafka_timeout_with_http_info(self, **kwargs):  # noqa: E501
        """(DEBUG) Test rest-mq service timeout handling  # noqa: E501

        Test bahavior in case of timeout  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.get_kafka_timeout_with_http_info(async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :return: CommonResponseFields
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = []  # noqa: E501
        all_params.append('async_req')
        all_params.append('_return_http_data_only')
        all_params.append('_preload_content')
        all_params.append('_request_timeout')

        params = locals()
        for key, val in six.iteritems(params['kwargs']):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method get_kafka_timeout" % key
                )
            params[key] = val
        del params['kwargs']

        collection_formats = {}

        path_params = {}

        query_params = []

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        # HTTP header `Accept`
        header_params['Accept'] = self.api_client.select_header_accept(
            ['application/json'])  # noqa: E501

        # HTTP header `Content-Type`
        header_params['Content-Type'] = self.api_client.select_header_content_type(  # noqa: E501
            ['application/json'])  # noqa: E501

        # Authentication setting
        auth_settings = ['ApiKeyAuth', 'basicAuth']  # noqa: E501

        return self.api_client.call_api(
            '/apigateway/test_rest_timeout', 'GET',
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type='CommonResponseFields',  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get('async_req'),
            _return_http_data_only=params.get('_return_http_data_only'),
            _preload_content=params.get('_preload_content', True),
            _request_timeout=params.get('_request_timeout'),
            collection_formats=collection_formats)

    def get_user_token(self, body_get_user_token, **kwargs):  # noqa: E501
        """Get a token  # noqa: E501

        For user to generate a token with basic auth  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.get_user_token(body_get_user_token, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param BodyGetUserToken body_get_user_token: (required)
        :return: ResponseDataWithUserToken
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs['_return_http_data_only'] = True
        if kwargs.get('async_req'):
            return self.get_user_token_with_http_info(body_get_user_token, **kwargs)  # noqa: E501
        else:
            (data) = self.get_user_token_with_http_info(body_get_user_token, **kwargs)  # noqa: E501
            return data

    def get_user_token_with_http_info(self, body_get_user_token, **kwargs):  # noqa: E501
        """Get a token  # noqa: E501

        For user to generate a token with basic auth  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.get_user_token_with_http_info(body_get_user_token, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param BodyGetUserToken body_get_user_token: (required)
        :return: ResponseDataWithUserToken
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = ['body_get_user_token']  # noqa: E501
        all_params.append('async_req')
        all_params.append('_return_http_data_only')
        all_params.append('_preload_content')
        all_params.append('_request_timeout')

        params = locals()
        for key, val in six.iteritems(params['kwargs']):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method get_user_token" % key
                )
            params[key] = val
        del params['kwargs']
        # verify the required parameter 'body_get_user_token' is set
        if ('body_get_user_token' not in params or
                params['body_get_user_token'] is None):
            raise ValueError("Missing the required parameter `body_get_user_token` when calling `get_user_token`")  # noqa: E501

        collection_formats = {}

        path_params = {}

        query_params = []

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        if 'body_get_user_token' in params:
            body_params = params['body_get_user_token']
        # HTTP header `Accept`
        header_params['Accept'] = self.api_client.select_header_accept(
            ['application/json'])  # noqa: E501

        # HTTP header `Content-Type`
        header_params['Content-Type'] = self.api_client.select_header_content_type(  # noqa: E501
            ['application/json'])  # noqa: E501

        # Authentication setting
        auth_settings = []  # noqa: E501

        return self.api_client.call_api(
            '/user/token', 'POST',
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type='ResponseDataWithUserToken',  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get('async_req'),
            _return_http_data_only=params.get('_return_http_data_only'),
            _preload_content=params.get('_preload_content', True),
            _request_timeout=params.get('_request_timeout'),
            collection_formats=collection_formats)

    def upgrade_fc_software(self, **kwargs):  # noqa: E501
        """(INTERNAL) Upgrades sc software  # noqa: E501

        Used to upgrade controller s/w  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.upgrade_fc_software(async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param file upfile: The file to upload
        :return: SuccessResponseFields
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs['_return_http_data_only'] = True
        if kwargs.get('async_req'):
            return self.upgrade_fc_software_with_http_info(**kwargs)  # noqa: E501
        else:
            (data) = self.upgrade_fc_software_with_http_info(**kwargs)  # noqa: E501
            return data

    def upgrade_fc_software_with_http_info(self, **kwargs):  # noqa: E501
        """(INTERNAL) Upgrades sc software  # noqa: E501

        Used to upgrade controller s/w  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.upgrade_fc_software_with_http_info(async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param file upfile: The file to upload
        :return: SuccessResponseFields
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = ['upfile']  # noqa: E501
        all_params.append('async_req')
        all_params.append('_return_http_data_only')
        all_params.append('_preload_content')
        all_params.append('_request_timeout')

        params = locals()
        for key, val in six.iteritems(params['kwargs']):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method upgrade_fc_software" % key
                )
            params[key] = val
        del params['kwargs']

        collection_formats = {}

        path_params = {}

        query_params = []

        header_params = {}

        form_params = []
        local_var_files = {}
        if 'upfile' in params:
            local_var_files['upfile'] = params['upfile']  # noqa: E501

        body_params = None
        # HTTP header `Accept`
        header_params['Accept'] = self.api_client.select_header_accept(
            ['application/json'])  # noqa: E501

        # HTTP header `Content-Type`
        header_params['Content-Type'] = self.api_client.select_header_content_type(  # noqa: E501
            ['multipart/form-data'])  # noqa: E501

        # Authentication setting
        auth_settings = ['ApiKeyAuth', 'basicAuth']  # noqa: E501

        return self.api_client.call_api(
            '/apigateway/upload', 'POST',
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type='SuccessResponseFields',  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get('async_req'),
            _return_http_data_only=params.get('_return_http_data_only'),
            _preload_content=params.get('_preload_content', True),
            _request_timeout=params.get('_request_timeout'),
            collection_formats=collection_formats)

    def upgrade_fc_status(self, **kwargs):  # noqa: E501
        """(INTERNAL) status of fc software upgrade  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.upgrade_fc_status(async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :return: ResponseDataWithUpgradeStatus
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs['_return_http_data_only'] = True
        if kwargs.get('async_req'):
            return self.upgrade_fc_status_with_http_info(**kwargs)  # noqa: E501
        else:
            (data) = self.upgrade_fc_status_with_http_info(**kwargs)  # noqa: E501
            return data

    def upgrade_fc_status_with_http_info(self, **kwargs):  # noqa: E501
        """(INTERNAL) status of fc software upgrade  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.upgrade_fc_status_with_http_info(async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :return: ResponseDataWithUpgradeStatus
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = []  # noqa: E501
        all_params.append('async_req')
        all_params.append('_return_http_data_only')
        all_params.append('_preload_content')
        all_params.append('_request_timeout')

        params = locals()
        for key, val in six.iteritems(params['kwargs']):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method upgrade_fc_status" % key
                )
            params[key] = val
        del params['kwargs']

        collection_formats = {}

        path_params = {}

        query_params = []

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        # HTTP header `Accept`
        header_params['Accept'] = self.api_client.select_header_accept(
            ['application/json'])  # noqa: E501

        # HTTP header `Content-Type`
        header_params['Content-Type'] = self.api_client.select_header_content_type(  # noqa: E501
            ['application/json'])  # noqa: E501

        # Authentication setting
        auth_settings = ['ApiKeyAuth', 'basicAuth']  # noqa: E501

        return self.api_client.call_api(
            '/apigateway/upgrade_status', 'GET',
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type='ResponseDataWithUpgradeStatus',  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get('async_req'),
            _return_http_data_only=params.get('_return_http_data_only'),
            _preload_content=params.get('_preload_content', True),
            _request_timeout=params.get('_request_timeout'),
            collection_formats=collection_formats)