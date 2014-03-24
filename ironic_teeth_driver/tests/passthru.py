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
import datetime

from ironic.common import exception
from ironic.common import states
from ironic_teeth_driver import passthru
from ironic_teeth_driver import tests

import mock
from sqlalchemy.orm import exc as db_exc
import unittest


class FakeNode(object):
    provision_state = states.NOSTATE
    target_provision_state = states.NOSTATE

    def __init__(self, driver_info=None, instance_info=None, uuid=None):
        if driver_info:
            self.driver_info = driver_info
        else:
            self.driver_info = {
                'agent_url': 'http://127.0.0.1/foo'
            }
        self.instance_info = instance_info or {}
        self.uuid = uuid or 'fake-uuid'

    def save(self, context):
        pass


class FakeTask(object):
    def __init__(self):
        self.drivername = "fake"
        self.context = {}


class FakePort(object):
    def __init__(self, uuid=None, node_id=None):
        self.uuid = uuid or 'fake-uuid'
        self.node_id = node_id or 'fake-node'

    def save(self, context):
        pass


class TestTeethPassthru(unittest.TestCase):
    def setUp(self):
        self.passthru = passthru.TeethVendorPassthru()
        self.passthru.db_connection = mock.Mock(autospec=True)
        port_patcher = mock.patch.object(self.passthru.db_connection,
                                        'get_port')
        self.port_mock = port_patcher.start()
        node_patcher = mock.patch.object(self.passthru.db_connection,
                                         'get_node')
        self.node_mock = node_patcher.start()
        self.task = FakeTask()
        self.fake_datetime = datetime.datetime(2011, 2, 3, 10, 11)

    def test_validate(self):
        node = FakeNode()
        self.passthru.validate(node)

    def test_validate_bad_params(self):
        node = FakeNode()
        node.driver_info = {}
        self.assertRaises(exception.InvalidParameterValue,
                          self.passthru.validate,
                          node)

    @mock.patch('ironic_teeth_driver.passthru.TeethVendorPassthru'
                '._find_node_by_macs')
    def test_heartbeat_no_uuid(self, find_mock):
        kwargs = {
            'hardware': [
                {
                    'id': 'aa:bb:cc:dd:ee:ff',
                    'type': 'mac_address'
                },
                {
                    'id': 'ff:ee:dd:cc:bb:aa',
                    'type': 'mac_address'
                }

                ]
        }
        expected_node = FakeNode(uuid='heartbeat')
        find_mock.return_value = expected_node

        with tests.mock_now(self.fake_datetime):
            node = self.passthru._heartbeat_no_uuid(FakeTask(), **kwargs)
        self.assertEqual(expected_node, node['node'])

    def test_heartbeat_no_uuid_bad_kwargs(self):
        self.assertRaises(exception.InvalidParameterValue,
                          self.passthru._heartbeat_no_uuid,
                          FakeTask())

    def test_find_ports_by_macs(self):
        fake_port = FakePort()
        self.port_mock.return_value = fake_port

        macs = ['aa:bb:cc:dd:ee:ff']
        ports = self.passthru._find_ports_by_macs(macs)
        self.assertEqual(1, len(ports))
        self.assertEqual(fake_port.uuid, ports[0].uuid)
        self.assertEqual(fake_port.node_id, ports[0].node_id)

    def test_find_ports_by_macs_bad_params(self):
        self.port_mock.side_effect = db_exc.NoResultFound

        macs = ['aa:bb:cc:dd:ee:ff']
        self.assertRaises(exception.IronicException,
                          self.passthru._find_ports_by_macs,
                          macs)

    @mock.patch('ironic.objects.node.Node.get_by_uuid')
    @mock.patch('ironic_teeth_driver.passthru.TeethVendorPassthru'
                '._get_node_id')
    @mock.patch('ironic_teeth_driver.passthru.TeethVendorPassthru'
                '._find_ports_by_macs')
    def test_find_node_by_macs(self, ports_mock, node_id_mock, node_mock):
        ports_mock.return_value = [FakePort()]
        node_id_mock.return_value = 'c3e83a6a-f094-4c55-8480-760a44efffc6'
        fake_node = FakeNode()
        node_mock.return_value = fake_node

        macs = ['aa:bb:cc:dd:ee:ff']
        node = self.passthru._find_node_by_macs(FakeTask(), macs)
        self.assertEqual(fake_node, node)

    @mock.patch('ironic.objects.node.Node.get_by_uuid')
    @mock.patch('ironic_teeth_driver.passthru.TeethVendorPassthru'
                '._get_node_id')
    @mock.patch('ironic_teeth_driver.passthru.TeethVendorPassthru'
                '._find_ports_by_macs')
    def test_find_node_by_macs_bad_params(self, ports_mock, node_id_mock,
                                          node_mock):
        ports_mock.return_value = []
        node_id_mock.return_value = 'fake-uuid'
        node_mock.side_effect = db_exc.NoResultFound()

        macs = ['aa:bb:cc:dd:ee:ff']
        self.assertRaises(exception.IronicException,
                          self.passthru._find_node_by_macs,
                          FakeTask(),
                          macs)

    def test_get_node_id(self):
        fake_port1 = FakePort(node_id='fake-uuid')
        fake_port2 = FakePort(node_id='fake-uuid')

        node_id = self.passthru._get_node_id([fake_port1, fake_port2])
        self.assertEqual(fake_port2.uuid, node_id)

    def test_get_node_id_exception(self):
        fake_port1 = FakePort(node_id='fake-uuid')
        fake_port2 = FakePort(node_id='other-fake-uuid')

        self.assertRaises(exception.IronicException,
                          self.passthru._get_node_id,
                          [fake_port1, fake_port2])

    def test_heartbeat(self):
        task = FakeTask()
        fake_node = FakeNode()
        kwargs = {
            'agent_url': 'http://127.0.0.1:9999/bar'
        }
        with tests.mock_now(self.fake_datetime):
            node = self.passthru._heartbeat(task, fake_node, **kwargs)
        self.assertEqual(self.fake_datetime,
                         node.driver_info['last_heartbeat'])
        self.assertEqual('http://127.0.0.1:9999/bar',
                         node.driver_info['agent_url'])

    def test_heartbeat_bad_params(self):
        task = FakeTask()
        node = FakeNode()
        self.assertRaises(exception.InvalidParameterValue,
                          self.passthru._heartbeat,
                          task=task,
                          node=node)
