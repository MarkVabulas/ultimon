import * as mt from '@maptiler/sdk';
import { ColorRamp, TemperatureLayer, PrecipitationLayer, PressureLayer, RadarLayer, WindLayer } from "@maptiler/weather";

import "@maptiler/sdk/dist/maptiler-sdk.css";

/*
<div id="mapTiler" style="z-index: -50; left:2%; width:96%; top:2%; height:96%;">
	<div id="weather_map"></div>
	<div id="time-info">
		<div id="map-type"></div>
		<span id="time-delta-text"></span>
		<span id="time-text"></span>
	</div>
</div>
*/

class MapTilerScreensaver {
	constructor(apiConfig) {
		if (!document.getElementById('weather_map')) {
			
			let weather_map = document.createElement('div');
			weather_map.id = 'weather_map';
			document.getElementById('background').appendChild(weather_map);
			
			let time_info = document.createElement('div');
			time_info.id = 'time-info';
			document.getElementById('background').appendChild(time_info);
			
			let map_type = document.createElement('div');
			map_type.id = 'map-type';
			document.getElementById('time-info').appendChild(map_type);
			
			let time_delta_text = document.createElement('span');
			time_delta_text.id = 'time-delta-text';
			document.getElementById('time-info').appendChild(time_delta_text);
			
			let time_text = document.createElement('span');
			time_text.id = 'time-text';
			document.getElementById('time-info').appendChild(time_text);
		}

		this._apiConfig = apiConfig;

		this._pointerLngLat = null;
		this._activeLayer = null;
		this._isPlaying = false;
		this._currentTime = null;

		mt.config.apiKey = this._apiConfig.apiKey;
		mt.config.primaryLanguage = mt.Language.LOCAL;

		this._weatherLayers = {
			"precipitation": {
			  "layer": null,
			  "value": "value",
			  "units": " mm"
			},
			/*
			"pressure": {
			  "layer": null,
			  "value": "value",
			  "units": " hPa"
			},
			*/
			"radar": {
			  "layer": null,
			  "value": "value",
			  "units": " dBZ"
			},
			"temperature": {
			  "layer": null,
			  "value": "value",
			  "units": "°"
			},
			"wind": {
			  "layer": null,
			  "value": "speedMetersPerSecond",
			  "units": " m/s"
			}
		};
		
		console.log(`MapTilerScreensaver [${JSON.stringify(apiConfig)}]`);

		this._map = new mt.Map({
			container: 'weather_map', // container's id or the HTML element in which SDK will render the map
			center: [6.475, 44.0], // starting position [lng, lat]
			zoom: 7.05, // starting zoom
			style: mt.MapStyle.DATAVIZ.DARK,
			source: this._apiConfig.mapUrl
		});

		this._map.on('load', () => {
			this._map.setPaintProperty("Water", 'fill-color', "rgba(0, 0, 0, 0.4)");
			const weatherLayer = this.nextMap();
			this.playAnimation(weatherLayer);
		});
	}
	
	playAnimation(weatherLayer) {
		weatherLayer.animateByFactor(60*60);
		this._isPlaying = true;
	}

	pauseAnimation(weatherLayer) {
		weatherLayer.animateByFactor(0);
		this._isPlaying = false;
	}

	nextMap() {
		const keys = Object.keys(this._weatherLayers);
		const rand = Math.floor(Math.random() * keys.length) % keys.length;
		return this.changeWeatherLayer(keys[rand]);
	}

	changeWeatherLayer(type) {
		setTimeout(() => { 
			this.nextMap();
		}, 10000 + Math.random() * 10000);
	  
		console.log(`changing map from [${this._activeLayer}] to [${type}]`);

		if (type != this._activeLayer) {
			if (this._activeLayer) {
				const activeWeatherLayer = this._weatherLayers[this._activeLayer]?.layer;
				if (activeWeatherLayer && this._map.getLayer(activeWeatherLayer.id)) {
					this._map.setLayoutProperty(activeWeatherLayer.id, 'visibility', 'none');
				}
			}
		
			this._activeLayer = type;
		
			const weatherLayer = this._weatherLayers[this._activeLayer].layer || this.createWeatherLayer(this._activeLayer);
			if (weatherLayer && this._map.getLayer(weatherLayer.id)) {
				this._map.setLayoutProperty(weatherLayer.id, 'visibility', 'visible');
			} else {
				this._map.addLayer(weatherLayer, 'Water');
			}
			
			$("#map-type").text(this._activeLayer);
			this.changeLayerAnimation(weatherLayer);
			return weatherLayer;
		}
	}
	
