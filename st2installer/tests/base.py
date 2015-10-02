import os
import unittest

import mock
from pecan import set_config

from st2installer.controllers.root import RootController


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        super(BaseTestCase, self).setUp()

        self.root_controller = RootController()
        self.keypair_controller = self.root_controller.keypair

        # Make sure the lock doesnt exist
        self.removeLock()

        # Mock puppet check for tests
        RootController.puppet_check = mock.Mock()
        RootController.puppet_check.return_value = False

        # Travis fix
        self.root_controller.path = 'tmp/hieradata/'
        self.root_controller.command = '/bin/echo testing'

    def tearDown(self):
        super(BaseTestCase, self).tearDown()
        set_config({}, overwrite=True)
        self.removeLock()

    def setLock(self):
        self.root_controller.lock()

    def removeLock(self):
        if os.path.isfile(self.root_controller.lockfile):
            os.remove(self.root_controller.lockfile)
