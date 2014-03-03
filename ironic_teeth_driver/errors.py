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

from ironic_teeth_driver import encoding


class RESTError(Exception, encoding.Serializable):
    """Base class for errors generated in teeth."""
    message = 'An error occurred'
    details = 'An unexpected error occurred. Please try back later.'
    status_code = 500

    def serialize(self, view):
        """Turn a RESTError into a dict."""
        return collections.OrderedDict([
            ('type', self.__class__.__name__),
            ('code', self.status_code),
            ('message', self.message),
            ('details', self.details),
        ])


class UnsupportedContentTypeError(RESTError):
    """Error which occurs when a user supplies an unsupported
    `Content-Type` (ie, anything other than `application/json`).
    """
    message = 'Unsupported Content-Type'
    status_code = 400

    def __init__(self, content_type):
        self.details = 'Content-Type "{content_type}" is not supported'
        self.details = self.details.format(content_type=content_type)


class InvalidContentError(RESTError):
    """Error which occurs when a user supplies invalid content, either
    because that content cannot be parsed according to the advertised
    `Content-Type`, or due to a content validation error.
    """
    message = 'Invalid request body'
    status_code = 400

    def __init__(self, details):
        self.details = details


class NotFound(RESTError):
    """Error which occurs when a user supplies invalid content, either
    because that content cannot be parsed according to the advertised
    `Content-Type`, or due to a content validation error.
    """
    message = 'Not found'
    status_code = 404
    details = 'The requested URL was not found.'


class ChassisAlreadyReservedError(RESTError):
    """Error which occurs when the scheduler recommends a chassis, but
    someone else reserves it first. This should generally be handled
    by requesting another chassis from the scheduler.
    """
    message = 'Chassis already reserved'

    def __init__(self, chassis):
        self.details = 'Chassis {chassis_id} is already reserved.'.format(
            chassis_id=str(chassis.id))


class InsufficientCapacityError(RESTError):
    """Error which occurs when not enough capacity is available to
    fulfill a request.
    """
    message = 'Insufficient capacity'
    details = ('There was not enough capacity available to fulfill your '
               'request. Please try back later.')


class AgentNotConnectedError(RESTError):
    """Error which occurs when an RPC call is attempted against a chassis
    for which no agent is connected.
    """
    message = 'Agent not connected'

    def __init__(self, chassis_id):
        self.details = 'No agent is connected for chassis {chassis_id}'
        self.details = self.details.format(chassis_id=chassis_id)


class AgentConnectionLostError(RESTError):
    """Error which occurs when an agent's connection is lsot while an RPC
    call is in progress.
    """
    message = 'Agent connection lost'
    details = 'The agent\'s connection was lost while performing your request.'


class AgentExecutionError(RESTError):
    """Exception class which represents errors that occurred in the agent."""
    message = 'Error executing command'

    def __init__(self, details):
        self.details = details


class ImageNotFoundError(InvalidContentError):
    """Error which is raised when an image is not found."""
    message = 'Image not found'

    def __init__(self, image_id):
        msg = 'Image "{image_id}" not found.'.format(image_id=str(image_id))
        super(ImageNotFoundError, self).__init__(msg)


class InvalidParametersError(RESTError):
    """Error which is raised for invalid parameters."""
    message = 'Invalid query parameters'
    status_code = 400

    def __init__(self, details):
        self.details = details


class ObjectCannotBeDeletedError(RESTError):
    """Error which is raised when a consumer attempts to delete an
    objects which can't be deleted. (ex: foreign key constraint)
    """
    message = 'Object cannot be deleted'
    status_code = 403

    def __init__(self, cls, id, details=None):
        super(ObjectCannotBeDeletedError, self).__init__(cls, id)
        default_details = '{type} with id {id} cannot be deleted.'.format(
            type=cls.__name__, id=id)
        self.details = details if details else default_details


class ObjectAlreadyDeletedError(RESTError):
    """Error which is raised when a consumer attempts to delete an object which
    has already been deleted. This error only applies to objects which remain
    user-visible for archival purposes after a DELETE call. If an object has
    been hard deleted, or never existed in the first place (presumably these
    states are indistinguishable to the system) a
    `RequestedObjectNotFoundError` should be used instead.
    """
    message = 'Object already deleted'
    status_code = 403

    def __init__(self, cls, id):
        super(ObjectAlreadyDeletedError, self).__init__(cls, id)
        self.details = '{type} with id {id} has already been deleted.'.format(
            type=cls.__name__, id=id)


class RequestedObjectNotFoundError(RESTError):
    """Error which is returned when a requested object is not found."""
    message = 'Requested object not found'
    status_code = 404

    def __init__(self, cls, id):
        super(RequestedObjectNotFoundError, self).__init__(cls, id)
        self.details = '{type} with id {id} not found.'.format(
            type=cls.__name__, id=id)


class MultipleChassisFound(RESTError):
    """Error when chassis lookup is done by hardware keys,
    and more than one matching chassis is found.
    """
    message = 'Multiple chassis found'
    status_code = 400

    def __init__(self, hardware):
        self.details = 'Multiple chassis with hardware {} were found.'
        self.details = self.details.format(hardware)
