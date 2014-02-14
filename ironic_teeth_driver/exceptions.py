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

import collections

from ironic.common import exception
from ironic.openstack.common.gettextutils import _


class RESTError(exception.IronicException):
    """Base class for errors generated in teeth."""
    message = _('An error occurred')
    code = 500
    details = _('An unexpected error occurred. Please try back later.')

    def serialize(self):
        """Turn a RESTError into a dict."""
        return collections.OrderedDict([
            ('type', self.__class__.__name__),
            ('code', self.code),
            ('message', self.message),
            ('details', self.details),
        ])


class UnsupportedContentTypeError(RESTError):
    """Error which occurs when a user supplies an unsupported
    `Content-Type` (ie, anything other than `application/json`).
    """
    message = _('Unsupported Content-Type')
    code = 400

    def __init__(self, content_type):
        self.details = 'Content-Type "{content_type}" is not supported'
        self.details = _(self.details.format(content_type=content_type))


class InvalidContentError(RESTError):
    """Error which occurs when a user supplies invalid content, either
    because that content cannot be parsed according to the advertised
    `Content-Type`, or due to a content validation error.
    """
    message = _('Invalid request body')
    code = 400

    def __init__(self, details):
        self.details = _(details)


class NotFound(RESTError):
    """Error which occurs when a user supplies invalid content, either
    because that content cannot be parsed according to the advertised
    `Content-Type`, or due to a content validation error.
    """
    message = _('Not found')
    code = 404
    details = _('The requested URL was not found.')


class ChassisAlreadyReservedError(RESTError):
    """Error which occurs when the scheduler recommends a chassis, but
    someone else reserves it first. This should generally be handled
    by requesting another chassis from the scheduler.
    """
    message = _('Chassis already reserved')

    def __init__(self, chassis):
        self.details = _('Chassis {chassis_id} is already reserved.'.format(
            chassis_id=str(chassis.id)))


class InsufficientCapacityError(RESTError):
    """Error which occurs when not enough capacity is available to
    fulfill a request.
    """
    message = _('Insufficient capacity')
    details = _('There was not enough capacity available to fulfill your '
               'request. Please try back later.')


class AgentNotConnectedError(RESTError):
    """Error which occurs when an RPC call is attempted against a chassis
    for which no agent is connected.
    """
    message = _('Agent not connected')

    def __init__(self, chassis_id):
        self.details = 'No agent is connected for chassis {chassis_id}'
        self.details = _(self.details.format(chassis_id=chassis_id))


class AgentConnectionLostError(RESTError):
    """Error which occurs when an agent's connection is lsot while an RPC
    call is in progress.
    """
    message = _('Agent connection lost')
    details = _('The agent\'s connection was lost while performing your ' \
                 'request.')


class AgentExecutionError(RESTError):
    """Exception class which represents errors that occurred in the agent."""
    message = _('Error executing command')

    def __init__(self, details):
        self.details = _(details)


class ImageNotFoundError(InvalidContentError):
    """Error which is raised when an image is not found."""
    message = _('Image not found')

    def __init__(self, image_id):
        msg = _('Image "{image_id}" not found.'.format(image_id=str(image_id)))
        super(ImageNotFoundError, self).__init__(msg)


class InvalidParametersError(RESTError):
    """Error which is raised for invalid parameters."""
    message = _('Invalid query parameters')
    code = 400

    def __init__(self, details):
        self.details = _(details)


class ObjectCannotBeDeletedError(RESTError):
    """Error which is raised when a consumer attempts to delete an
    objects which can't be deleted. (ex: foreign key constraint)
    """
    message = _('Object cannot be deleted')
    code = 403

    def __init__(self, cls, id, details=None):
        super(ObjectCannotBeDeletedError, self).__init__(cls, id)
        default_details = '{type} with id {id} cannot be deleted.'.format(
            type=cls.__name__, id=id)
        self.details = _(details if details else default_details)


class ObjectAlreadyDeletedError(RESTError):
    """Error which is raised when a consumer attempts to delete an object which
    has already been deleted. This error only applies to objects which remain
    user-visible for archival purposes after a DELETE call. If an object has
    been hard deleted, or never existed in the first place (presumably these
    states are indistinguishable to the system) a
    `RequestedObjectNotFoundError` should be used instead.
    """
    message = _('Object already deleted')
    code = 403

    def __init__(self, cls, id):
        super(ObjectAlreadyDeletedError, self).__init__(cls, id)
        self.details = _('{type} with id {id} has already been deleted.'
                         .format(type=cls.__name__, id=id))


class RequestedObjectNotFoundError(RESTError):
    """Error which is returned when a requested object is not found."""
    message = _('Requested object not found')
    code = 404

    def __init__(self, cls, id):
        super(RequestedObjectNotFoundError, self).__init__(cls, id)
        self.details = _('{type} with id {id} not found.'.format(
            type=cls.__name__, id=id))


class MultipleChassisFound(RESTError):
    """Error when chassis lookup is done by hardware keys,
    and more than one matching chassis is found.
    """
    message = _('Multiple chassis found')
    code = 400

    def __init__(self, hardware):
        self.details = 'Multiple chassis with hardware {} were found.'
        self.details = _(self.details.format(hardware))
