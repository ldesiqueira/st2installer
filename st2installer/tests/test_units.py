import os
from st2installer.controllers.root import RootController

from st2installer.tests.base import BaseTestCase


class MainUnits(BaseTestCase):
    def get_keypair(self, type, valid):
        path = os.path.dirname(__file__)
        valid_string = ('good' if valid else 'bad')
        public_extension = ('pub' if type is 'ssh' else 'crt')
        with open(path+('/%s-%s.key') % (type, valid_string), 'r') as private_file:
            private = private_file.read()
        with open(path+('/%s-%s.%s') % (type, valid_string, public_extension), 'r') as public_file:
            public = public_file.read()
        return (private, public)

    def test_temp_files_are_writable(self):
        temp_dir = '/tmp'
        temp_files = [
            self.keypair_controller.privatefile,
            self.keypair_controller.publicfile,
            self.keypair_controller.diff_output,
            self.root_controller.output,
            self.root_controller.lockfile
        ]
        temp_writable = os.access(temp_dir, os.W_OK)
        for file in temp_files:
            file_exists = os.path.isfile(file)
            file_writable = os.access(file, os.W_OK)
            self.assertTrue((file_exists and file_writable) or temp_writable)

    def test_config_is_writable(self):
        self.assertTrue(os.path.isdir(self.root_controller.path))

        config = "%s%s" % (self.root_controller.path, self.root_controller.configname)
        config_exists = os.path.isfile(config)
        config_writable = os.access(config, os.W_OK)
        path_writable = os.access(self.root_controller.path, os.W_OK)

        self.assertTrue((config_exists and config_writable) or path_writable)

    def test_diff_scripts_are_executable(self):
        self.assertTrue(self.keypair_controller.ssh_diff, os.X_OK)
        self.assertTrue(self.keypair_controller.ssl_diff, os.X_OK)

    def test_installer_locking_works(self):
        self.root_controller.lock()
        self.assertTrue(self.root_controller.is_locked())

    def test_ssh_keypairs_are_generated_correctly(self):
        keypair = self.keypair_controller.keygen()
        keypair_valid = self.keypair_controller.compare(self.keypair_controller.ssh_diff,
                                                        keypair['private'],
                                                        'ssh-rsa ' + keypair['public'])
        self.assertEqual('0\n', keypair_valid)

    def test_good_ssh_keys_evaluate_correctly(self):
        (private, public) = self.get_keypair('ssh', True)
        keypair_valid = self.keypair_controller.compare(self.keypair_controller.ssh_diff,
                                                        private,
                                                        public)
        self.assertEqual('0\n', keypair_valid)


    def test_bad_ssh_keys_fail(self):
        (private, public) = self.get_keypair('ssh', False)
        keypair_valid = self.keypair_controller.compare(self.keypair_controller.ssh_diff,
                                                        private,
                                                        public)
        self.assertNotEqual('0\n', keypair_valid)

    def test_good_ssl_keys_evaluate_correctly(self):
        (private, public) = self.get_keypair('ssl', True)
        keypair_valid = self.keypair_controller.compare(self.keypair_controller.ssl_diff,
                                                        private,
                                                        public)
        self.assertEqual('0\n', keypair_valid)

    def test_bad_ssl_keys_fail(self):
        (private, public) = self.get_keypair('ssl', False)
        keypair_valid = self.keypair_controller.compare(self.keypair_controller.ssl_diff,
                                                        private,
                                                        public)
        self.assertNotEqual('0\n', keypair_valid)
