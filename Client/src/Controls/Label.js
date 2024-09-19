$('.label').on('data_update', function( event, data ) {
    var label = $( this );
    var format = $( this ).data('format');
    if (format) {
      label.html(format.replace("{}", data.value));
    }
    else {
      label.html(data.value);
    }
  });
  