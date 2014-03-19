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
from ironic.common import utils
from ironic.db.sqlalchemy import api as dbapi
from ironic.drivers import base
from ironic.openstack.common import log

from sqlalchemy.orm.exc import NoResultFound


class TeethVendorPassthru(base.VendorInterface):
    #TODO(pcsforeducation) use MixingVendorInterface when merged
    def __init__(self):
        self.vendor_routes = {
            'heartbeat': self._heartbeat
        }
        self.driver_routes = {
            'lookup': self._heartbeat_no_uuid
        }
        self.db_connection = dbapi.get_backend()
        self.LOG = log.getLogger(__name__)

    def validate(self, node, **kwargs):
        """Validate the driver-specific Node deployment info.

        This method validates whether the 'driver_info' property of the
        supplied node contains the required information for this driver to
        deploy images to the node.

        :param node: a single Node to validate.
        :raises: InvalidParameterValue
        """
        if 'agent_url' not in node.driver_info:
            raise exception.InvalidParameterValue('agent_url is required to '
                                                  'talk to the agent')

    def driver_vendor_passthru(self, method, **kwargs):
        """A node that does not know its UUID should POST to this method.
        Given method, route the command to the appropriate private function.
        """
        if method not in self.driver_routes:
            raise ValueError('No handler for method {0}'.format(method))
        func = self.driver_routes[method]
        return func(**kwargs)

    def vendor_passthru(self, task, node, **kwargs):
        """A node that knows its UUID should heartbeat to this passthu. It will
        get its node object back, with what Ironic thinks its provision state
        is and the target provision state is.
        """
        if 'method' not in kwargs:
            raise ValueError('No method provided in kwargs')
        method = kwargs['method']
        if method not in self.vendor_routes:
            raise ValueError('No handler for method {0}'.format(method))
        func = self.vendor_routes[method]
        return func(task, node, **kwargs)

    def _heartbeat(self, task, node, **kwargs):
        """Method for agent to periodically check in. The agent should be
        sending its agent_url (so Ironic can talk back) as a kwarg.

        kwargs should have the following format:
        {
            'agent_url': 'http://AGENT_HOST:AGENT_PORT'
        }
                AGENT_PORT defaults to 9999.
        """
        if 'agent_url' not in kwargs:
            raise exception.InvalidParameterValue('"agent_url" is a required'
                                                  ' parameter')
        node.driver_info['last_heartbeat'] = datetime.datetime.now()
        node.driver_info['agent_url'] = kwargs['agent_url']
        node.save(task)
        return node

    def _heartbeat_no_uuid(self, **kwargs):
        """Method to be called the first time a ramdisk agent checks in. This
        can be because this is a node just entering decom or a node that
        rebooted for some reason. We will use the mac addresses listed in the
        kwargs to find the matching node, then return the node object to the
        agent. The agent can that use that UUID to use the normal vendor
        passthru method.

        Currently, we don't handle the instance where the agent doesn't have
        a matching node (i.e. a brand new, never been in Ironic node).

        kwargs should have the following format:
        {
            hardware: [
                {
                    'id': 'aa:bb:cc:dd:ee:ff',
                    'type': 'mac_address'
                },
                {
                    'id': '00:11:22:33:44:55',
                    'type': 'mac_address'
                }
            ], ...
        }

        hardware is a list of dicts with id being the actual mac address,
        with type 'mac_address' for the non-IPMI ports in the
        server, (the normal network ports). They should be in the format
        "aa:bb:cc:dd:ee:ff".
        """
        if 'hardware' not in kwargs or not kwargs['hardware']:
            raise exception.InvalidParameterValue('"hardware" is a '
                                                  'required parameter and must'
                                                  ' not be empty')

        # Find the address from the hardware list
        mac_addresses = []
        for hardware in kwargs['hardware']:
            if 'id' not in hardware or 'type' not in hardware:
                self.LOG.warning(_('Malformed hardware entry %s') % hardware)
                continue
            if 'type' == 'mac_address':
                try:
                    mac = utils.validate_and_normalize_mac(hardware['id'])
                except exception.InvalidMAC:
                    self.LOG.warning(_('Malformed MAC in hardware entry %s.')
                                     % hardware)
                    continue
                mac_addresses.append(mac)

        node = self._find_node_by_macs(mac_addresses)
        return node

    def _find_node_by_macs(self, mac_addresses):
        """Given a list of MAC addresses, find the ports that match the MACs
        and return the node they are all connected to.

        raises IronicException if the ports point to multiple nodes or no
        nodes.
        """
        ports = self._find_ports_by_macs(mac_addresses)
        node_id = self._get_node_id(ports)
        try:
            node = self.db_connection.get_node(node_id=node_id)
        except NoResultFound:
            self.LOG.exception('Could not find matching node for the provided '
                               'MACs.')
            raise exception.IronicException('No node matches the given MAC '
                                            'addresses.')
        return node

    def _find_ports_by_macs(self, mac_addresses):
        """Given a list of MAC addresses, find the ports that mach the MACs
        and return them as a list of Port objects.

        raises IroniceException if the no matching ports are found.
        """
        ports = []
        for mac in mac_addresses:
            # Will do a search by mac if the mac isn't malformed
            try:
                port = self.db_connection.get_port(port_id=mac)
                ports.append(port)
            except NoResultFound:
                # TODO(pcsforeducation) is this the right log level?
                self.LOG.exception('MAC address {0} attached to node not in '
                                   'database'.format(mac))

        if not ports:
            raise exception.IronicException('None of the provided MAC '
                                            'addresses match a port.')
        return ports

    def _get_node_id(self, ports):
        """Given a list of ports, either return the node_id they all share or
        raise a ValueError if there are multiple node_ids (indicating these
        ports are connected to multiple nodes)
        """
        # See if all the ports point to the same node
        node_ids = set()
        for port in ports:
            node_ids.add(port.node_id)
        if len(node_ids) > 1:
            raise exception.IronicException('Ports matching mac addresses '
                                            'match multiple nodes.')
        return node_ids.pop()
