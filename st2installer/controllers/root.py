from IPy import IP
from pecan import expose, request, redirect, conf
from subprocess import Popen, CalledProcessError
from keypair import KeypairController
from uuid import uuid1
import time
import random
import string
import os
import json
from st2installer.controllers.base import BaseController


class RootController(BaseController):

    def __init__(self, config=None):

        self.proc = None
        self.st2stop = '/usr/bin/sudo /usr/bin/st2ctl stop'
        self.output = '/tmp/st2installer.log'
        self.lockfile = '/tmp/st2installer_lock'
        self.keypair = KeypairController()
        self.configname = "answers.json"
        self.hostname = ''
        self.config = None
        self.start_time = None
        self.runtime = None
        self.analytics_sent = False
        self.puppet_check_command = 'ps aux | grep "[p]uppet-apply"'
        self.gen_ssl = 'Self-signed'
        self.gen_ssh = 'Generated'
        self.version = None

        config = config or conf.to_dict()
        if 'app' in config and 'version' in config['app']:
            self.version = config['app']['version']
        if 'puppet' in config and 'command' in config['puppet']:
            self.command = config['puppet']['command']
        else:
            self.command = '/usr/bin/sudo ' + \
                           'FACTER_installer_running=true ' + \
                           'ENV=current_working_directory ' + \
                           'NOCOLOR=true /usr/bin/puprun'
        if 'puppet' in config and 'hieradata' in config['puppet']:
            self.path = config['puppet']['hieradata']
        else:
            self.path = "/opt/puppet/hieradata/"

        password_length = 32
        password_chars = string.ascii_letters + string.digits
        self.password = ''.join([random.choice(password_chars) for n in xrange(password_length)])

        # Note, any command added here needs to be added to the workroom sudoers entry.
        # File can be found at
        # https://github.com/StackStorm/st2workroom/blob/master/modules/profile/manifests/st2server.pp#L513
        self.cleanup_chain = [
            "/usr/bin/sudo /bin/chmod 660 %s%s" % (self.path, self.configname),
            "/usr/bin/sudo /usr/sbin/service nginx restart",
            "/usr/bin/sudo /usr/bin/st2ctl reload --register-all",
            "/usr/bin/sudo /usr/sbin/service docker-hubot restart",
            "/usr/bin/sudo /usr/bin/st2 run st2.call_home",
        ]

        self.grant_access = "/usr/bin/sudo /bin/chmod 755 %s%s" % (self.path, self.configname)

    def lock(self):
        open(self.lockfile, 'w').close()

    def is_locked(self):
        return os.path.isfile(self.lockfile)

    def log_is_empty(self):
        return not os.path.isfile(self.output) or os.stat(self.output).st_size == 0

    def config_written(self):
        return os.path.isfile(self.path + self.configname)

    def puppet_check(self):
        p = Popen(self.puppet_check_command, shell=True)
        p.communicate()
        return p.returncode == 0

    def redirect_check(self):
        if self.is_locked():
            redirect('/install', internal=True)
        elif self.puppet_check():
            redirect('/wait', internal=True)

    def cleanup(self):
        errors = []
        for command in self.cleanup_chain:
            try:
                Popen(command, shell=True).wait()
            except CalledProcessError as e:
                errors.append(e)
        return errors or True

    @expose(content_type='text/plain')
    def puppet(self, line):
        if not self.proc and self.log_is_empty():
            open(self.output, 'w').close()
            self.p = Popen("%s > %s 2>&1" % (self.st2stop, self.output), shell=True)
            self.proc = Popen("%s > %s 2>&1" % (self.command, self.output), shell=True)
            self.lock()
            self.start_time = time.time()

        data = ''
        logfile = open(self.output, 'r')
        for i, logline in enumerate(logfile):
            if i >= int(line):
                data += logline.strip() + '\n'
        logfile.close()

        if not self.proc and not self.log_is_empty():
            data += '--terminate--'

        elif self.proc.poll() is not None:
            if self.runtime:
                data += '--terminate--'
            else:
                cleanup = self.cleanup()
                if cleanup is not True:
                    data += 'ERROR: Cleanup failure!' + '\n'
                    data += '\n'.join(cleanup)
                self.runtime = (time.time() - self.start_time)
                data += '\n--terminate--'
                data += str(self.runtime)

        if not data:
            return '--idle--'

        return data

    @expose(generic=True, template='index.html')
    def index(self):
        skip_lock_check = self._get_query_param_value(request=request,
                                                      param_name='skip_lock_check',
                                                      param_type='bool',
                                                      default_value=False)

        if not skip_lock_check:
            self.redirect_check()

        self.hostname = self.hostname or request.host.split(':')[0]
        return {"hubotpassword": self.password,
                "hostname": self.hostname,
                "version": self.version}

    @expose(generic=True, template='wait.html')
    def wait(self):
        return {}

    @index.when(method='POST', template='progress.html')
    def index_post(self, **kwargs):
        skip_lock_check = self._get_query_param_value(request=request,
                                                      param_name='skip_lock_check',
                                                      param_type='bool',
                                                      default_value=False)

        if not skip_lock_check:
            self.redirect_check()

        # special handling for system hostname incase it is an IP.
        system_hostname = kwargs['hostname']

        try:
            ip = IP(system_hostname)
            # checking for len == 1 enables us to skip an hostname value of the
            # kind 127.0.0.0/30. Arguably this is a bogus value anyway.
            if len(ip) == 1 and ip.version() == 4:
                system_hostname = 'ip-%s' % system_hostname.replace('.', '-')
            if len(ip) == 1 and ip.version() == 6:
                system_hostname = 'ip-%s' % system_hostname.strip(':').replace(':', '-')
        except:
            pass

        self.hostname = kwargs['hostname']
        password = kwargs['hubot-password']

        collect_anonymous_data = True if "anon-data" in kwargs else False

        uuid = str(uuid1())

        config = {
            "system::hostname": system_hostname,
            "st2::installer_run": True,

            "st2::api_url": "https://%s/api" % kwargs['hostname'],
            "st2::auth_url": "https://%s/auth" % kwargs['hostname'],

            "st2::cli_api_url": "https://%s/api" % kwargs['hostname'],
            "st2::cli_auth_url": "https://%s/auth" % kwargs['hostname'],

            "st2::stanley::username": kwargs['username'],

            "users": {
                kwargs['admin-username']: {
                    "password": kwargs['password-1'],
                    "admin": True,
                },
                "chatops_bot": {
                    "password": password,
                    "shell": "/bin/false"
                }
            },
            "groups": {
                "robots": {
                    "gid": "6000",
                }
            },
            "st2::kvs": {
                "st2::server_uuid": {
                    "value": uuid,
                },
                "st2::collect_anonymous_data": {
                    "value": collect_anonymous_data
                },
                "st2::user_data": {
                    "value": "{}"
                }
            }
        }

        if kwargs["selfsigned"] == "0":
            config["st2::ssl_public_key"] = request.POST['file-publickey'].file.read()
            config["st2::ssl_private_key"] = request.POST['file-privatekey'].file.read()
            self.gen_ssl = 'Provided'

        if kwargs["sshgen"] == "0":
            config["st2::ssh_public_key"] = request.POST['file-ssh-publickey'].file.read()
            config["st2::ssh_private_key"] = request.POST['file-ssh-privatekey'].file.read()
            self.gen_ssh = 'Provided'
        else:
            config["st2::stanley::ssh_private_key"] = kwargs['gen-private']
            config["st2::stanley::ssh_public_key"] = kwargs['gen-public']

        if "enterprise" in kwargs and kwargs["enterprise"] != "":
            config["st2enterprise::token"] = kwargs["enterprise"]

        if "check-chatops" in kwargs and kwargs["check-chatops"] == "1":

            config.update({
                "hubot::docker": True,
                "hubot::chat_alias": "!",
                "hubot::env_export": {
                    "HUBOT_LOG_LEVEL": "debug",
                    "ST2_AUTH_USERNAME": "chatops_bot",
                    "ST2_AUTH_PASSWORD": password,
                    "ST2_API": "https://%s:443/api" % kwargs['hostname'],
                    "ST2_WEBUI_URL": "https://%s" % kwargs['hostname'],
                    "ST2_AUTH_URL": "https://%s:443/auth" % kwargs['hostname'],
                    "NODE_TLS_REJECT_UNAUTHORIZED": "0",
                    "EXPRESS_PORT": "8081"
                },
                "hubot::external_scripts": ["hubot-stackstorm"],
                "hubot::dependencies": {},
            })

            if kwargs["chatops"] == "example":
                config["hubot::adapter"] = "irc"
                config["hubot::env_export"].update({
                    "HUBOT_IRC_SERVER": "localhost",
                    "HUBOT_IRC_ROOMS": "#stackstorm",
                    "HUBOT_IRC_NICK": kwargs['username'],
                })
            elif kwargs["chatops"] == "irc":
                config["hubot::adapter"] = "irc"
                config["hubot::env_export"].update({
                    "HUBOT_IRC_SERVER": kwargs["irc-server"],
                    "HUBOT_IRC_ROOMS": kwargs["irc-rooms"],
                    "HUBOT_IRC_NICK": kwargs['irc-nick'],
                })

                # Optional arguments
                if kwargs["irc-port"] != "":
                    config["hubot::env_export"]["HUBOT_IRC_PORT"] = kwargs["irc-port"]
                if kwargs["irc-password"] != "":
                    config["hubot::env_export"]["HUBOT_IRC_PASSWORD"] = kwargs["irc-password"]
                if kwargs["irc-nickserv-password"] != "":
                    config["hubot::env_export"]["HUBOT_IRC_NICKSERV_PASSWORD"] = \
                        kwargs["irc-nickserv-password"]
                if kwargs["irc-nickserv-username"] != "":
                    config["hubot::env_export"]["HUBOT_IRC_NICKSERV_USERNAME"] = \
                        kwargs["irc-nickserv-username"]
                if "irc-server-fake-ssl" in kwargs:
                    config["hubot::env_export"]["HUBOT_IRC_SERVER_FAKE_SSL"] = \
                        kwargs["irc-server-fake-ssl"]
                if "irc-usessl" in kwargs:
                    config["hubot::env_export"]["HUBOT_IRC_USESSL"] = kwargs["irc-usessl"]
                if "irc-unflood" in kwargs:
                    config["hubot::env_export"]["HUBOT_IRC_UNFLOOD"] = kwargs["irc-unflood"]

            elif kwargs["chatops"] == "flowdock":
                config["hubot::adapter"] = "flowdock"
                config["hubot::env_export"].update({
                    "HUBOT_FLOWDOCK_API_TOKEN": kwargs["flowdock-token"],
                    "HUBOT_FLOWDOCK_LOGIN_EMAIL": kwargs["flowdock-email"],
                    "HUBOT_FLOWDOCK_LOGIN_PASSWORD": kwargs['flowdock-password']
                })
            elif kwargs["chatops"] == "slack":
                config["hubot::adapter"] = "slack"
                config["hubot::env_export"].update({
                    "HUBOT_SLACK_TOKEN": kwargs["slack-token"]
                })
            elif kwargs["chatops"] == "hipchat":
                config["hubot::adapter"] = "hipchat"
                config["hubot::env_export"].update({
                    "HUBOT_HIPCHAT_JID": kwargs["hipchat-jid"],
                    "HUBOT_HIPCHAT_PASSWORD": kwargs["hipchat-password"]
                })
                if kwargs["text-hipchat-domain"] != "":
                    config["hubot::env_export"]["HUBOT_XMPP_DOMAIN"] = kwargs["text-hipchat-domain"]
            elif kwargs["chatops"] == "xmpp":
                config["hubot::adapter"] = "xmpp"
                config["hubot::env_export"].update({
                    "HUBOT_XMPP_USERNAME": kwargs["xmpp-username"],
                    "HUBOT_XMPP_PASSWORD": kwargs["xmpp-password"],
                    "HUBOT_XMPP_ROOMS": kwargs["xmpp-rooms"]
                })
                if kwargs["xmpp-host"] != "":
                    config["hubot::env_export"]["HUBOT_XMPP_HOST"] = kwargs["xmpp-host"]
                if kwargs["xmpp-port"] != "":
                    config["hubot::env_export"]["HUBOT_XMPP_PORT"] = kwargs["xmpp-port"]

        if not os.path.exists(self.path):
            os.makedirs(self.path)

        if not os.access(self.path + self.configname, os.W_OK):
            Popen(self.grant_access, shell=True).wait()

        with open(self.path + self.configname, 'w') as workroom:
            workroom.write(json.dumps(config))

        self.config = config
        redirect('/install', internal=True)

    @expose(generic=True)
    def data_save(self, hostname, password):
        self.hostname = hostname
        self.password = password

    @expose(generic=True, template='progress.html')
    def install(self):
        if self.config_written():
            if self.config:
                if "hubot::adapter" in self.config:
                    chatops = self.config["hubot::adapter"]
                else:
                    chatops = "Disabled"
                sent = self.analytics_sent
                self.analytics_sent = True
                return {"hostname": self.hostname,
                        "config": self.config,
                        "gen_ssl": self.gen_ssl,
                        "gen_ssh": self.gen_ssh,
                        "sent": sent,
                        "chatops": chatops}
            else:
                return {"hostname": self.hostname,
                        "sent": True}
        else:
            redirect('/', internal=True)

    @expose(generic=True, template='byob.html')
    def byob(self):
        return {"hostname": (self.hostname or request.host.split(':')[0]),
                "password": self.password}
