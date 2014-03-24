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
        self.deploy_data = {
            'image_info': {
                'image_id': 'test'
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
        node = FakeNode()
        task = FakeTask()
        self.driver.validate(task, node)

    def test_validate_fail(self):
        node = FakeNode()
        task = FakeTask()
        del node.driver_info['agent_url']
        deploy_data = node.deploy_data
        self.assertRaises(exception.InvalidParameterValue,
                          self.driver.validate,
                          task,
                          node,
                          deploy_data)

    @mock.patch('ironic_teeth_driver.teeth.TeethDeploy._get_client')
    def test_deploy(self, get_client_mock):
        node = FakeNode()
        deploy_data = node.deploy_data

        client_mock = mock.Mock()

        client_mock.prepare_image.return_value = None
        client_mock.run_image.return_value = None

        get_client_mock.return_value = client_mock

        driver_return = self.driver.deploy(self.task, node, deploy_data)
        client_mock.prepare_image.assert_called_with(node,
                                                     deploy_data['image_info'],
                                                     deploy_data['metadata'],
                                                     deploy_data['files'],
                                                     wait=True)
        client_mock.run_image.assert_called_with(node, wait=True)
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
        # driver_info = node.driver_info
        deploy_data = node.deploy_data

        client_mock = mock.Mock()
        client_mock.cache_image.return_value = None

        get_client_mock.return_value = client_mock

        driver_return = self.driver.prepare(self.task, node, deploy_data)
        client_mock.cache_image.assert_called_with(node,
                                                   deploy_data['image_info'],
                                                   force=False,
                                                   wait=True)
        self.assertEqual(driver_return, 'prepared')
        #TODO(pcsforeducation) replace 'preparing' with states.PREPARED
        # when the merge is done upstream
        self.assertEqual(node.provision_state, 'prepared')
        self.assertEqual(node.target_provision_state, 'prepared')

    def test_validate_bad_params(self):
        node = FakeNode()
        deploy_data = node.deploy_data
        del deploy_data['image_info']
        self.assertRaises(exception.InvalidParameterValue,
                          self.driver.validate,
                          self.task,
                          node,
                          deploy_data)
