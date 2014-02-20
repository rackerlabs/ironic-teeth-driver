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
from ironic.openstack.common import jsonutils
from ironic.openstack.common import log

import json
import requests
import uuid


class RESTAgentClient(object):
    """Client for interacting with nodes via a REST API."""
    def __init__(self):
        self.session = requests.Session()
        self.log = log.getLogger(__name__)

    def _get_command_url(self, node):
        return '{}/v1/commands'.format(node.driver_info['agent_url'])

    def _get_command_body(self, method, params):
        return jsonutils.dumps({
            'name': method,
            'params': params,
        })

    def _command(self, node, method, params):
        url = self._get_command_url(node)
        body = self._get_command_body(method, params)
        headers = {
            'Content-Type': 'application/json'
        }
        response = self.session.post(url, data=body, headers=headers)

        # TODO(russellhaering): real error handling
        return json.loads(response.text)

    def new_task_id(self):
        """Generate a serialized UUID for use as a task ID."""
        return str(uuid.uuid4())

    def cache_image(self, node, image_info):
        """Attempt to cache the specified image."""
        self.log.debug('Caching image {image} on node {node}.'.format(
                       image=image_info,
                       node=node.driver_info['agent_url']))
        return self._command(node, 'standby.cache_image', {
            'task_id': self.new_task_id(),
            'image_info': image_info,
        })

    def prepare_image(self, node, image_info, metadata, files):
        """Call the `prepare_image` method on the node."""
        self.log.debug('Preparing image {image} on node {node}.'.format(
                       image=image_info.get('image_id'),
                       node=node.driver_info['agent_url']))
        return self._command(node, 'standby.prepare_image', {
            'image_info': image_info,
            'metadata': metadata,
            'files': files,
            'task_id': self.new_task_id(),
        })

    #TODO(pcsforeducation) match agent function def to this.
    def run_image(self, node):
        """Run the specified image."""
        # self.log.debug('Running image {image} on node {node}.')
        return self._command(node, 'standby.run_image', {
            'task_id': self.new_task_id()
        })

    def secure_drives(self, node, drives, key):
        """Secures given drives with given key."""
        self.log.info('Securing drives {drives} for node {node}'.format(
                      drives=drives,
                      node=node.driver_info['agent_url']))
        return self._command(node, 'decom.secure_drives', {
            'drives': drives,
            'key': key,
        })

    def erase_drives(self, node, drives, key):
        """Erases given drives."""
        self.log.info('Erasing drives {drives} for node {node}'.format(
                      drives=drives,
                      node=node.driver_info['agent_url']))
        return self._command(node, 'decom.erase_drives', {
            'drives': drives,
            'key': key,
        })
