
$('.bar_graph').on('data_update', function( event, data ) {
    // Not implemented yet
    var bar_graph = $( this );
    bar_graph.text(data.value);
  });