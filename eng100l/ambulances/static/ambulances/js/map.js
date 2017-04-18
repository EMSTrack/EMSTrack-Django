$(document).ready(function() {
	var mymap = L.map('live-map').setView([32.5149, -117.0382], 12);
	// Initialize marker icons.
	var ambulanceIcon = L.icon({
		iconUrl: '/static/icons/ambulance_icon.png',
		iconSize: [60, 60],
	});
	var hospitalIcon = L.icon({
		iconUrl: '/static/icons/hospital_icon.png',
		iconSize: [40, 40]
	});

	// Add layer to map.
	L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token=pk.eyJ1IjoieWFuZ2Y5NiIsImEiOiJjaXltYTNmbTcwMDJzMzNwZnpzM3Z6ZW9kIn0.gjEwLiCIbYhVFUGud9B56w', {
		attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="http://mapbox.com">Mapbox</a>',
		maxZoom: 18,
		id: 'mapbox.streets',
		accessToken: 'pk.eyJ1IjoieWFuZ2Y5NiIsImEiOiJjaXltYTNmbTcwMDJzMzNwZnpzM3Z6ZW9kIn0.gjEwLiCIbYhVFUGud9B56w'
	}).addTo(mymap);

	// Add hospital marker.
	L.marker([32.506787, -116.963839], {icon: hospitalIcon}).addTo(mymap);

	var ajaxUrl = "api/ambulances";
	$('#refresh').click(function() {
		/*
		console.log('change url');
		console.log('click url is ' + ajaxUrl);
		if(ajaxUrl === 'https://yangf96.github.io/Cruz-Roja-Views/ambulances.json')
			ajaxUrl = 'https://yangf96.github.io/JSON-test/moreAmbulances.json';
		else
			ajaxUrl = 'https://yangf96.github.io/Cruz-Roja-Views/ambulances.json';
			*/
	});


	var ambulanceMarkers = {};	// Store ambulance markers

	$.ajax({
		type: 'GET',
		url: ajaxUrl,
		success: function(arr) {
			$.each(arr, function(index, item) {
				ambulanceMarkers[item.id] = L.marker([item.location.latitude, item.location.longitude], {icon: ambulanceIcon})
				.bindPopup("<strong>Ambulance " + item.id + "</strong><br/>" + item.status).addTo(mymap);
				// Bind id to icon
				ambulanceMarkers[item.id]._icon.id = item.id;
				// Collapse panel on icon hover.
				ambulanceMarkers[item.id].on('mouseover', function(e){
					$('#collapse' + this._icon.id).collapse('show');
					this.openPopup().on('mouseout', function(e){
						$('#collapse' + this._icon.id).collapse('hide');
						this.closePopup();
					});
				});  

			});
		}
	});

	window.setInterval(function() {
		AjaxReq(ambulanceMarkers, ajaxUrl, ambulanceIcon, mymap);
	}, 1000);


	// Open popup on panel hover.
	$('.ambulance-panel').click(function(){
		var id = $(this).attr('id');
		// Open popup for 2.5 seconds.
		ambulanceMarkers[id].openPopup();
		setTimeout(function(){
			ambulanceMarkers[id].closePopup();
		}, 2500);
	});
});

function AjaxReq(ambulanceMarkers, ajaxUrl, ambulanceIcon, mymap) {
	console.log('ajax request sent');
	console.log(ajaxUrl);
	$.ajax({
		type: 'GET',
		datatype: "json",
		url: ajaxUrl,
		success: function(arr) {
			$.each(arr, function (index, item) {
				// Create new ambulance markers if new ambulances are added
				if(typeof ambulanceMarkers[item.id] == 'undefined'){
					ambulanceMarkers[item.id] = L.marker([item.location.latitude, item.location.longitude], {icon: ambulanceIcon})
					.bindPopup("<strong>Ambulance " + item.id + "</strong><br/>" + item.status).addTo(mymap);
					// Bind id to icon
					ambulanceMarkers[item.id]._icon.id = item.id;
					// Collapse panel on icon hover.
					ambulanceMarkers[item.id].on('mouseover', function(e){
						$('#collapse' + this._icon.id).collapse('show');
						this.openPopup().on('mouseout', function(e){
							$('#collapse' + this._icon.id).collapse('hide');
							this.closePopup();
						});
					});  
				}
				// Update ambulance location
				ambulanceMarkers[item.id] = ambulanceMarkers[item.id].setLatLng([item.location.latitude, item.location.longitude]).update();
				ambulanceMarkers[item.id]._popup.setContent("<strong>Ambulance " + item.id + "</strong><br/>" + item.status);
			});
		}
	});
}