var i18n = {
  next: "Next",
  back: "Back",
  last: "Get started!",
  required: "Required field.",
  fqdn: "Should be an IP address or a FQDN.",
  ssl_required: "Both keys are required if not using a self-signed certificate.",
  complexity: "Complexity requirements are not met.",
  confirmation: "Passwords do not match.",
  slack: "API token is required for Slack integration.",
  hipchat: "JID and password are required for HipChat integration.",
  xmpp: "Username, password and at least one room are required for XMPP integration.",
  irc: "Server and at least one room are required for IRC integration.",
  flowdock: "All fields are required for Flowdock integration."
};
var installer = {
  page: 0, 
  chatops: 0,
  errors: 0,
  switch_page: function(page) {
    if (page <= installer.page || installer.validate(installer.page)) {
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
      if (page == 0) {
        $('#step-back').hide();
      } else {
        $('#step-back').show();
      }
    }
  },
  switch_chatops: function(tab) {
    $('#chatops-tabs li')
      .removeClass('active')
      .eq(tab)
        .addClass('active');
    $('#chatops-navigation li a')
      .removeClass('active')
      .eq(tab)
        .addClass('active');
  },
  append_error: function(el, error) {
    installer.errors += 1;
    el.after('<p class="error">'+error+'</p>');
  },
  validate: function(page) {

    installer.errors = 0;
    $('p.error').remove();

    if (installer.page == 0) {

      var hostname = $('#text-hostname');
      if (hostname.val().trim().length == 0) {
        installer.append_error(hostname, i18n.required);
      } else if (!/^[0-9a-z\.\-]+$/.test(hostname.val())) {
        installer.append_error(hostname, i18n.fqdn);
      }

      if ($('#radio-selfsigned-false').is(':checked') && 
          ($('#textarea-public').val().trim().length==0 ||
           $('#textarea-private').val().trim().length==0)) {
        installer.append_error($('#ssl'), i18n.ssl_required);  
      }

    } else if (installer.page == 1) {

      var password = $('#text-password-1');
      if (password.val().trim().length == 0) {
        installer.append_error(password, i18n.required);
      } else if (!/^(?!^[0-9]*$)(?!^[a-zA-Z]*$)^([a-zA-Z0-9]{8,20})$/.test(password.val())) {
        installer.append_error(password, i18n.complexity);
      }

      var password_confirmation = $('#text-password-2');
      if (password.val() != password_confirmation.val()) {
        installer.append_error(password_confirmation, i18n.confirmation);
      }

      var username = $('#text-username');
      if (username.val().trim().length==0) {
        installer.append_error(username, i18n.required);
      }

    } else if (installer.page == 2) {

      if ($('#checkbox-flowdock-enable').is(':checked')) {
        if ($('#text-flowdock-token').val().trim().length==0 ||
            $('#text-flowdock-email').val().trim().length==0 ||
            $('#text-flowdock-password').val().trim().length==0) {
          installer.append_error($('label[for=checkbox-flowdock-enable]'), i18n.flowdock);
          installer.switch_chatops(5);
        }
      }
      if ($('#checkbox-irc-enable').is(':checked')) {
        if ($('#text-irc-server').val().trim().length==0 ||
            $('#text-irc-rooms').val().trim().length==0) {
          installer.append_error($('label[for=checkbox-irc-enable]'), i18n.irc);
          installer.switch_chatops(4);
        }
      }
      if ($('#checkbox-xmpp-enable').is(':checked')) {
        if ($('#text-xmpp-rooms').val().trim().length==0 ||
            $('#text-xmpp-username').val().trim().length==0 ||
            $('#text-xmpp-password').val().trim().length==0) {
          installer.append_error($('label[for=checkbox-xmpp-enable]'), i18n.xmpp);
          installer.switch_chatops(3);
        }
      }
      if ($('#checkbox-hipchat-enable').is(':checked')) {
        if ($('#text-hipchat-jid').val().trim().length==0 ||
            $('#text-hipchat-password').val().trim().length==0) {
          installer.append_error($('label[for=checkbox-hipchat-enable]'), i18n.hipchat);
          installer.switch_chatops(2);
        }
      }
      if ($('#checkbox-slack-enable').is(':checked')) {
        if ($('#text-slack-token').val().trim().length==0) {
          installer.append_error($('label[for=checkbox-slack-enable]'), i18n.slack);
          installer.switch_chatops(1);
        }
      }

    }

    if (installer.errors > 0) {
      return false;
    }
    return true;

  },
  init: function() {
    installer.switch_page(0);
    installer.switch_chatops(0);

    $('#installer').submit(function(e) {
      if (installer.page == $('.page').length-1 && installer.validate(installer.page)) {
        return;
      } else {
        installer.switch_page(installer.page+1);
      } 
      e.preventDefault();
      return false;
    });
    $('#step-back').click(function() {
      installer.switch_page(installer.page-1);
    });
    $('#step-next').click(function() {
      if (installer.page == $('.page').length-1) {
        $('#installer').submit();
      } else {
        installer.switch_page(installer.page+1);
      }
    });

    $('#total-steps').text($('.page').length);

    $('#radio-selfsigned-false').on('change', function() {
      $('#ssl').show()
    });

    $('#radio-selfsigned-true').on('change', function() {
      $('#ssl').hide()
    });

    $('#chatops-navigation li a').on('click', function() {
      installer.switch_chatops($('#chatops-navigation a').index(this));
      return false;
    });

  }
}

$(function() {
  installer.init();
});