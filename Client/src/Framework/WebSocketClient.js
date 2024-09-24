function convert(jsonObject){
  var msg = (typeof jsonObject == "object" ? jsonObject : JSON.parse(jsonObject));
  return msg;
}

function _eventToMessage(event, data) {
  if (data === undefined) {
    return JSON.stringify({event: event});
  } else {
    return JSON.stringify({event: event, data: data});
  }
}

class WebSocketClient {
  constructor(serverConfig) {
    this._serverConfig = serverConfig;

    this._ws = null;
    this._id = null;
    
    this._onConnectionOpen = () => {};
    this._onConnectionClose = () => {};
    this._onConnectionError = () => {};
    
    this._onSensorDataChange = () => {};
  }

  set onConnectionOpen(onConnectionOpen) {
    this._onConnectionOpen = onConnectionOpen;
  }

  set onConnectionClose(onConnectionClose) {
    this._onConnectionClose = onConnectionClose;
  }

  set onConnectionError(onConnectionError) {
    this._onConnectionError = onConnectionError;
  }

  set onSuggestRefresh(onSuggestRefresh) {
    this._onSuggestRefresh = onSuggestRefresh;
  }

  set onSensorDataChange(onSensorDataChange) {
    this._onSensorDataChange = onSensorDataChange;
  }

  get isConnected() {
    return this._id !== null;
  }

  get sessionId() {
    return this._id;
  }

  _retry_connection() {
    console.log('retrying connection...');
    setTimeout(() => {
      try {
        this.connect();
      }
      catch(ignore) {
      }
    }, 5000);
  }

  connect() {
    this._ws = new WebSocket(this._serverConfig.url);
    
    this._ws.onopen = () => {
      console.log('Server connected');
      let data = {
        data: this._serverConfig.data,
        password: this._serverConfig.password
      };
      try {
        this._ws.send(_eventToMessage('connect', data));
      } catch (error) {
        console.log(error.message);
      }
    }

    this._ws.onclose = (event) =>{
      //console.log('Server disconnect event: ' + event.type);
      this._onConnectionClose();

      this._retry_connection();
    }

    this._ws.onerror = (event) => {
      //console.log('Server error event: ' + event.type);
      this._onConnectionError(event);
    }

    this._ws.onmessage = async event => {
      try {
        let data = JSON.parse(event.data);
        let eventName = data.event;
        let deep_data = convert(data.data);

        //console.log(eventName + ', data=' + deep_data);

        switch (eventName)
        {
        case 'welcome':                                     this._onWelcome(deep_data);                break;
        case 'suggest-refresh':                             this._onSuggestRefresh();                  break;
        case 'sensor-data':                                 this._onSensorDataChange(deep_data);       break;
        default:
          console.log(eventName + ', data=' + JSON.stringify(deep_data));
        }
      } catch(e) {
        console.error('onmessage error: ', e.stack);
      }
    };
  }

  _onWelcome(data) {
    if (data['id'] === '') {
      this._onConnectionError('Invalid password or invalid protocol version');
    } else {
      console.log('onWelcome session id: ' + data['id']);
      this._id = data['id'];
      this._onConnectionOpen(data['id']);
    }
  }

  disconnect() {
    this._disconnectEvents();
    this._id = null;
    this._ws.close();
    this._ws = null;
  }

  _disconnectEvents() {
    this._ws.onopen = () => {};
    this._ws.onclose = () => {};
    this._ws.onerror = () => {};
    this._ws.onmessage = () => {};
  }
}

$(function() {
  const serverConfiguration = {
    url: '/sensor_data',
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

export default WebSocketClient;
