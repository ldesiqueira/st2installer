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
  generating_keys: "Our best engineers are forging your SSH keys...",
  ssh: {
    'header': "Whoa. The keys do not match!",
    'text': "It appears you've uploaded a key pair that either does not match, is password protected or isn't really a key pair at all! " +
            "You can upload another set of keys or we can just generate a new key pair for you, no problem.",
    'buttons': [
      ['Generate', '#generate'],
      ['Re-upload', '#back']
    ]
  },
  ssl: {
    'header': "Certificate error",
    'text': "It appears you've uploaded a certificate and a private key that either do not match or aren't in the right format! " +
              "You need to upload a PEM certificate and a private key without a passphrase. " +
              "You can upload another certificate or we can just generate a self-signed one for you, no problem.",
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
    [/remove empty hubot env settings.*executed successfully/, 25],
    [/st2sensorcontainer\.log/, 45],
    [/Setting root_cli password.*executed successfully/, 57],
    [/Service\[mistral\].*'running'/, 66],
    [/Service\[st2rulesengine\].*'running'/, 75],
    [/Service\[hubot\]: Triggered 'refresh'/, 82],
    [/Service\[nginx\]: Triggered 'refresh'/, 89],
    [/set-st2-key-st2::server_uuid.*executed successfully/, 95]
  ],
  progress: 0,
  errors: 0,
  warnings: 0,
  line: 0,
  access_errors: 0,
  interval: 700,
  url: 'puppet',
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
      success: function(res, status, data) {
        puppet.access_errors = 0;
        data = String(data.responseText);
        if (data != '--idle--' && status != 'timeout') {
          lines = data.split('\n');
          for (var i = 0; i < lines.length; i++) {
            line = lines[i];
            if (i == lines.length-1 && line.slice(0, 13) == '--terminate--') {
              puppet.set_progress(100);
              runtime = Math.ceil(parseFloat(line.slice(13)));
              if (ga && runtime) {
                ga('set', 'metric1', runtime);
                ga('set', 'metric2', parseInt($('#errors').text()));
                ga('set', 'metric3', parseInt($('#warnings').text()));
                ga('send', 'pageview', '/done');
              }
            } else if (line.trim()) {
              puppet.line += 1;
              p_class = 'message';

              var ii;
              for (ii = 0; ii < puppet.important.length; ii++) {
                if (puppet.important[ii].test(line)) {
                  p_class = 'output-important';
                }
              }
              for (ii = 0; ii < puppet.warning.length; ii++) {
                if (puppet.warning[ii].test(line)) {
                  p_class = 'output-warning';
                  puppet.add_warning();
                }
              }
              for (ii = 0; ii < puppet.error.length; ii++) {
                if (puppet.error[ii].test(line)) {
                  p_class = 'output-error';
                  puppet.add_error();
                }
              }
              for (ii = 0; ii < puppet.checkpoints.length; ii++) {
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
      },
      error: function() {
        puppet.access_errors += 1;
        if (puppet.access_errors > 5) {
          location.reload();
        }
      },
      complete: function(data, status) {
        if (puppet.progress < 100) {
          setTimeout(puppet.read, puppet.interval);
        }
      }
    });
  },
  complete: function() {
    $('#page-puppet')
      .removeClass('progress')
      .addClass('done');
    $('#puppet-done').show();
    $.ajax({
      type: 'HEAD',
      url: '/ssl/st2_root_ca.cer',
      success: function() {
        $('#rootca-warning').show();
      }
    });
  },
  init: function() {
    if (ga && $('#sent').val() == 'False') {
      ga('set', 'metric4', 1);
      ga('set', 'dimension1', $('#ga-chatops').val());
      switch($('#ga-chatops').val()) {
        case 'Disabled':
          ga('set', 'metric5', 1);
          break;
        case 'slack':
          ga('set', 'metric6', 1);
          break;
        case 'flowdock':
          ga('set', 'metric7', 1);
          break;
        case 'hipchat':
          ga('set', 'metric8', 1);
          break;
        case 'irc':
          ga('set', 'metric9', 1);
          break;
        case 'xmpp':
          ga('set', 'metric11', 1);
          break;
      }
      ga('set', 'dimension2', $('#ga-ssh').val());
      switch($('#ga-ssh').val()) {
        case 'Generated':
          ga('set', 'metric12', 1);
          break;
        case 'Provided':
          ga('set', 'metric13', 1);
          break;
      }
      ga('set', 'dimention3', $('#ga-ssl').val());
      switch($('#ga-ssl').val()) {
        case 'Self-signed':
          ga('set', 'metric14', 1);
          break;
        case 'Provided':
          ga('set', 'metric15', 1);
          break;
      }
      ga('send', 'pageview', '/install');
    } else if (ga && $('#sent').val() == 'True') {
      ga('send', 'pageview', '/install-refresh');
    }
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
      $(window).scrollTop(0);
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
      if (ga) {
        if (page === 0 && $('#version').val().length) {
          ga('set', 'dimension4', $('#version').val());
        }
        ga('send', 'pageview', '/step'+(page+1));
      }
      $('#step-back, #step-next').removeClass('disabled');
    };
    if (page <= installer.page) {
      perform_switch();
    } else {
      $('#step-back, #step-next').addClass('disabled');
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
  overlay: $('<div id="overlay">').appendTo('#installer'),
  wait_message: $('<p id="wait-message">'),
  modal: $(
    '<div id="modal">' +
      '<h3></h3>' +
      '<p></p>' +
      '<div id="keypair">' +
        '<label for="keypair-public">Your public key</label>' +
        '<textarea id="keypair-public"></textarea>' +
        '<a data-key-type="public" data-key-filename="st2-ssh.pub" class="download-ssh-key">Download</a>' +
        '<label for="keypair-private">Your private key</label>' +
        '<textarea id="keypair-private"></textarea>' +
        '<a data-key-type="private" data-key-filename="st2-ssh.key" class="download-ssh-key">Download</a>' +
      '</div>' +
      '<div id="modal-buttons">' +
      '</div>' +
    '</div>'
  ),
  show_wait_message: function(text) {
    installer.wait_message.text(text);
    installer.overlay.empty().append(installer.wait_message).show();
  },
  raise_modal: function(template) {

    var modal = installer.modal;
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
    installer.overlay.empty().append(modal).show();

  },
  modal_back: function () {
    installer.overlay.hide();
    return false;
  },
  modal_generate: function () {
    installer.overlay.hide();
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
        installer.show_wait_message(i18n.generating_keys);
        $.get(installer.key_generator).always(function(keypair) {
          $('#gen-private').val(keypair.private);
          $('#gen-public').val(keypair.public);
          installer.raise_modal('keypair');
        });
      } else {
        callback();
      }
    } else {
      $('#step-back, #step-next').removeClass('disabled');
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
      if ($(this).hasClass('disabled')) {
        return false;
      }

      installer.switch_page(installer.page-1);
      return false;
    });
    $('#step-next').click(function() {
      if ($(this).hasClass('disabled')) {
        return false;
      }

      if (installer.page == $('.page').length-1) {
        installer.submit();
      } else {
        installer.switch_page(installer.page+1);
      }
      return false;
    });

    var check_key_state = function () {
      if (!!($('#ch-enterprise:checked').get(0))) {
        $('#license-key input').removeAttr('disabled');
      } else {
        $('#license-key input').attr('disabled', 'disabled');
      }
    };

    check_key_state();
    $('#ch-enterprise').change(check_key_state);

    $('#installer').on('click', '#modal a[href=#back]', installer.modal_back);
    $('#installer').on('click', '#modal a[href=#generate]', installer.modal_generate);
    $('#installer').on('click', '#modal a[href=#next]', function() {
      installer.switch_page(installer.page+1);
      installer.overlay.hide();
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

  $(document).on('click', '.download-ssh-key', function(e) {
    var key_type, key_filename, data;

    key_type = $(this).attr('data-key-type');
    key_filename = $(this).attr('data-key-filename');

    id = $(this).attr('id');
    data = $('#keypair-' + key_type).val();
    elem = download_as_file(key_filename, data);
    $('body').append(elem);
    elem.click();
  });

  function download_as_file(filename, data) {
    var elem, encoded_data;

    encoded_data = window.btoa(unescape(encodeURIComponent(data)));
    elem = document.createElement('a');
    elem.download = filename;
    elem.textContent = filename;
    elem.href = 'data:application/octet-stream;base64,' + encoded_data;
    return elem;
  }
});
