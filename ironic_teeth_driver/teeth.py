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
from ironic.conductor import utils as manager_utils
from ironic.drivers import base
from ironic_teeth_driver import rest

"""States:

BUILDING: caching
PREPARED: image cached, ready for deploy

DEPLOYING: applying instance definition (SSH pub keys, etc), rebooting
ACTIVE: ready to be used

DELETING: doing decom
DELETED: decom finished
"""


class TeethDeploy(base.DeployInterface):
    """Interface for deploy-related actions."""

    def _get_client(self):
        # TODO(pcsforeducation) add config
        client = rest.RESTAgentClient({})
        return client

    def validate(self, task, node):
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

    def deploy(self, task, node):
        """Perform a deployment to a node.

        Perform the necessary work to deploy an image onto the specified node.
        This method will be called after prepare(), which may have already
        performed any preparatory steps, such as pre-caching some data for the
        node.

        :param task: a TaskManager instance.
        :param node: the Node to act upon.
        :returns: status of the deploy. One of ironic.common.states.
        """
        self.validate(task, node)

        image_info = node.driver_info.get('image_info', None)
        metadata = node.driver_info.get('metadata', None)
        files = node.driver_info.get('files', None)
        if image_info is None:
            raise exception.InvalidParameterValue('image_info required for '
                                                  'deploy.')
        if metadata is None:
            raise exception.InvalidParameterValue('metadata required for '
                                                  'deploy.')
        if files is None:
            raise exception.InvalidParameterValue('files required for deploy.')

        node.provision_state = states.DEPLOYING
        node.target_provision_state = states.DEPLOYDONE
        node.save(task.context)

        # Tell the client to run the image with the given args
        client = self._get_client()
        client.prepare_image(node, image_info, metadata, files)
        # TODO(pcsforeducation) Switch network here
        client.run_image(node)
        return states.DEPLOYING

    def tear_down(self, task, node):
        """Reboot the machine and begin decom.

        When the node reboots, it will check in, see that it is supposed
        to be deleted, and start decom.

        :param task: a TaskManager instance.
        :param node: the Node to act upon.
        :returns: status of the deploy. One of ironic.common.states.
        """
        self.validate(task, node)

        # Set the node to decom in the DB
        node.provision_state = states.DELETING
        node.target_provision_state = states.DELETED
        node.save(task.context)

        # Reboot
        manager_utils.node_power_action(task, node, states.REBOOT)
        return states.DELETING

    def prepare(self, task, node):
        """Prepare the deployment environment for this node.

        The method must be idempotent. It will be called right before
        `deploy`, which we will ignore.

        Cache the image stored in node.driver_info['image_id']


        :param task: a TaskManager instance.
        :param node: the Node for which to prepare a deployment environment
                     on this Conductor.
        """

        self.validate(task, node)

        # Set the node to cache in the DB
        image_info = node.driver_info.get('image_info', None)
        if image_info is None:
            raise exception.InvalidParameterValue('image_info required '
                                                  'in driver_info.')
        node.provision_state = states.BUILDING

        #TODO(pcsforeducation) replace 'preparing' with states.PREPARING
        # when the merge is done upstream
        node.target_provision_state = 'preparing'
        node.save(task.context)

        # Tell the agent to cache the image
        client = self._get_client()
        client.cache_image(node, image_info)
        #TODO(pcsforeducation) replace 'preparing' with states.PREPARING
        # when the merge is done upstream
        return 'preparing'

    def clean_up(self, task, node):
        """Clean up the deployment environment for this node.

        If preparation of the deployment environment ahead of time is possible,
        this method should be implemented by the driver. It should erase
        anything cached by the `prepare` method.

        If implemented, this method must be idempotent. It may be called
        multiple times for the same node on the same conductor, and it may be
        called by multiple conductors in parallel. Therefore, it must not
        require an exclusive lock.

        This method is called before `tear_down`.

        :param task: a TaskManager instance.
        :param node: the Node whose deployment environment should be cleaned up
                     on this Conductor.
        """
        # Not implemented. tear_down does everything.
        pass

    def take_over(self, task, node):
        """Take over management of this node from a dead conductor.

        If conductors' hosts maintain a static relationship to nodes, this
        method should be implemented by the driver to allow conductors to
        perform the necessary work during the remapping of nodes to conductors
        when a conductor joins or leaves the cluster.

        For example, the PXE driver has an external dependency:
            Neutron must forward DHCP BOOT requests to a conductor which has
            prepared the tftpboot environment for the given node. When a
            conductor goes offline, another conductor must change this setting
            in Neutron as part of remapping that node's control to itself.
            This is performed within the `takeover` method.

        :param task: a TaskManager instance.
        :param node: the Node which is now being managed by this Conductor.
        """
        # Unnecessary. Trying to keep everything as stateless as possible.
        pass
