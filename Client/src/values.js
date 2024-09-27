// This import is what makes the magic happen, coming from the Server and listening for events
// WebSocketClient is also in charge of refreshing the browser if the server suggests it should take place
import {} from './Framework/WebSocketClient.js';
import { Tree } from './Framework/jsonTree.js';

var tree;
var complete_data = {};

$('body').on('data_update_full', function( event, data ) {
    try {
        let new_data = false;
        for (const [id, item_data] of Object.entries(data)) {
            if (!complete_data.hasOwnProperty(id)) {
                complete_data[id] = item_data;
                new_data = true;
            }
        }

        if (new_data) {
            console.log('new data arrived!');

            if (tree)
                tree.destroy();

            tree = new Tree(data, document.getElementById("tree")); 
        }   
    } catch (ex) {
      console.error('onSensorDataChange error: ', ex.stack);
    }
});

$(function() {

    console.log('App is started!');
});