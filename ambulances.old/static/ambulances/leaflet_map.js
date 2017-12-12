
// Create map
 var MyMap = function(options) {
 	console.log("I'm in!");

	this.options = {
		url: 'https://api.mapbox.com/styles/v1/kalmande/ciufxmct1008j2irucek2fila/tiles/256/{z}/{x}/{y}?access_token=pk.eyJ1Ijoia2FsbWFuZGUiLCJhIjoiY2l1ZnZqZWdqMDBnZzJ4bnlpeGhkd2U2dSJ9.d-0JrK8uGLFPua9Q3pGKGw',
		start_options: {
			attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="http://mapbox.com">Mapbox</a>',
			maxZoom: 18,
			id: 'map',
		},
		map_id: 'map',
		lat: 32.523,
		lng: -117.096623,
		zoom: 13
	};

	this.map = L.map(this.options.map_id, {
		zoomControl: false
	}).setView([this.options.lat, this.options.lng], this.options.zoom);

	// options layer
	L.tileLayer(this.options.url,
		this.options.start_options).addTo(this.map);

	// zoom control positioning
	L.control.zoom({
        position: 'topright'
      }).addTo(this.map);
}

// custom icon settings
var ambulance_icon = L.icon({
	iconUrl: '/static/icons/ambulance_icon.png',

	iconSize: [50, 50],
	iconAnchor: [25, 0],
	popupAnchor: [25, 25]
});


var MyMarkers = function (options) {
	//call parent
	MyMap.call(this, options);

	//store marker id's
	this.markerIdMap = {};

	//create markers layer
	this.markers = L.layerGroup();
}

MyMarkers.prototype = Object.create(MyMap.prototype);
MyMarkers.prototype.constructor = MyMarkers;

var ambulance_marker;

// Add marker function

MyMarkers.prototype.addMarker = function(lat, lng, license, fun) {

	ambulance_marker = L.marker([lat, lng], {icon: ambulance_icon}).addTo(this.map);
	//ambulance_marker.bindPopup("Latitude: " + lat + "<br /> " +"Longitude: " + lng + "<br />" + "License Plate: " + license + "<br />").openPopup();
	
	// add marker to mapping
	this.markerIdMap[ambulance_marker._leaflet_id] = license;

	return ambulance_marker;
}



// Update marker location
MyMarkers.prototype.updateMarker = function(lat, lng, status) {
	console.log("updating...", lat, lng, status);
	//var marker = L.marker([lat, lng], {icon: ambulance_icon}).update(this.map);
	ambulance_marker.setLatLng([lat, lng]).update();

}


// Center view on selected ambulance
MyMarkers.prototype.panToAmbulance = function(lat, lng) {
	console.log("In panToAmbulance function");
	this.map.setView([lat, lng], 16);
}

// Updatuppopip
MyMarkers.prototype.addPopup = function(onM) {
  alert("popup works");
}
