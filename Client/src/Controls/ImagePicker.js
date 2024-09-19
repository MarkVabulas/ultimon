
$('.imagepicker').on('data_update', function( event, data ) {
    var picker = $( this );
    var percent = data.value / 100.0;
    var possible_images = picker.children('img');
    var increment = possible_images.length / 100.0;
    var plus_minus = increment / 2.0;
    
    //console.log(`updating picker ${this.id} with value=${data.value} and ${possible_images.length} images`);
    
    for (let i=0; i<possible_images.length; i++) {
      if (increment*i-plus_minus < percent && percent <= increment*i + plus_minus) {
        $(possible_images[i]).show();
      } else {
        $(possible_images[i]).hide();
      }
    }
  });
  