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
import collections
import json
import mock
import unittest

from werkzeug import test
from werkzeug import wrappers


class TeethMockTestUtilities(unittest.TestCase):

    def setUp(self):
        self._patches = collections.defaultdict(dict)

    def _get_env_builder(self, method, path, data=None, query=None):
        if data:
            data = json.dumps(data)

        # makes remote_addr work correctly
        environ_base = {'REMOTE_ADDR': '127.0.0.1'}

        return test.EnvironBuilder(method=method,
                                   path=path,
                                   data=data,
                                   content_type='application/json',
                                   query_string=query,
                                   environ_base=environ_base)

    def build_request(self, method, path, data=None, query=None):
        env_builder = self._get_env_builder(method, path, data, query)
        return env_builder.get_request(wrappers.BaseRequest)

    def make_request(self, method, path, data=None, query=None):
        client = test.Client(self.api, wrappers.BaseResponse)
        return client.open(self._get_env_builder(method, path, data, query))

    def _mock_class(self, cls, return_value=None, side_effect=None,
                    autospec=False):
        """Patches a class wholesale.

        Args:
            cls: the class to patch.
        Returns:
            a Mock() instance
        """
        if cls not in self._patches:
            if isinstance(cls, basestring):
                patcher = mock.patch(cls, autospec=autospec)
            else:
                patcher = mock.patch(cls.__module__ + '.' + cls.__name__)
            self._patches[cls] = patcher.start().return_value
            self.addCleanup(patcher.stop)

        m = self.get_mock(cls)
        if return_value:
            m.return_value = return_value
        if side_effect:
            m.side_effect = side_effect
        return m

    def _mock_attr(self, cls, attr, return_value=None, side_effect=None,
                   autospec=False):
        """Patches an attribute of a class.

        Args:
            cls: the class to patch.
            attr: the attribute to patch ("some_method",
                    "some_object.some_method", etc)
            return_value: optional return_value of the mock
            side_effect: option side_effect of the mock
        Returns:
            a Mock() instance
        """
        patcher = mock.patch.object(cls, attr, autospec=autospec)
        self._patches[cls][attr] = patcher.start()
        self.addCleanup(patcher.stop)

        m = self.get_mock(cls, attr)
        if return_value:
            m.return_value = return_value
        if side_effect:
            m.side_effect = side_effect
        return m

    def get_mock(self, cls, attr=None):
        """Returns a previously added mock.

        Args:
            cls: the class to patch.
            attr: the attribute to fetch
        Returns:
            a Mock() instance
        """
        if attr:
            return self._patches[cls][attr]
        else:
            return self._patches[cls]
