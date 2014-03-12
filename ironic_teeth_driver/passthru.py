from ironic.common import exception
from ironic.db.sqlalchemy import api as dbapi
from ironic.drivers import base


class TeethVendorPassthru(base.VendorInterface):
    def __init__(self):
        self.routes = {
            'heartbeat': self._heartbeat
        }
        self.db_connection = dbapi.get_backend()

    def validate(self, node, **kwargs):
        """Validate the driver-specific Node deployment info.

        This method validates whether the 'driver_info' property of the
        supplied node contains the required information for this driver to
        deploy images to the node.

        :param node: a single Node to validate.
        :raises: InvalidParameterValue
        """
        if 'agent_url' not in node.driver_info:
            raise exception.InvalidParameterValue('Nodes require an '
                                                  'agent_url.')
        if node.instance_info is not None:
            if 'image_info' not in node.instance_info:
                raise exception.InvalidParameterValue('Nodes require '
                                                      'image_info.')
            if 'metadata' not in node.instance_info:
                raise exception.InvalidParameterValue('metadata in '
                                                      'deploy_data required '
                                                      'for deploy.')
            if 'files' not in node.instance_info:
                raise exception.InvalidParameterValue('files in deploy_data '
                                                      'required for deploy.')

    def vendor_passthru(self, **kwargs):
        """
        Given 'method' in kwargs, route the command to the appropriate
        private function.
        """
        if 'method' not in kwargs:
            raise TypeError("passthru must be called with a method "
                            "argument.")
        # Call the function matching the method param
        # Call the function matching the method param
        func = self.routes[kwargs['method']]
        func(**kwargs)

    def _heartbeat(self, **kwargs):
        """Method for ramdisk agent checking in

        There are 3 possibilities for the nodes state:
        * first time the node is ever heartbeating: add the node
        * node just rebooted (either deliberately moving to decom,
        or unexpectedly, doesn't know its uuid yet): tell it what its target
        state is
        * node is checking in with uuid while currently doing decom/standby:
        update db so we can know when it dies.

        If the node does not provide a UUID, the node is created in the DB
        with the given information.

        When a node is creating itself, it should provide its IPMI address as
        {'instance_info': {'ipmi_address': ADDRESS}}

        Note: this is a security risk. If a malicious node heartbeats,
        it will be considered a valid node and exist in the DB.
        """
        if 'uuid' not in kwargs:
            if 'mac_addresses' not in kwargs:
                raise ValueError("Ramdisk must provide a list of "
                                 "mac_addresses of its ports")
            # See if node is already in DB by checking the provided mac
            # addresses
            # This isn't implemented, and I don't think this the correct
            # call. We probably need to implement get_port_by_mac
            ports = []
            for mac in kwargs['mac_addresses']:
                port = self.db_connection.get_port_by_vif(mac)
                if port is not None:
                    ports.append(port)
            if ports == []:
                # Nothing in DB. Create new node from provided info
                node = self.db_connection.create_node(kwargs)
            else:
                # TODO error handling for two ports on different nodes
                node = self.db_connection.get_node(ports[0].node_id)
            return node
        else:
            # Send back the node information, which will tell the node its
            # current provision_state and target_provision_state.
            node = self.db_connection.get_node(kwargs['uuid'])
            return node
