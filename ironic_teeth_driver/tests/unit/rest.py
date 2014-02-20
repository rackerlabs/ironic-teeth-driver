"""
Copyright 2013 Rackspace, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import json
import mock
import requests

from ironic_teeth_driver import rest as agent_client
from ironic_teeth_driver import tests


class MockResponse(object):
    def __init__(self, data):
        self.text = json.dumps(data)


class MockNode(object):
    def __init__(self):
        self.driver_info = {
            'agent_url': "127.0.0.1/foo"
        }


class TestRESTAgentClient(tests.TeethMockTestUtilities):
    def setUp(self):
        super(TestRESTAgentClient, self).setUp()
        self.client = agent_client.RESTAgentClient()
        self.client.session = mock.Mock(autospec=requests.Session)
        self.node = MockNode()

    @mock.patch('uuid.uuid4', mock.MagicMock(return_value='uuid'))
    def test_cache_image(self):
        _command = self._mock_attr(self.client, '_command')
        image_info = {'image_id': 'image'}
        params = {'task_id': 'uuid', 'image_info': image_info}

        self.client.cache_image(self.node, image_info)
        _command.assert_called_once_with(self.node,
                                         'standby.cache_image',
                                         params)

    @mock.patch('uuid.uuid4', mock.MagicMock(return_value='uuid'))
    def test_prepare_image(self):
        _command = self._mock_attr(self.client, '_command')
        image_info = {'image_id': 'image'}
        metadata = {}
        files = {}
        params = {
            'task_id': 'uuid',
            'image_info': image_info,
            'metadata': metadata,
            'files': files,
        }

        self.client.prepare_image(self.node,
                                  image_info,
                                  metadata,
                                  files)
        _command.assert_called_once_with(self.node,
                                         'standby.prepare_image',
                                         params)

    @mock.patch('uuid.uuid4', mock.MagicMock(return_value='uuid'))
    def test_run_image(self):
        _command = self._mock_attr(self.client, '_command')
        params = {'task_id': 'uuid'}

        self.client.run_image(self.node)
        _command.assert_called_once_with(self.node,
                                         'standby.run_image',
                                         params)

    def test_secure_drives(self):
        _command = self._mock_attr(self.client, '_command')
        key = 'lol'
        drives = ['/dev/sda']
        params = {'key': key, 'drives': drives}

        self.client.secure_drives(self.node, drives, key)
        _command.assert_called_once_with(self.node,
                                         'decom.secure_drives',
                                         params)

    def test_erase_drives(self):
        _command = self._mock_attr(self.client, '_command')
        key = 'lol'
        drives = ['/dev/sda']
        params = {'key': key, 'drives': drives}

        self.client.erase_drives(self.node, drives, key)
        _command.assert_called_once_with(self.node,
                                         'decom.erase_drives',
                                         params)

    def test_command(self):
        response_data = {'status': 'ok'}
        self.client.session.post.return_value = MockResponse(response_data)
        method = 'standby.run_image'
        image_info = {'image_id': 'test_image'}
        params = {'task_id': 'uuid', 'image_info': image_info}

        url = self.client._get_command_url(self.node)
        body = self.client._get_command_body(method, params)
        headers = {'Content-Type': 'application/json'}

        response = self.client._command(self.node, method, params)
        self.assertEqual(response, response_data)
        self.client.session.post.assert_called_once_with(url,
                                                         data=body,
                                                         headers=headers)