	changeLayerAnimation(weatherLayer) {
		weatherLayer.setAnimationTime(this._currentTime);
		if (this._isPlaying) {
			this.playAnimation(weatherLayer);
		} else {
			this.pauseAnimation(weatherLayer);
		}
	}


	createWeatherLayer(type) {
		let weatherLayer = null;
		switch (type) {
			case 'precipitation':
				weatherLayer = new PrecipitationLayer();
			break;
			/*
			case 'pressure':
				weatherLayer = new PressureLayer({
					opacity: 0.8
				});
			break;
			*/
			case 'radar':
				weatherLayer = new RadarLayer({
					opacity: 0.8
				});
			break;
			case 'temperature':
				weatherLayer = new TemperatureLayer({
					colorramp: ColorRamp.builtin.JET.scale(0, 30)
				});
			break;
			case 'wind':
				weatherLayer = new WindLayer({
					colorramp: ColorRamp.builtin.VELOCITY_BLUE.scale(0, 20)
				});
			break;
		}

		// Called when the animation is progressing
		weatherLayer.on("tick", event => {
			this.refreshTime();
		});

		// Called when the time is manually set
		weatherLayer.on("animationTimeSet", event => {
			this.refreshTime();
		});

		// Event called when all the datasource for the next days are added and ready.
		// From now on, the layer nows the start and end dates.
		weatherLayer.on("sourceReady", event => {
			weatherLayer.setAnimationTime(this._currentTime);
			this.changeLayerAnimation(weatherLayer);
		});

		this._weatherLayers[type].layer = weatherLayer;
		return weatherLayer;
	}

	parseMillisecondsIntoReadableTime(milliseconds){
		var sign = (milliseconds < 0) ? '-' : '+';
		milliseconds = Math.abs(milliseconds);

		//Get hours from milliseconds
		var hours = milliseconds / (1000*60*60);
		var absoluteHours = Math.floor(hours);
		var h = absoluteHours > 9 ? absoluteHours : '0' + absoluteHours;
	  
		//Get remainder from hours and convert to minutes
		var minutes = (hours - absoluteHours) * 60;
		var absoluteMinutes = Math.floor(minutes);
		var m = absoluteMinutes > 9 ? absoluteMinutes : '0' +  absoluteMinutes;
	  
		return sign + h + 'h ' + m + 'm';
	  }

	// Update the date time display
	refreshTime() {
	  	const weatherLayer = this._weatherLayers[this._activeLayer]?.layer;
	 	if (weatherLayer) {
			this._currentTime = weatherLayer.getAnimationTime();
			const d = weatherLayer.getAnimationTimeDate();
			const timeDelta = this.parseMillisecondsIntoReadableTime(d - Date.now());
			$('#time-delta-text').text(timeDelta);
			$('#time-text').text(d.toUTCString());
			if (d < Date.now()) {
			 	$('#time-delta-text').css('color', 'rgb(96, 96, 96)');
			} else {
			  	$('#time-delta-text').css('color', 'rgb(192, 192, 192)');
			}
	  	}
	}
}

var userDataApiKey = '';
var mapTilerURL = '';
var mapTiler;

$(document).bind('user_data', (_, data) => {
	if (userDataApiKey != data['MapTilerAPIKey']) {
		userDataApiKey = data['MapTilerAPIKey'];
		mapTilerURL = data['MapTilerURL'];

		mapTiler = new MapTilerScreensaver({
			apiKey: userDataApiKey,
			mapUrl: mapTilerURL
		});
	}
});

export default MapTilerScreensaver;
