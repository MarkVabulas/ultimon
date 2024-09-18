const { DrawGraphDefault } = require('./DrawGraphDefault.js');

import WebSocketClient from './WebSocketClient.js';
import MapTilerScreensaver from './MapTilerScreensaver.js';
import {} from './WebGLFluidBursts.js';

var graph_history = {}
var graph_offset = {}
var screensaver = null;

$(function() {
  screensaver = new MapTilerScreensaver({
    apiKey: 'oJfCFFR9g2SbLCtLiAVQ',
    mapUrl: 'https://api.maptiler.com/maps/54ea2e55-d319-42c6-a2c1-1e0fe923fef8/?key=oJfCFFR9g2SbLCtLiAVQ'
  });

  $('toggle').on('data_update', function( event, data ) {
    var toggle = $( this );
    if (data == true) {
      toggle.css('color', 'green');
    } else {
      toggle.css('color', 'red');
    }
  });

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

  $('.arc_guage').on('data_update', function( event, data ) {
    var guage = $( this );
    guage.text(data.value);
  });

  $('.line_graph').on('data_update', function( event, data ) {
    var line_graph = $( this );
    line_graph.text(data.value);

    if (!(this.id in graph_history)) {
      graph_history[this.id] = [];
    }
    if (!(this.id in graph_offset)) {
      graph_offset[this.id] = 22;
    }

    graph_history[this.id].unshift(data.value);
    if (graph_history[this.id].length > 128)
      graph_history[this.id].pop();

    //console.log('updated graph ' + this.id + ': ' + graph_history[this.id]);
    
    var linewidth = $(this).data('linewidth');
    if (linewidth=== null) linewidth = 2;

    var graphcolor = $(this).data('graphcolor');
    if (graphcolor=== null) graphcolor = '#FFFFFF';

    var minimum = $(this).data('min');
    if (minimum=== null) minimum = 0;
    
    var maximum = $(this).data('max');
    if (maximum=== null) maximum = 100;

    var showvalue = $(this).data('showvalue');
    if (showvalue === null) showvalue = true;

    var showscale = $(this).data('showscale');
    if (showscale === null) showscale = true;

    DrawGraphDefault(
      this.id, graph_history[this.id], graph_offset[this.id], "LG"
       , 1, linewidth, this.clientHeight/2-1
       , minimum, maximum
       , false
       , false
       , false, "#000000"
       , false, "#666666"
       , true, "#003C00"
       , graphcolor
       , showvalue
       , showscale, "Segoe UI Variable Small Light", graphcolor, "8pt", "normal", "normal", "normal", false);
    
    graph_offset[this.id] -= 1;
    if (graph_offset[this.id] < 0)
      graph_offset[this.id] = 24 + graph_offset[this.id];
    if (graph_offset[this.id] < 0)
      graph_offset[this.id] = 22;

  });

  $('.bar_graph').on('data_update', function( event, data ) {
    var bar_graph = $( this );
    bar_graph.text(data.value);
  });
  
  const serverConfiguration = {
    url: 'ws://'+location.host+'/sensor_data',
    data: {}, // Client custom data
    password: 'UltimateSensorMonitor'
  };
  let sensorClient = new WebSocketClient(serverConfiguration);
  sensorClient.onConnectionOpen = () =>
  {
    $('#disconnected').hide();
    $('#live').show();
  };
  sensorClient.onConnectionClose = async () =>
  {
    $('#live').hide();
    $('#disconnected').show();
  };
  sensorClient.onConnectionError = message => {};
  sensorClient.onSuggestRefresh = () => {
    console.log('refresh suggested');
    
    window.location = window.location.href;
  }
  sensorClient.onSensorDataChange = (data) => {
    //console.log('onSensorDataChange data = ' + data);

    for (const [id, item_data] of Object.entries(data)) {
      //console.log(`${id} : ${JSON.stringify(item_data)}`); // Log the key and its corresponding value

      var exact_matches = $('#' + id);
      if (exact_matches.length > 0) {
        exact_matches.trigger('data_update', item_data);
      } else {
        const duplicated_matches = `[id*="${id}"]`;
        $(duplicated_matches).trigger('data_update', item_data);
      }
    }
  };

  (async function() {
    await sensorClient.connect();
  })();

});
