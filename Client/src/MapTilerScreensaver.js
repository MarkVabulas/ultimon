import * as mt from '@maptiler/sdk';
import { ColorRamp, TemperatureLayer, PrecipitationLayer, PressureLayer, RadarLayer, WindLayer } from "@maptiler/weather";

import "@maptiler/sdk/dist/maptiler-sdk.css";

class MapTilerScreensaver {
	constructor(apiConfig) {
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
		
		this._map.on('mouseout', (evt) => {
			if (evt && evt.originalEvent && !evt.originalEvent.relatedTarget) {
				$('#pointer-data').text("");
				this._pointerLngLat = null;
			}
		});

		this._map.on('mousemove', (e) => {
			this.updatePointerValue(e.lngLat);
		});
	}
	
	playAnimation(weatherLayer) {
		weatherLayer.animateByFactor(3*60*60);
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


	updatePointerValue(lngLat) {
		if (!this._lngLat)
			return;

		this._pointerLngLat = this._lngLat;
		const weatherLayer = this._weatherLayers[this._activeLayer]?.layer;
		const weatherLayerValue = this._weatherLayers[this._activeLayer]?.value;
		const weatherLayerUnits = this._weatherLayers[this._activeLayer]?.units;
		if (weatherLayer) {
			const value = weatherLayer.pickAt(this._lngLat.lng, this._lngLat.lat);
			if (!value) {
				$('#pointer-data').text("");
				return;
			}
			$('#pointer-data').text(`${value[weatherLayerValue].toFixed(1)}${weatherLayerUnits}`);
		}
	}

	changeWeatherLayer(type) {
		setTimeout(() => { 
			this.nextMap();
		}, 10000);
	  
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
			
			$("#variable-name").text(this._activeLayer);
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
			this.updatePointerValue(this._pointerLngLat);
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

	// Update the date time display
	refreshTime() {
	  	const weatherLayer = this._weatherLayers[this._activeLayer]?.layer;
	 	if (weatherLayer) {
			this._currentTime = weatherLayer.getAnimationTime();
			const d = weatherLayer.getAnimationTimeDate();
			$('#time-text').text(d.toUTCString());
			if (d < Date.now()) {
			 	$('#time-text').css('color', 'rgb(90, 90, 90, 90)');
			} else {
			  	$('#time-text').css('color', 'white');
			}
	  	}
	}
}

export default MapTilerScreensaver;