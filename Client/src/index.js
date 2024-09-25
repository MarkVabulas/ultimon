// This import is what makes the magic happen, coming from the Server and listening for events
// WebSocketClient is also in charge of refreshing the browser if the server suggests it should take place
import {} from './Framework/WebSocketClient.js';

// Here we can include our different desired functionalities, if we design it properly, we can just include them 
// here and they will respond properly to when the values change (See LineGraph and ImagePicker for examples)
import {} from './Controls/LineGraph.js';
import {} from './Controls/ImagePicker.js';
import {} from './Controls/Label.js';

// Here we can add even more customization, which we have added the MapTiler when the WebSocketClient sees a disconnection
// By default, WebSocketClient will hide everything in the "live" when disconnected, and show the "disconnected" div tag.
// The opposite is true upon reconnection
// Ideally, these javascript files only talk to the html DOM, so we don't even need to add code for them anywhere else
import {} from './Addons/MapTilerScreensaver.js';
//import {} from './Addons/WebGLFluidBursts.js';
import {} from './Addons/AdvancingFronts.js';

$(function() {
    console.log('App is started!');
});
