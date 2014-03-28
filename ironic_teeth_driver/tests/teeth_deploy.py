"""
Copyright 2014 Rackspace, Inc.

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
from ironic.common import exception
from ironic.common import states
from ironic_teeth_driver import teeth

import mock
import unittest


class FakeNode(object):
    provision_state = states.NOSTATE
    target_provision_state = states.NOSTATE

    def __init__(self):
        self.driver_info = {
            'agent_url': 'http://127.0.0.1/foo'
        }
        self.instance_info = {
            'image_info': {
                'image_id': 'test',
                'direct_url': 'swift+http://example.com/v2'
                              '.0/container/fake-uuid'
            },
            'metadata': {
                'foo': 'bar'
            },
            'files': ['foo.tar.gz']
        }

    def save(self, context):
        pass


class FakeTask(object):
    def __init__(self):
        self.context = {}


class TestTeethDeploy(unittest.TestCase):
    def setUp(self):
        self.driver = teeth.TeethDeploy()
        self.task = FakeTask()

    def test_validate(self):
        self.driver.validate(FakeNode())

    def test_validate_fail(self):
        node = FakeNode()
        del node.driver_info['agent_url']
        self.assertRaises(exception.InvalidParameterValue,
                          self.driver.validate,
                          node)

    @mock.patch('ironic.common.image_service.Service')
    @mock.patch('ironic_teeth_driver.teeth.TeethDeploy._get_client')
    def test_deploy(self, get_client_mock, image_service_mock):
        node = FakeNode()
        info = node.instance_info
        expected_image_info = info['image_info']
        expected_image_info['urls'] = [
            'swift+http://example.com/v2.0/container/fake-uuid']

        client_mock = mock.Mock()

        glance_mock = mock.Mock()
        glance_mock.swift_temp_url.return_value = 'swift+http://example' \
                                                  '.com/v2' \
                                                  '.0/container/fake-uuid'
        image_service_mock.return_value = glance_mock

        client_mock.prepare_image.return_value = None
        client_mock.run_image.return_value = None

        get_client_mock.return_value = client_mock

        driver_return = self.driver.deploy(self.task, node)
        client_mock.prepare_image.assert_called_with(node,
                                                     expected_image_info,
                                                     info['metadata'],
                                                     info['files'],
                                                     wait=True)
        client_mock.run_image.assert_called_with(node, wait=True)
        glance_mock.swift_temp_url.assert_called_with(info['image_info'])
        self.assertEqual(driver_return, states.DEPLOYDONE)

    @mock.patch('ironic.conductor.utils.node_power_action')
    def test_tear_down(self, power_mock):
        node = FakeNode()

        driver_return = self.driver.tear_down(self.task, node)
        power_mock.assert_called_with(self.task, node, states.REBOOT)

        self.assertEqual(driver_return, states.DELETING)

    @mock.patch('ironic_teeth_driver.teeth.TeethDeploy._get_client')
    def test_prepare(self, get_client_mock):
        node = FakeNode()
        driver_return = self.driver.prepare(self.task, node)
        self.assertEqual(None, driver_return)

    def test_validate_bad_params(self):
        node = FakeNode()
        del node.instance_info['image_info']
        self.assertRaises(exception.InvalidParameterValue,
            self.driver.validate,
            node)
