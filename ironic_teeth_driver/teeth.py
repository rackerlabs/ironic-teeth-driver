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

    def validate(self, node):
        """Validate the driver-specific git Node deployment info.

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
        image_info = node.instance_info.get('image_info')
        metadata = node.instance_info.get('metadata')
        files = node.instance_info.get('files')

        # Tell the client to run the image with the given args
        client = self._get_client()
        client.prepare_image(node, image_info, metadata, files, wait=True)
        # TODO(pcsforeducation) Switch network here
        client.run_image(node, wait=True)
        # TODO(pcsforeducation) don't return until we have a totally working
        # machine, so we'll need to do some kind of testing here.
        return states.DEPLOYDONE

    def tear_down(self, task, node):
        """Reboot the machine and begin decom.

        When the node reboots, it will check in, see that it is supposed
        to be deleted, and start decom.

        :param task: a TaskManager instance.
        :param node: the Node to act upon.
        :returns: status of the deploy. One of ironic.common.states.
        """
        # Reboot
        manager_utils.node_power_action(task, node, states.REBOOT)
        # TODO(russell_h): resume decom when the agent comes back up
        return states.DELETING

    def prepare(self, task, node):
        """Prepare the deployment environment for this node.

        :param task: a TaskManager instance.
        :param node: the Node for which to prepare a deployment environment
                     on this Conductor.
        """
        # Not implemented. Try to keep as little state in the conductor as
        # possible.
        pass

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
