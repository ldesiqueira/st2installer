var installer = {
  i18n: {
    next: "Next",
    last: "Get started!"
  },
  page: 0, 
  chatops: 0,
  switch_page: function(page) {
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
    if (installer.page == $('.page').length-1) {
      $('#step-next').text(installer.i18n.last);
    } else {
      $('#step-next').text(installer.i18n.next);
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
  validate: function(page) {
    return true;
  },
  init: function() {
    installer.switch_page(0);
    installer.switch_chatops(0);

    $('#installer').submit(function(e) {
      if (installer.validate(installer.page)) {
        if (installer.page == $('.page').length-1) {
          return;
        } else {
          installer.switch_page(installer.page+1);
        } 
      }
      e.preventDefault();
      return false;
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