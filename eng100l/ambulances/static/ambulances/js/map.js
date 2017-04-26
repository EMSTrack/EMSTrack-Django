$(document).ready(function() {
	var mymap = L.map('live-map').setView([32.5149, -117.0382], 12);
	// Initialize marker icons.
	var ambulanceIcon = L.icon({
		iconUrl: '/static/icons/ambulance_icon.png',
		iconSize: [60, 60],
	});
	var ambulanceIconBlack = L.icon({
		iconUrl: '/static/icons/ambulance_icon_black.png',
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

	var ajaxUrl = "ambulance_info";

	var ambulanceMarkers = {};	// Store ambulance markers

	$.ajax({
		type: 'GET',
		url: ajaxUrl,
		success: function(arr) {
			$.each(arr, function(index, item) {
				// Red = active?
				if(item.status === "Active" ) {
					ambulanceMarkers[item.id] = L.marker([item.lat, item.long], {icon: ambulanceIcon})
					.bindPopup("<strong>" + item.id + "</strong><br/>" + item.status).addTo(mymap);
				}
				else {
					ambulanceMarkers[item.id] = L.marker([item.lat, item.long], {icon: ambulanceIconBlack})
					.bindPopup("<strong>" + item.id + "</strong><br/>" + item.status).addTo(mymap);
				}
				

				console.log(item.status);
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

	$('.collapse').on('show.bs.collapse', function() {
		let idStr = $(this).attr('id');
		let jsonUrl = '/ambulances/ambulance_info?id=' + idStr.slice(8);	// get ambulance id
		console.log(jsonUrl);
		$.getJSON(jsonUrl, function (data) {
			let detailsHtml = '<li class"list-group-list">Status: '
				+ data[0].status + '</li>'
				+ '<li class"list-group-list">Latitude: '
				+ data[0].lat + '</li>'
				+ '<li class"list-group-list">Longitude: '
				+ data[0].long + '</li>';
			$('.collapse').find('ul.list-group').html(detailsHtml);
		});
	});

	window.setInterval(function() {
		AjaxReq(ambulanceMarkers, ajaxUrl, ambulanceIcon, mymap);
	}, 1000);


	// Open popup on panel hover.
	$('.ambulance-panel').click(function(){
		var id = $(this).attr('id');

		var position = ambulanceMarkers[id].getLatLng();
		mymap.setView(position, 12);

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
		url: 'ambulance_info',
		success: function(arr) {
			$.each(arr, function (index, item) {
				// Create new ambulance markers if new ambulances are added
				if(typeof ambulanceMarkers[item.id] == 'undefined'){
					ambulanceMarkers[item.id] = L.marker([item.lat, item.long], {icon: ambulanceIcon})
					.bindPopup("<strong>" + item.id + "</strong><br/>" + item.status).addTo(mymap);
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
				ambulanceMarkers[item.id] = ambulanceMarkers[item.id].setLatLng([item.lat, item.long]).update();
				ambulanceMarkers[item.id]._popup.setContent("<strong>" + item.id + "</strong><br/>" + item.status);
			});
		}
	});
}