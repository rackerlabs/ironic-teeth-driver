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
from ironic.drivers import base


class TeethDeploy(base.DeployInterface):
    """Interface for deploy-related actions."""

    def validate(self, node):
        """Validate the driver-specific Node deployment info.

        This method validates whether the 'driver_info' property of the
        supplied node contains the required information for this driver to
        deploy images to the node.

        :param node: a single Node to validate.
        :raises: InvalidParameterValue
        """

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

    def tear_down(self, task, node):
        """Tear down a previous deployment.

        Given a node that has been previously deployed to,
        do all cleanup and tear down necessary to "un-deploy" that node.

        :param task: a TaskManager instance.
        :param node: the Node to act upon.
        :returns: status of the deploy. One of ironic.common.states.
        """

    def prepare(self, task, node):
        """Prepare the deployment environment for this node.

        If preparation of the deployment environment ahead of time is possible,
        this method should be implemented by the driver.

        If implemented, this method must be idempotent. It may be called
        multiple times for the same node on the same conductor, and it may be
        called by multiple conductors in parallel. Therefore, it must not
        require an exclusive lock.

        This method is called before `deploy`.

        :param task: a TaskManager instance.
        :param node: the Node for which to prepare a deployment environment
                     on this Conductor.
        """

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


class TeethConsole(object):
    """Interface for console-related actions."""

    def validate(self, node):
        """Validate the driver-specific Node console info.

        This method validates whether the 'driver_info' property of the
        supplied node contains the required information for this driver to
        provide console access to the Node.

        :param node: a single Node to validate.
        :raises: InvalidParameterValue
        """

    def start_console(self, task, node):
        """Start a remote console for the node.

        TODO
        """

    def stop_console(self, task, node):
        """Stop the remote console session for the node.

        TODO
        """


class TeethRescue(base.RescueInterface):
    """Interface for rescue-related actions."""

    def validate(self, node):
        """Validate the rescue info stored in the node' properties.

        :param node: a single Node to validate.
        :raises: InvalidParameterValue
        """

    def rescue(self, task, node):
        """Boot the node into a rescue environment.

        TODO
        """

    def unrescue(self, task, node):
        """Tear down the rescue environment, and return to normal.

        TODO
        """


class VendorPassthrough(base.VendorInterface):
    """Interface for all vendor passthru functionality.

    Additional vendor- or driver-specific capabilities should be implemented as
    private methods and invoked from vendor_passthru().
    """

    def validate(self, node, **kwargs):
        """Validate vendor-specific actions.

        :param node: a single Node.
        :param kwargs: info for action.
        :raises: InvalidParameterValue
        """

    def vendor_passthru(self, task, node, **kwargs):
        """Receive requests for vendor-specific actions.

        :param task: a task from TaskManager.
        :param node: a single Node.
        :param kwargs: info for action.
        """
