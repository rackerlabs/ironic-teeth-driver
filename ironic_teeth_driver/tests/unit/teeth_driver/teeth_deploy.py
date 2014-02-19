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


class FakeNode():
    provision_state = states.NOSTATE
    target_provision_state = states.NOSTATE

    def __init__(self):
        self.driver_info = {
            'image_info': {
                'image_id': 'test'
            },
            'metadata': {
                'foo': 'bar'
            },
            'files': ['foo.tar.gz'],
            'agent_url': 'http://127.0.0.1/foo'
        }

    def save(self, context):
        pass


class FakeTask():
    def __init__(self):
        self.context = {}


class TestTeethDeploy(unittest.TestCase):
    def setUp(self):
        self.driver = teeth.TeethDeploy()
        self.task = FakeTask()

    def test_validate(self):
        node = FakeNode()
        task = FakeTask()
        self.driver.validate(task, node)

    def test_validate_fail(self):
        node = FakeNode()
        task = FakeTask()
        del node.driver_info['agent_url']
        with self.assertRaises(exception.InvalidParameterValue):
            self.driver.validate(task, node)

    @mock.patch('ironic_teeth_driver.teeth.TeethDeploy._get_client')
    def test_deploy(self, get_client_mock):
        node = FakeNode()
        driver_info = node.driver_info

        client_mock = mock.Mock()

        client_mock.prepare_image.return_value = None
        client_mock.run_image.return_value = None

        get_client_mock.return_value = client_mock

        driver_return = self.driver.deploy(self.task, node)
        client_mock.prepare_image.assert_called_with(node,
                                                     driver_info['image_info'],
                                                     driver_info['metadata'],
                                                     node.driver_info['files'])
        client_mock.run_image.assert_called_with(node)
        self.assertEqual(driver_return, states.DEPLOYING)
        self.assertEqual(node.provision_state, states.DEPLOYING)
        self.assertEqual(node.target_provision_state, states.DEPLOYDONE)

    def test_deploy_bad_params(self):

        with self.assertRaises(exception.InvalidParameterValue):
            node = FakeNode()
            del node.driver_info['image_info']
            self.driver.deploy(self.task, node)

        with self.assertRaises(exception.InvalidParameterValue):
            node = FakeNode()
            del node.driver_info['metadata']
            self.driver.deploy(self.task, node)

        with self.assertRaises(exception.InvalidParameterValue):
            node = FakeNode()
            del node.driver_info['files']
            self.driver.deploy(self.task, node)

    @mock.patch('ironic.conductor.utils.node_power_action')
    def test_tear_down(self, power_mock):
        node = FakeNode()

        driver_return = self.driver.tear_down(self.task, node)
        power_mock.assert_called_with(self.task, node, states.REBOOT)

        self.assertEqual(driver_return, states.DELETING)
        self.assertEqual(node.provision_state, states.DELETING)
        self.assertEqual(node.target_provision_state, states.DELETED)

    @mock.patch('ironic_teeth_driver.teeth.TeethDeploy._get_client')
    def test_prepare(self, get_client_mock):
        node = FakeNode()
        driver_info = node.driver_info

        client_mock = mock.Mock()
        client_mock.cache_image.return_value = None

        get_client_mock.return_value = client_mock

        driver_return = self.driver.prepare(self.task, node)
        client_mock.cache_image.assert_called_with(node,
                                                   driver_info['image_info'])
        self.assertEqual(driver_return, 'preparing')
        #TODO(pcsforeducation) replace 'preparing' with states.PREPARING
        # when the merge is done upstream
        self.assertEqual(node.provision_state, states.BUILDING)
        self.assertEqual(node.target_provision_state, 'preparing')

    def test_prepare_bad_params(self):
        with self.assertRaises(exception.InvalidParameterValue):
            node = FakeNode()
            del node.driver_info['image_info']
            self.driver.prepare(self.task, node)