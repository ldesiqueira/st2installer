var i18n = {
  next: "Next",
  back: "Back",
  last: "Get started!",
  required: "Required field.",
  fqdn: "Should be an IP address or a FQDN.",
  ssl_required: "Both keys are required if not using a generated pair.",
  complexity: "Complexity requirements are not met.",
  confirmation: "Passwords do not match.",
  slack: "API token is required for Slack integration.",
  hipchat: "JID and password are required for HipChat integration.",
  xmpp: "Username, password and at least one room are required for XMPP integration.",
  irc: "Server and at least one room are required for IRC integration.",
  flowdock: "All fields are required for Flowdock integration.",
  ssh: {
    'header': "Whoa. The keys do not match!",
    'text': "It appears you've uploaded a key pair that either does not match or isn't really a key pair at all! \
              You can upload another set of keys or we can just generate a new key pair for you, no problem.",
    'buttons': [
      ['Generate', '#generate'],
      ['Re-upload', '#back']
    ]
  },
  ssl: {
    'header': "Certificate error",
    'text': "It appears you've uploaded a certificate and a private key that either do not match or aren't in the right format! \
              You need to upload a PEM certificate and a private key without a passphrase. \
              You can upload another certificate or we can just generate a self-signed one for you, no problem.",
    'buttons': [
      ['Generate', '#generate'],
      ['Re-upload', '#back']
    ]
  },
  keypair: {
    'header': "Your SSH key pair",
    'text': "There's a new pair of SSH keys generated just for you! Be sure to save them and keep them very safe.",
    'buttons': [
      ['Got it!', '#next']
    ]
  }
};
var puppet = {
  warning: [
    /warn/i
  ],
  error: [
    /error/i,
    /fail/i
  ],
  important: [

  ],
  checkpoints: [
    [/apply hostname.*executed successfully/, 15],
    [/pip_install_python-mistralclient.*executed successfully/, 25],
    [/Download st2client requirements.*executed successfully/, 35],
    [/pip_install_uwsgi.*executed successfully/, 45],
    [/Download st2server requirements.*executed successfully/, 55],
    [/wget-st2web.*executed successfully/, 65],
    [/npm_proxy.*executed successfully/, 75],
    [/st2api.conf.*executed successfully/, 85],
  ],
  progress: 0,
  errors: 0,
  warnings: 0,
  line: 0,
  interval: 700,
  url: 'puppet',
  cleanup: 'cleanup',
  set_progress: function(p) {
    puppet.progress = p;
    $('#progressbar>span').width(p+'%');
    if (p == 100) {
      puppet.complete();
    }
  },
  add_error: function() {
    puppet.errors += 1;
    $('#errors').text(puppet.errors);
    if (puppet.errors == 1) {
      $('#errors-plural').hide();
    } else {
      $('#errors-plural').show();
    }
  },
  add_warning: function() {
    puppet.warnings += 1;
    $('#warnings').text(puppet.warnings);
    if (puppet.warnings == 1) {
      $('#warnings-plural').hide();
    } else {
      $('#warnings-plural').show();
    }
  },
  read: function() {
    var stream = $.ajax({
      url: puppet.url,
      data: {line: puppet.line},
      timeout: 500,
      complete: function(data, status) {
        data = String(data.responseText);
        if (data != '--idle--' && status != 'timeout') {
          lines = data.split('\n');
          for (var i = 0; i < lines.length; i++) {
            line = lines[i];
            if (i == lines.length-1 && line == '--terminate--') {
              puppet.set_progress(100);
            } else if (line.trim()) {
              puppet.line += 1;
              p_class = 'message';

              for (var ii = 0; ii < puppet.important.length; ii++) {
                if (puppet.important[ii].test(line)) {
                  p_class = 'output-important';
                }
              }
              for (var ii = 0; ii < puppet.warning.length; ii++) {
                if (puppet.warning[ii].test(line)) {
                  p_class = 'output-warning';
                  puppet.add_warning();
                }
              }
              for (var ii = 0; ii < puppet.error.length; ii++) {
                if (puppet.error[ii].test(line)) {
                  p_class = 'output-error';
                  puppet.add_error();
                }
              }
              for (var ii = 0; ii < puppet.checkpoints.length; ii++) {
                if (puppet.checkpoints[ii][0].test(line)) {
                  p_class = 'output-important';
                  puppet.set_progress(puppet.checkpoints[ii][1]);
                }
              }

              scroll = $('#output')[0].scrollHeight - $('#output')[0].scrollTop === $('#output')[0].clientHeight;
              content = $('<p class="'+p_class+'"/>').text(line);
              $('#output-content').append(content);
              if (scroll) {
                $('#output')[0].scrollTop = $('#output')[0].scrollHeight;
                puppet.scroll_disabled = 0;
              }
            }
          }
        }
        if (puppet.progress < 100) {
          setTimeout(puppet.read, puppet.interval);
        }
      }
    });
  },
  complete: function() {
    $('#page-puppet').removeClass('progress');
    $('#puppet-done').show();
    $.get(puppet.cleanup);
    $.ajax({
      type: 'HEAD',
      url: '/ssl/st2_root_ca.cer',
      success: function() {
        $('#rootca-warning').show();
      }
    });
  },
  init: function() {
    $('#page-puppet').addClass('progress');
    $('#progress-bar').addClass('started');
    $('#filtering input').on("change", function() {
      $('#output').removeClass('important-only');
      $('#output').removeClass('errors-only');
      if ($('#filtering input[value=important]').is(':checked')) {
        $('#output').addClass('important-only');
      } else if ($('#filtering input[value=errors]').is(':checked')) {
        $('#output').addClass('errors-only');
      }
    });
    puppet.set_progress(5); // So that the user could notice the progress bar from the beginning.
    puppet.read();
  }

};
var installer = {
  page: 0,
  chatops: 0,
  errors: 0,
  key_validator: 'keypair/',
  key_generator: 'keypair/keygen',
  switch_page: function(page) {
    var perform_switch = function() {
      installer.page = page;
      $('.page')
        .removeClass('active')
        .eq(page)
          .addClass('active');
      $('#stepcount li')
        .removeClass('past')
        .removeClass('active')
        .eq(page)
          .addClass('active')
          .prevAll()
            .addClass('past');
      $('#current-step').text(page+1);
      if (page == $('.page').length-1) {
        $('#step-next').text(i18n.last);
      } else {
        $('#step-next').text(i18n.next);
      }
      if (page === 0) {
        $('#step-back').hide();
      } else {
        $('#step-back').show();
      }
    };
    if (page <= installer.page) {
      perform_switch();
    } else {
      installer.validate(installer.page, perform_switch);
    }
    return false;
  },
  switch_chatops: function(tab) {
    installer.chatops = tab;
    $('#chatops-tabs li')
      .removeClass('active')
      .eq(tab)
        .addClass('active');
    $('#chatops-navigation li a')
      .removeClass('active')
      .eq(tab)
        .addClass('active');
    $('#chatops-flag').val($('#chatops-navigation li a').eq(tab).attr('href').slice(5));
  },
  append_error: function(el, error) {
    installer.errors += 1;
    el.after('<p class="error">'+error+'</p>');
  },
  modal: $(
    '<div id="modal-overflow">' +
      '<div id="modal">' +
        '<h3></h3>' +
        '<p></p>' +
        '<div id="keypair">' +
          '<label for="keypair-public">Your public key</label>' +
          '<textarea id="keypair-public"></textarea>' +
          '<a href="keypair/public">Download</a>' +
          '<label for="keypair-private">Your private key</label>' +
          '<textarea id="keypair-private"></textarea>' +
          '<a href="keypair/private">Download</a>' +
        '</div>' +
        '<div id="modal-buttons">' +
        '</div>' +
      '</div>' +
    '</div>'
  ),
  raise_modal: function(template) {

    $('#modal-overflow').remove();
    modal = installer.modal;
    modal.find('h3').text(i18n[template].header);
    modal.find('p').text(i18n[template].text);
    modal.find('#modal-buttons').empty();
    for (var i = 0; i < i18n[template].buttons.length; i++) {
      modal.find('#modal-buttons').append('<a href="'+i18n[template].buttons[i][1]+'">'+i18n[template].buttons[i][0]+'</a>');
    }
    if (template == 'keypair') {
      modal.find('#keypair').show();
      modal.find('#keypair-public').val('ssh-rsa '+$('#gen-public').val());
      modal.find('#keypair-private').val($('#gen-private').val());
    }
    modal.appendTo('#installer').show();
    modal.find('#modal').css('margin-top', -modal.find('#modal').height()/2);

  },
  modal_back: function () {
    $('#modal-overflow').remove();
    return false;
  },
  modal_generate: function () {
    $('#modal-overflow').remove();
    if (installer.page === 0) {
      $('#radio-selfsigned-true').click();
      installer.switch_page(1);
    } else if (installer.page === 1) {
      $('#radio-sshgen-true').click();
      installer.switch_page(2);
    }
    return false;
  },
  validate: function(page, callback) {

    var framewait = false;
    installer.errors = 0;
    $('p.error').remove();

    if (installer.page === 0) {

      var hostname = $('#text-hostname');
      if (hostname.val().trim().length === 0) {
        installer.append_error(hostname, i18n.required);
      } else if (!/^[0-9a-z\.\-]+$/.test(hostname.val())) {
        installer.append_error(hostname, i18n.fqdn);
      }

      if ($('#radio-selfsigned-false').is(':checked') &&
          ($('#file-publickey').val().trim().length === 0 ||
           $('#file-privatekey').val().trim().length === 0)) {
        installer.append_error($('#ssl'), i18n.ssl_required);
      }

      if (installer.errors === 0) {
        $.get("data_save", { hostname: hostname.val(), password: $('#hubot-password').val() });
        if ($('#radio-selfsigned-false').is(':checked')) {
          $('#hidden-comparison').val('ssl');
          $('#installer').attr("target", "keypair-frame");
          $('#installer').attr("action", installer.key_validator);
          $('#installer').submit();
          framewait = true;
        }
      }

    } else if (installer.page === 1) {

      var password = $('#text-password-1');
      if (password.val().trim().length === 0) {
        installer.append_error(password, i18n.required);
      } else if (!(password.val().match(/[a-zA-Z]/) &&
                   password.val().match(/[0-9]/) &&
                   password.val().length >= 8)) {
        installer.append_error(password, i18n.complexity);
      }

      var password_confirmation = $('#text-password-2');
      if (password.val() != password_confirmation.val()) {
        installer.append_error(password_confirmation, i18n.confirmation);
      }

      var username = $('#text-username');
      if (username.val().trim().length === 0) {
        installer.append_error(username, i18n.required);
      }

      if ($('#radio-sshgen-false').is(':checked') &&
          ($('#file-ssh-publickey').val().trim().length === 0 ||
           $('#file-ssh-privatekey').val().trim().length === 0)) {
        installer.append_error($('#ssh'), i18n.ssl_required);
      }

      if ($('#radio-sshgen-false').is(':checked') &&
          installer.errors === 0) {

        $('#hidden-comparison').val('ssh');
        $('#installer').attr("target", "keypair-frame");
        $('#installer').attr("action", installer.key_validator);
        $('#installer').submit();
        framewait = true;

      }

    } else if (installer.page == 2) {

      if ($('#check-chatops').is(':checked')) {
        switch(installer.chatops) {
        case 0:
          if ($('#text-slack-token').val().trim().length === 0) {
            installer.append_error($('#tab-slack p:first-child'), i18n.slack);
          }
          break;
        case 1:
          if ($('#text-hipchat-jid').val().trim().length === 0 ||
              $('#text-hipchat-password').val().trim().length === 0) {
            installer.append_error($('#tab-hipchat p:first-child'), i18n.hipchat);
          }
          break;
        case 2:
          if ($('#text-xmpp-rooms').val().trim().length === 0 ||
              $('#text-xmpp-username').val().trim().length === 0 ||
              $('#text-xmpp-password').val().trim().length === 0) {
            installer.append_error($('#tab-xmpp p:first-child'), i18n.xmpp);
          }
          break;
        case 3:
          if ($('#text-irc-server').val().trim().length === 0 ||
              $('#text-irc-rooms').val().trim().length === 0) {
            installer.append_error($('#tab-irc p:first-child'), i18n.irc);
          }
          break;
        case 4:
          if ($('#text-flowdock-token').val().trim().length === 0 ||
              $('#text-flowdock-email').val().trim().length === 0 ||
              $('#text-flowdock-password').val().trim().length === 0) {
            installer.append_error($('#tab-flowdock p:first-child'), i18n.flowdock);
          }
          break;
        }
      }

    }

    if (installer.errors === 0) {
      if (framewait) {
        framewait = false;
        $('#keypair-frame').off('load');
        $('#keypair-frame').on('load', function() {
          if ($('#keypair-frame').contents().text().trim() != "0") {
            installer.errors += 1;
            installer.raise_modal($('#hidden-comparison').val());
          } else {
            callback();
          }
        });
      } else if (installer.page == 1 &&
                 $('#radio-sshgen-true').is(':checked') &&
                 $('#gen-private').val() === '') {
        $.get(installer.key_generator).always(function(keypair) {
          $('#gen-private').val(keypair.private);
          $('#gen-public').val(keypair.public);
          installer.raise_modal('keypair');
        });
      } else {
        callback();
      }
    }

  },
  submit: function() {
    if (installer.page == $('.page').length-1) {
      installer.validate(installer.page, function() {
        $('#installer').removeAttr("target");
        $('#installer').removeAttr("action");
        $('#installer').submit();
      });
    } else {
      installer.switch_page(installer.page+1);
    }
  },
  init: function() {
    installer.switch_page(0);
    installer.switch_chatops(0);
    $('#step-back').click(function() {
      installer.switch_page(installer.page-1);
      return false;
    });
    $('#step-next').click(function() {
      if (installer.page == $('.page').length-1) {
        installer.submit();
      } else {
        installer.switch_page(installer.page+1);
      }
      return false;
    });

    $('#installer').on('click', '#modal a[href=#back]', installer.modal_back);
    $('#installer').on('click', '#modal a[href=#generate]', installer.modal_generate);
    $('#installer').on('click', '#modal a[href=#next]', function() {
      installer.switch_page(installer.page+1);
      $('#modal-overflow').remove();
      return false;
    });

    $('#total-steps').text($('.page').length);

    $('#radio-selfsigned-false').on('change', function() {
      $('#ssl').show();
    });

    $('#radio-selfsigned-true').on('change', function() {
      $('#ssl').hide();
    });

    $('#radio-sshgen-false').on('change', function() {
      $('#ssh').show();
    });

    $('#radio-sshgen-true').on('change', function() {
      $('#ssh').hide();
    });

    $('#chatops-navigation li a').on('click', function() {
      installer.switch_chatops($('#chatops-navigation a').index(this));
      return false;
    });

  }
};

$(function() {
  if ($('#installer').length) {
    installer.init();
  }
  if ($('#page-puppet').length) {
    puppet.init();
  }
});
