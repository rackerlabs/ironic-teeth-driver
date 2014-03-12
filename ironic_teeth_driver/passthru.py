import datetime

from ironic.common import exception
from ironic.db.sqlalchemy import api as dbapi
from ironic.drivers import base
from ironic.openstack.common import log

from sqlalchemy.orm.exc import NoResultFound


class TeethVendorPassthru(base.VendorInterface):
    def __init__(self):
        self.routes = {
            'heartbeat': self._heartbeat_no_uuid()
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
        pass

    def driver_vendor_passthru(self, method, **kwargs):
        """
        Given method, route the command to the appropriate
        private function.
        """
        if method not in self.routes:
            raise ValueError('No handler for method {0}'.format(method))
        func = self.routes[method]
        return func(**kwargs)

    def vendor_passthru(self, task, node, **kwargs):
        """A node that knows its uuid should heartbeat to this passthu. It will
        get its node object back, with what Ironic thinks its provision state
        is and the target provision state is.
        """
        # heartbeats with uuid, return the updated node
        node.driver_info['last_heartbeat'] = datetime.datetime.now()
        node.save()
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
            'ipmi_address': OUT_OF_BAND_IP_ADDRESS,
            'agent_url': http://NODE_IP:AGENT_PORT
            'mac_addresses': ['MAC_1', 'MAC_2'...]
        }

        AGENT_PORT defaults to 9999.
        mac_addresses is a list of strings for the non-IPMI ports in the
        server, (the normal network ports). They should be in the format
        "aa:bb:cc:dd:ee:ff".
        """
        if 'agent_url' not in kwargs:
            raise exception.InvalidParameterValue('"agent_url" is a required'
                                                  ' parameter')
        if 'ipmi_address' not in kwargs:
            raise exception.InvalidParameterValue('"ipmi_address" is a required'
                                                  ' parameter')
        if 'mac_addresses' not in kwargs or not kwargs['mac_addresses']:
            raise exception.InvalidParameterValue('"mac_addresses" is a '
                                                  'required parameter and must'
                                                  ' not be empty')

        node = self._find_node_by_macs(kwargs['mac_addresses'])
        node.driver_info['last_heartbeat'] = datetime.datetime.now()
        node.driver_info['agent_url'] = kwargs['agent_url']
        node.instance_info['ipmi_address'] = kwargs['ipmi_address']
        node.save()
        return node

    def _find_node_by_macs(self, mac_addresses):
        """Given a list of MAC addresses, find the ports that match the MACs
        and return the node they are all connected to.

        raises IronicException if the ports point to multiple nodes or no
        nodes.
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
            raise exception.IronicException('None of the provided MAC addresses'
                                            ' match a port.')
        node_id = self._get_node_id(ports)
        try:
            node = self.db_connection.get_node(node_id=node_id)
        except NoResultFound:
            self.LOG.exception('Could not find matching node for the provided '
                               'MACs.')
            raise exception.IronicException('No node matches the given MAC '
                                            'addresses.')
        return node

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
