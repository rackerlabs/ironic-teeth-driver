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
import mock
import unittest


class TeethMockTestUtilities(unittest.TestCase):
    def setUp(self):
        self._patches = collections.defaultdict(dict)
        self.patcher = None

    def tearDown(self):
        if self.patcher:
            self.patcher.stop()

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
            self.patcher = patcher

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
