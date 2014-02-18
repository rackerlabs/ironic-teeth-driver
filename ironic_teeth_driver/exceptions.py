"""
Copyright 2013 Rackspace, Inc.

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
from ironic.openstack.common.gettextutils import _


class UnsupportedContentTypeError(exception.InvalidParameterValue):
    """Error which occurs when a user supplies an unsupported
    `Content-Type` (ie, anything other than `application/json`).
    """
    code = 400
    message = _('Unsupported Content-Type: %(content_type)s.')


class InvalidContentError(exception.InvalidParameterValue):
    """Error which occurs when a user supplies invalid content, either
    because that content cannot be parsed according to the advertised
    `Content-Type`, or due to a content validation error.
    """
    code = 400
    message = _('Invalid request body')


class ChassisAlreadyReservedError(exception.IronicException):
    """Error which occurs when the scheduler recommends a chassis, but
    someone else reserves it first. This should generally be handled
    by requesting another chassis from the scheduler.
    """
    message = _('Chassis %(chassis_id)d already reserved')


class MultipleChassisFound(exception.IronicException):
    """Error when chassis lookup is done by hardware keys,
    and more than one matching chassis is found.
    """
    message = _('Multiple chassis found')
    code = 400


class InsufficientCapacityError(exception.IronicException):
    """Error which occurs when not enough capacity is available to
    fulfill a request.
    """
    message = _('Insufficient capacity')


class AgentNotConnectedError(exception.IronicException):
    """Error which occurs when an RPC call is attempted against a chassis
    for which no agent is connected.
    """
    message = _('Agent not connected for chassis %(chassis_id)d')


class AgentConnectionLostError(exception.IronicException):
    """Error which occurs when an agent's connection is lost while an RPC
    call is in progress.
    """
    message = _('Agent connection lost')


class AgentExecutionError(exception.IronicException):
    """Exception class which represents errors that occurred in the agent."""
    message = _('Error executing command')


class ImageNotFoundError(exception.NotFound):
    """Error which is raised when an image is not found."""
    message = _('Image %(image_id)d not found')


class InvalidParametersError(exception.InvalidParameterValue):
    """Error which is raised for invalid parameters."""
    message = _('Invalid query parameters')


class ObjectCannotBeDeletedError(exception.IronicException):
    """Error which is raised when a consumer attempts to delete an
    objects which can't be deleted. (ex: foreign key constraint)
    """
    message = _('Object %(type)s with id %(id)d cannot be deleted')
    code = 403


class ObjectAlreadyDeletedError(exception.IronicException):
    """Error which is raised when a consumer attempts to delete an object which
    has already been deleted. This error only applies to objects which remain
    user-visible for archival purposes after a DELETE call. If an object has
    been hard deleted, or never existed in the first place (presumably these
    states are indistinguishable to the system) a
    `RequestedObjectNotFoundError` should be used instead.
    """
    message = _('Object %(type)s with id %(id)d already deleted')
    code = 403


class RequestedObjectNotFoundError(exception.NotFound):
    """Error which is returned when a requested object is not found."""
    message = _('Requested object {type} with id {id} not found')
