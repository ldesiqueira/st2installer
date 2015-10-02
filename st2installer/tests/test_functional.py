from unittest import TestCase
from st2installer.controllers.root import RootController
from st2installer.controllers.keypair import KeypairController
from pecan import set_config
from pecan.testing import load_test_app
from copy import copy
import os
import re


class FunctionalTest(TestCase):

    def setUp(self):
        self.app = load_test_app(os.path.join(
            os.path.dirname(__file__),
            'config.py'
        ))
        self.keypair_controller = KeypairController()
        self.root_controller = RootController()
        self.public_regex = re.compile("^ssh-rsa AAAA[0-9A-Za-z+/]+[=]{0,3}( ([^@]+@[^@]+))?$")
        self.private_regex = re.compile("^-----BEGIN RSA PRIVATE KEY-----.*-----END RSA PRIVATE KEY-----$", re.DOTALL)
        self.was_locked = os.path.isfile(self.root_controller.lockfile)
        self.default_post = {
            'hostname': 'localhost-test',
            'check-chatops': '1',
            'hubot-password': 'aF8l5rddf8sBKe6aWYTAZNwo4V4R8vCK',
            'admin-username': 'admin',
            'password-1': 'adminpass1',
            'password-2': 'adminpass1',
            'username': 'stanley',
            'anon-data': '1',
            'chatops': 'slack',
            'selfsigned': '1',
            'sshgen': '1',
            'slack-token': 'slackapi'
        }
        self.removeLock()

        ssh_keys = self.keypair_controller.keygen()
        self.default_post['gen-public'] = ssh_keys['public']
        self.default_post['gen-private'] = ssh_keys['private']

        # Travis fix
        self.root_controller.path = 'tmp/hieradata/'
        self.root_controller.command = '/bin/echo testing'

    def setLock(self):
        self.root_controller.lock()

    def removeLock(self):
        if os.path.isfile(self.root_controller.lockfile):
            os.remove(self.root_controller.lockfile)

    def get_key_filename(self, type, key, valid):
        path = os.path.dirname(__file__)
        valid_string = ('good' if valid else 'bad')
        public_extension = ('pub' if type is 'ssh' else 'crt')
        if key == 'private':
            return path+('/%s-%s.key') % (type, valid_string)
        if key == 'public':
            return path+('/%s-%s.%s') % (type, valid_string, public_extension)

    def tearDown(self):
        set_config({}, overwrite=True)
        if not self.was_locked and os.path.isfile(self.root_controller.lockfile):
            os.remove(self.root_controller.lockfile)

    def test_main_page(self):
        response = self.app.get('/')
        self.assertEqual(response.status_int, 200)
        self.assertIn('Configure Hostname and SSL', response.body)

    def test_get_not_found(self):
        response = self.app.get('/a/bogus/url', expect_errors=True)
        self.assertEqual(response.status_int, 404)

    def test_byob_and_correct_hostname(self):
        response = self.app.get('/byob')
        self.assertEqual(response.status_int, 200)
        self.assertIn(self.root_controller.hostname, response.body)

    def test_keypair_get_error(self):
        response = self.app.get('/keypair')
        self.assertEqual(response.status_int, 302)

    def test_keypair_post_valid_ssh(self):
        params = {'comparison': 'ssh'}
        files = [
            ('file-ssh-privatekey', self.get_key_filename('ssh', 'private', True)),
            ('file-ssh-publickey', self.get_key_filename('ssh', 'public', True)),
        ]
        response = self.app.post('/keypair/', params, upload_files=files)
        self.assertEqual('0\n', response.body)

    def test_keypair_post_valid_ssl(self):
        params = {'comparison': 'ssl'}
        files = [
            ('file-privatekey', self.get_key_filename('ssl', 'private', True)),
            ('file-publickey', self.get_key_filename('ssl', 'public', True)),
        ]
        response = self.app.post('/keypair/', params, upload_files=files)
        self.assertEqual('0\n', response.body)

    def test_keypair_post_invalid_ssh(self):
        params = {'comparison': 'ssh'}
        files = [
            ('file-ssh-privatekey', self.get_key_filename('ssh', 'private', False)),
            ('file-ssh-publickey', self.get_key_filename('ssh', 'public', False)),
        ]
        response = self.app.post('/keypair/', params, upload_files=files)
        self.assertNotEqual('0\n', response.body)

    def test_keypair_post_invalid_ssl(self):
        params = {'comparison': 'ssl'}
        files = [
            ('file-privatekey', self.get_key_filename('ssl', 'private', False)),
            ('file-publickey', self.get_key_filename('ssl', 'public', False)),
        ]
        response = self.app.post('/keypair/', params, upload_files=files)
        self.assertNotEqual('0\n', response.body)

    def test_keypair_keygen(self):
        response = self.app.get('/keypair/keygen')
        body = response.json
        self.assertEqual(response.status_int, 200)
        self.assertTrue(self.public_regex.match('ssh-rsa '+body['public']))
        self.assertTrue(self.private_regex.match(body['private']))

    def test_keypair_private(self):
        response = self.app.get('/keypair/private')
        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.content_disposition, 'attachment; filename="st2-ssh.key"')
        self.assertTrue(self.private_regex.match(response.body))

    def test_keypair_public(self):
        response = self.app.get('/keypair/public')
        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.content_disposition, 'attachment; filename="st2-ssh.pub"')
        self.assertTrue(self.public_regex.match(response.body))

    def test_root_datasave(self):
        response = self.app.get('/data_save', params={'hostname': 'new-hostname-test', 'password': 'new-password-test'})
        self.assertEqual(response.status_int, 204)
        main_page = self.app.get('/')
        self.assertIn('new-hostname-test', main_page.body)
        self.assertIn('new-password-test', main_page.body)

    def test_root_empty_install_redirect(self):
        response = self.app.get('/install')
        self.assertIn('GET / ', str(response.request))

    def test_root_post(self):
        params = copy(self.default_post)
        response = self.app.post('/', params)
        self.assertEqual(response.status_int, 200)
        self.assertIn('POST /install ', str(response.request))

    def test_root_post_with_files(self):
        params = copy(self.default_post)
        params['selfsigned'] = '0'
        params['sshgen'] = '0'
        params.pop("gen-public", None)
        params.pop("gen-private", None)
        files = [
            ('file-privatekey', self.get_key_filename('ssl', 'private', False)),
            ('file-publickey', self.get_key_filename('ssl', 'public', False)),
            ('file-ssh-privatekey', self.get_key_filename('ssh', 'private', False)),
            ('file-ssh-publickey', self.get_key_filename('ssh', 'public', False)),
        ]
        response = self.app.post('/', params, upload_files=files)
        self.assertEqual(response.status_int, 200)
        self.assertIn('POST /install ', str(response.request))

    def test_root_post_no_chatops(self):
        params = copy(self.default_post)
        params.pop("check-chatops", None)
        params.pop("chatops", None)
        params.pop("slack-token", None)
        response = self.app.post('/', params)
        self.assertEqual(response.status_int, 200)
        self.assertIn('POST /install ', str(response.request))

    def test_root_post_no_reports(self):
        params = copy(self.default_post)
        params.pop("anon-data", None)
        response = self.app.post('/', params)
        self.assertEqual(response.status_int, 200)
        self.assertIn('POST /install ', str(response.request))

    def test_root_post_no_hostname(self):
        params = copy(self.default_post)
        params.pop("hostname", None)
        response = self.app.post('/', params, expect_errors=True)
        self.assertNotEqual(response.status_int, 200)
        self.assertNotIn('POST /install ', str(response.request))

    def test_root_post_no_username(self):
        params = copy(self.default_post)
        params.pop("hostname", None)
        response = self.app.post('/', params, expect_errors=True)
        self.assertNotEqual(response.status_int, 200)
        self.assertNotIn('POST /install ', str(response.request))

    def test_root_post_no_password(self):
        params = copy(self.default_post)
        params.pop("password-1", None)
        params.pop("password-2", None)
        response = self.app.post('/', params, expect_errors=True)
        self.assertNotEqual(response.status_int, 200)
        self.assertNotIn('POST /install ', str(response.request))
