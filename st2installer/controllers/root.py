from IPy import IP
from pecan import expose, request, Response, redirect, abort, route
from subprocess import Popen, PIPE, call
from keypair import KeypairController
from uuid import uuid1
import random, string, os, json

class RootController(object):

  def __init__(self):
    self.proc = None
    self.command = '/usr/bin/sudo FACTER_installer_running=true ENV=current_working_directory NOCOLOR=true /usr/bin/puprun'
    self.st2stop = '/usr/bin/sudo /usr/bin/st2ctl stop'
    self.output = '/tmp/st2installer.log'
    self.lockfile = '/tmp/st2installer_lock'
    self.keypair = KeypairController()
    self.path = "/opt/puppet/hieradata/"
    self.configname = "answers.json"
    self.hostname = ''
    self.config_written = False

    password_length = 32
    password_chars = string.ascii_letters + string.digits
    self.password = ''.join([random.choice(password_chars) for n in xrange(password_length)])

    # Note, any command added here needs to be added to the workroom sudoers entry.
    # File can be found at https://github.com/StackStorm/st2workroom/blob/master/modules/profile/manifests/st2server.pp#L513
    self.cleanup_chain = [
      "/usr/bin/sudo /bin/chmod 660 %s%s" % (self.path, self.configname),
      "/usr/bin/sudo /usr/sbin/service nginx restart",
      "/usr/bin/sudo /usr/bin/st2ctl reload --register-all",
      "/usr/bin/sudo /usr/bin/st2 run st2.call_home",
    ]

    self.grant_access = "/usr/bin/sudo /bin/chmod 755 %s%s" % (self.path, self.configname)

  def lock(self):
    open(self.lockfile, 'w').close()
  def is_locked(self):
    return os.path.isfile(self.lockfile)

  @expose(content_type='text/plain')
  def cleanup(self):
    for command in self.cleanup_chain:
      Popen(command, shell=True)
    return "done"

  @expose(content_type='text/plain')
  def puppet(self, line):
    if not self.proc:
      open(self.output, 'w').close()
      self.p    = Popen("%s > %s 2>&1" % (self.st2stop, self.output), shell=True)
      self.proc = Popen("%s > %s 2>&1" % (self.command, self.output), shell=True)
      self.lock()

    data = ''
    logfile = open(self.output, 'r')
    for i, logline in enumerate(logfile):
      if i>=int(line):
        data += logline.strip()+'\n'
    logfile.close()

    if self.proc.poll() is not None:
      data += '--terminate--'

    if not data:
      return '--idle--'

    return data

  @expose(generic=True, template='index.html')
  def index(self):

    if self.is_locked():
      redirect('/install', internal=True)

    self.hostname = self.hostname or request.host.split(':')[0]

    return { "hubotpassword": self.password, "hostname": self.hostname }

  @index.when(method='POST', template='progress.html')
  def index_post(self, **kwargs):

    if self.is_locked():
      redirect('/install', internal=True)

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

    if "anon-data" in kwargs:
        collect_anonymous_data = True
    else:
        collect_anonymous_data = False

    uuid = str(uuid1())

    config = {
      "system::hostname":               system_hostname,
      "st2::installer_run":             True,
      "st2::api_url":                   "https://%s:9101" % kwargs['hostname'],
      "st2::auth_url":                  "https://%s:9100" % kwargs['hostname'],
      "st2::cli_api_url":               "https://%s:9101" % kwargs['hostname'],
      "st2::cli_auth_url":              "https://%s:9100" % kwargs['hostname'],
      "st2::stanley::username":         kwargs['username'],
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

    if kwargs["sshgen"] == "0":
      config["st2::ssh_public_key"] = request.POST['file-ssh-publickey'].file.read()
      config["st2::ssh_private_key"] = request.POST['file-ssh-privatekey'].file.read()
    else:
      config["st2::stanley::ssh_private_key"] = kwargs['gen-private']
      config["st2::stanley::ssh_public_key"] = kwargs['gen-public']

    if "check-chatops" in kwargs and kwargs["check-chatops"] == "1":

      config.update({
        "hubot::chat_alias": "!",
        "hubot::env_export": {
          "HUBOT_LOG_LEVEL":   "debug",
          "ST2_AUTH_USERNAME": "chatops_bot",
          "ST2_AUTH_PASSWORD": password,
          "ST2_API": "https://%s:9101" % kwargs['hostname'],
          "ST2_WEBUI_URL": "https://%s" % kwargs['hostname'],
          "ST2_AUTH_URL": "https://%s:9100" % kwargs['hostname'],
          "NODE_TLS_REJECT_UNAUTHORIZED": "0",
          "EXPRESS_PORT": "8081"
        },
        "hubot::external_scripts": ["hubot-stackstorm"],
        "hubot::dependencies": {
          "hubot": ">= 2.6.0 < 3.0.0",
          "hubot-scripts": ">= 2.5.0 < 3.0.0",
          "hubot-stackstorm": ">= 0.2.2 < 0.3.0"
        },
      })

      if kwargs["chatops"] == "example":
        config["hubot::adapter"] = "irc"
        config["hubot::env_export"].update({
          "HUBOT_IRC_SERVER":   "localhost",
          "HUBOT_IRC_ROOMS":    "#stackstorm",
          "HUBOT_IRC_NICK":     kwargs['username'],
        })
        config["hubot::dependencies"]["hubot-irc"] = ">=0.2.7 < 1.0.0"
      elif kwargs["chatops"] == "irc":
        config["hubot::adapter"] = "irc"
        config["hubot::env_export"].update({
          "HUBOT_IRC_SERVER":   kwargs["irc-server"],
          "HUBOT_IRC_ROOMS":    kwargs["irc-rooms"],
          "HUBOT_IRC_NICK":     kwargs['irc-nick'],
        })

        # Optional arguments
        if kwargs["irc-port"] != "":
          config["hubot::env_export"]["HUBOT_IRC_PORT"] = kwargs["irc-port"]
        if kwargs["irc-password"] != "":
          config["hubot::env_export"]["HUBOT_IRC_PASSWORD"] = kwargs["irc-password"]
        if kwargs["irc-nickserv-password"] != "":
          config["hubot::env_export"]["HUBOT_IRC_NICKSERV_PASSWORD"] = kwargs["irc-nickserv-password"]
        if kwargs["irc-nickserv-username"] != "":
          config["hubot::env_export"]["HUBOT_IRC_NICKSERV_USERNAME"] = kwargs["irc-nickserv-username"]
        if "irc-server-fake-ssl" in kwargs:
          config["hubot::env_export"]["HUBOT_IRC_SERVER_FAKE_SSL"] = kwargs["irc-server-fake-ssl"]
        if "irc-usessl" in kwargs:
          config["hubot::env_export"]["HUBOT_IRC_USESSL"] = kwargs["irc-usessl"]
        if "irc-unflood" in kwargs:
          config["hubot::env_export"]["HUBOT_IRC_UNFLOOD"] = kwargs["irc-unflood"]

        config["hubot::dependencies"]["hubot-irc"] = ">=0.2.7 < 1.0.0"
      elif kwargs["chatops"] == "flowdock":
        config["hubot::adapter"] = "flowdock"
        config["hubot::env_export"].update({
          "HUBOT_FLOWDOCK_API_TOKEN":       kwargs["flowdock-token"],
          "HUBOT_FLOWDOCK_LOGIN_EMAIL":     kwargs["flowdock-email"],
          "HUBOT_FLOWDOCK_LOGIN_PASSWORD":  kwargs['flowdock-password']
        })
        config["hubot::dependencies"]["hubot-flowdock"] = ">=0.7.6 < 1.0.0"
      elif kwargs["chatops"] == "slack":
        config["hubot::adapter"] = "slack"
        config["hubot::env_export"].update({
          "HUBOT_SLACK_TOKEN": kwargs["slack-token"]
        })
        config["hubot::dependencies"]["hubot-slack"] = ">=3.3.0 < 4.0.0"
      elif kwargs["chatops"] == "hipchat":
        config["hubot::adapter"] = "hipchat"
        config["hubot::env_export"].update({
          "HUBOT_HIPCHAT_JID": kwargs["hipchat-jid"],
          "HUBOT_HIPCHAT_PASSWORD": kwargs["hipchat-password"]
        })
        if kwargs["text-hipchat-domain"] != "":
          config["hubot::env_export"]["HUBOT_XMPP_DOMAIN"] = kwargs["text-hipchat-domain"]
        config["hubot::dependencies"]["hubot-hipchat"] = ">=2.12.0 < 3.0.0"
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
        config["hubot::dependencies"]["hubot-xmpp"] = ">=0.1.16 < 1.0.0"

    if not os.path.exists(self.path):
      os.makedirs(self.path)

    if not os.access(self.path+self.configname, os.W_OK):
      Popen(self.grant_access, shell=True).wait()

    with open(self.path+self.configname, 'w') as workroom:
      workroom.write(json.dumps(config))

    self.config_written = True
    redirect('/install', internal=True)

  @expose(generic=True)
  def data_save(self, hostname, password):
    self.hostname = hostname
    self.password = password

  @expose(generic=True, template='progress.html')
  def install(self):
    if self.config_written:
      return {"hostname": self.hostname}
    else:
      redirect('/', internal=True)

  @expose(generic=True, template='byob.html')
  def byob(self):
    return {"hostname": (self.hostname or request.host.split(':')[0]), "password": self.password}
