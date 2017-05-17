var ambulanceMarkers = {};	// Store ambulance markers

var statusWithMarkers = {}; //A JSON to map statuses with arrays of ambulances with that status.

// Initialize marker icons.
var ambulanceIcon = L.icon({
		iconUrl: '/static/icons/ambulance_icon.png',
		iconSize: [60, 60],
});
var ambulanceIconBlack = L.icon({
	iconUrl: '/static/icons/ambulance_icon_black.png',
	iconSize: [60, 60],
});
var ambulanceIconBlue = L.icon({
	iconUrl: '/static/icons/ambulance_blue.png',
	iconSize: [60, 40],
});
var hospitalIcon = L.icon({
	iconUrl: '/static/icons/hospital_icon.png',
	iconSize: [40, 40]
});

var ajaxUrl = "api/ambulances";

/**
 * Ambulance statuses 
 */
var STATUS_IN_SERVICE = "In Service";
var STATUS_AVAILABLE = "Available";
var STATUS_OUT_OF_SERVICE = "Out of service";

// Ajax update frequency (in milliseconds)
var UPDATE_FREQUENCY = 1000;

/**
 * This is a handler for when the page is loaded.
 */
$(document).ready(function() {
	var mymap = L.map('live-map').setView([32.5149, -117.0382], 12);


	// Add layer to map.
	L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token=pk.eyJ1IjoieWFuZ2Y5NiIsImEiOiJjaXltYTNmbTcwMDJzMzNwZnpzM3Z6ZW9kIn0.gjEwLiCIbYhVFUGud9B56w', {
		attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="http://mapbox.com">Mapbox</a>',
		maxZoom: 18,
		id: 'mapbox.streets',
		accessToken: 'pk.eyJ1IjoieWFuZ2Y5NiIsImEiOiJjaXltYTNmbTcwMDJzMzNwZnpzM3Z6ZW9kIn0.gjEwLiCIbYhVFUGud9B56w'
	}).addTo(mymap);

	// Add hospital marker.
	L.marker([32.506787, -116.963839], {icon: hospitalIcon}).addTo(mymap);

    // Add the drawing toolbar and the layer of the drawings.
	var drawnItems = new L.FeatureGroup();
    mymap.addLayer(drawnItems);
    var drawControl = new L.Control.Draw({
        edit: {
            featureGroup: drawnItems
        }
    });
    mymap.addControl(drawControl);
    
    // Event handler for when something is drawn. Only handles 
    // when a new drawing is made for now.
    mymap.on(L.Draw.Event.CREATED, function (e) {
    	var type = e.layerType;
        layer = e.layer;
   		if (type === 'marker') {
       	// Do marker specific actions
   		}
   		// Do whatever else you need to. (save to db; add to map etc)
   		mymap.addLayer(layer);
	});

    // Create ambulance grid (move somewhere else if not appropriate here)
    createAmbulanceGrid(mymap);

    // Update the ambulances on the map.
   	updateAmbulances(mymap);

    // Calling for ambulance updates every second.
	window.setInterval(function() {
		updateAmbulances(mymap);
	}, UPDATE_FREQUENCY);


	// Open popup on panel click.
	$('.ambulance-panel').click(function(){
		var id = $(this).attr('id');

		// Center icon on map
		var position = ambulanceMarkers[id].getLatLng();
		mymap.setView(position, 12);

		// Open popup for 2.5 seconds.
		ambulanceMarkers[id].openPopup();
		setTimeout(function(){
			ambulanceMarkers[id].closePopup();
		}, 2500);
	});

	// Update panel details on collapse
	$('.collapse').on('shown.bs.collapse', function() {
		let ambulance_id = this.id.slice(6);	// extract id from panel id
		let getAmbulanceUrl = 'api/ambulances/' + ambulance_id;
		$.get(getAmbulanceUrl, function(data) {
			//console.log(JSON.stringify(data));
			let liElement = '<li class="list-group-list">';
			$('#panel_'+ambulance_id).find('.list-group').html(liElement + "Status: " + data.status + '</li>'
				+ liElement + "Latitude: " + data.location.latitude + '</li>'
				+ liElement + "Longitude: " + data.location.longitude + '</li>'
				+ liElement + "Updated!" + '</li>');
		});
	});

	// Submit form
	$('#dispatchForm').submit(function(e) {
		e.preventDefault();
		postDispatchCall();
	})

});

var firstUpdate = true; // Flags if this is the first update to the map (initial update).
var layergroups = {}; // The layer groups that will be part of the map.
/*
 * updateAmbulances updates the map with the new ambulance's status.
 * @param mymap is the map UI.
 * @return void.
 */
function updateAmbulances(mymap) {
	console.log('ajax request sent');
	$.ajax({
		type: 'GET',
		datatype: "json",
		url: ajaxUrl,
		success: function(arr) {
			
			statusWithMarkers = {}; // clear all statuses from previous ajax call.
			var i = 0;
			$.each(arr, function(index, item) {
				// Update ambulance grid
				updateAmbulanceGrid(item.id);

				console.log("Status: " + item.status);
				// set icon by status
				let coloredIcon = ambulanceIcon;
				if(item.status === STATUS_AVAILABLE)
					coloredIcon = ambulanceIconBlue;
				if(item.status === STATUS_OUT_OF_SERVICE)
					coloredIcon = ambulanceIconBlack;

				if(typeof ambulanceMarkers[item.id] == 'undefined' ){
					// If ambulance marker doesn't exist
					ambulanceMarkers[item.id] = L.marker([item.location.latitude, item.location.longitude], {icon: coloredIcon})
					.bindPopup("<strong>Ambulance " + item.id + "</strong><br/>" + item.status).addTo(mymap);
			    }
			    else {
			    	// If ambulance markers exist

			    	// Remove existing marker
					mymap.removeLayer(ambulanceMarkers[item.id]);
					
					// Re-add it but with updated ambulance icon
					ambulanceMarkers[item.id] = L.marker([item.location.latitude, item.location.longitude], {icon: coloredIcon})
					.bindPopup("<strong>Ambulance " + item.id + "</strong><br/>" + item.status).addTo(mymap);
			    }

			    // Bind id to icons
				ambulanceMarkers[item.id]._icon.id = item.id;
				// Collapse panel on icon hover.
				ambulanceMarkers[item.id].on('mouseover', function(e){
					// open popup bubble
					this.openPopup().on('mouseout', function(e){
						this.closePopup();
					});

					// update details panel
					updateDetailPanel(item.id);
				});

			    // Update ambulance location
				ambulanceMarkers[item.id] = ambulanceMarkers[item.id].setLatLng([item.location.latitude, item.location.longitude]).update();
				ambulanceMarkers[item.id]._popup.setContent("<strong>Ambulance " + item.id + "</strong><br/>" + item.status);

				//Add to a map to differentiate the layers between statuses.
				if(statusWithMarkers[item.status]){
					statusWithMarkers[item.status].push(ambulanceMarkers[item.id]);
				}
				else{
					statusWithMarkers[item.status] = [ambulanceMarkers[item.id]];
				}			 
			});
			
			// This is for the first update of the map.
			if(firstUpdate){
				console.log("FIRST UPDATE!");
				// Add the checkbox on the top right corner for filtering.
				var container = L.DomUtil.create('div', 'filter-options');

				//Generate HTML code for checkboxes for each of the statuses.
				var filterHtml = "";
				$.get('api/status', function(statuses) {
					statuses.forEach(function(status){
						if(statusWithMarkers[status.name] !== undefined) {
							layergroups[status.name] = L.layerGroup(statusWithMarkers[status.name]);
							layergroups[status.name].addTo(mymap);
						}
						filterHtml += '<div class="checkbox"><label><input class="chk" data-status="' + status.name + '" type="checkbox" value="">' + status.name + "</label></div>";
					});
					// Append html code on success callback function
					container.innerHTML = filterHtml;
					// Initialize checked to true for all statuses.
					$('.chk').attr('checked', true);
				});

				// Add the checkboxes.
				var customControl = L.Control.extend({
 
  					options: {
    					position: 'topright' 
    					//control position - allowed: 'topleft', 'topright', 'bottomleft', 'bottomright'
  					},
 
  					onAdd: function (map) {
    					return container;
 					}
 
				 });
				 mymap.addControl(new customControl());

				 firstUpdate = false;

				 // Listener to see if a click on a checkbox leads to a check. If so,
				 // remove the layer from the map.
				 $('.chk').each(function(){
				 	console.log(this);
				 	$(this).change(function(){
				 		    console.log("Clicked!!!");
                			if(!($(this).is(':checked'))){
                				console.log("Clicked!");
                				var layersToRemove = statusWithMarkers[this.dataset.status];
                				console.log(layersToRemove);
                				for(var i = 0; i < layersToRemove.length; i++){
                					mymap.removeLayer(layersToRemove[i]);
                				}
                			}
				 	});

			    });


			}
			else{
				// Goes through each layer group and adds or removes accordingly.
				Object.keys(layergroups).forEach(function(key){
					layergroups[key].clearLayers();
					for(var i = 0; i < statusWithMarkers[key].length; i++){
						// Add the ambulances in the layer if it is checked.
						if($(".chk[data-status='" + key + "']").is(':checked')){
							layergroups[key].addLayer(statusWithMarkers[key][i])
						}
						// Remove from layer if it is not checked.
						else{
							layergroups[key].removeLayer(statusWithMarkers[key][i]);
							mymap.removeLayer(statusWithMarkers[key][i]);
						}
					}

			});

			}		

		}
	});
}

/*
 * updateDetailPanel updates the detail panel with the ambulance's details.
 * @param ambulanceId is the unique id used in the ajax call url.
 * @return void.
 */
 function updateDetailPanel(ambulanceId) {
 	let apiAmbulanceUrl = 'api/ambulances/' + ambulanceId;
 	console.log(apiAmbulanceUrl);
 	$.get(apiAmbulanceUrl, function(data) {
		$('.ambulance-detail').html("Ambulance: " + data.id + "<br/>" +
			"Status: " + data.status + "<br/>" + 
			"Priority: " + data.priority);
	});
 }

function onGridButtonClick(ambulanceId, mymap) {
	return function(e) {
		// Update detail panel
		updateDetailPanel(ambulanceId);

		// Center icon on map
		var position = ambulanceMarkers[ambulanceId].getLatLng();
		mymap.setView(position, 12);

		// Open popup for 2.5 seconds.
		ambulanceMarkers[ambulanceId].openPopup();
		setTimeout(function(){
			ambulanceMarkers[ambulanceId].closePopup();
		}, 2500);

	}
}

/*
 * createAmbulanceGrid creates the ambulance grid using the data from the server (status indicated by color of button, ID of ambulance on buttons)
 *
 */
function createAmbulanceGrid(mymap) {
	$.get('api/ambulances/', function(data) {
		var i, ambulanceId;
		//console.log(data);
		for(i = 0; i < data.length; i++) {
			ambulanceId = data[i].id;
			ambulanceLicensePlate = data[i].license_plate;
			console.log(ambulanceId);
			console.log(ambulanceLicensePlate);
			ambulanceStatus = data[i].status;
			if(ambulanceStatus === STATUS_AVAILABLE) {
				$('#ambulance-grid').append('<button type="button"' + ' id="' + 'grid-button' + ambulanceId + '" ' + 'class="btn btn-success" style="margin: 5px 5px;">' + ambulanceLicensePlate + '</button>');
				$('#ambulance-selection').append('<label><input type="checkbox" name="ambulance_assignment" value="' + ambulanceId + '"> Ambulance # ' + ambulanceLicensePlate + ' </label><br/>');
			}
			if(ambulanceStatus === STATUS_OUT_OF_SERVICE)
				$('#ambulance-grid').append('<button type="button"' + ' id="' + 'grid-button' + ambulanceId + '" ' + 'class="btn btn-default" style="margin: 5px 5px;">' + ambulanceLicensePlate + '</button>');
			if(ambulanceStatus === STATUS_IN_SERVICE)
				$('#ambulance-grid').append('<button type="button"' + ' id="' + 'grid-button' + ambulanceId + '" ' + 'class="btn btn-danger" style="margin: 5px 5px;">' + ambulanceLicensePlate + '</button>');
		
			// Open popup on panel click.
			// For some reason, only works when I create a separate function as opposed to creating a function within the click(...)
			$('#grid-button' + ambulanceId).click(onGridButtonClick(ambulanceId,mymap));
		}
	});
}

/*
 * updateAmbulanceGrid updates the ambulance grid. Will be called in AJAX call to update grid dynamically
 *
 */
function updateAmbulanceGrid(ambulanceId) {
 	let apiAmbulanceUrl = 'api/ambulances/' + ambulanceId;

 	$.get(apiAmbulanceUrl, function(data) {
		var buttonId = "#grid-button" + data.id;

		// console.log(buttonId);
		// Updating button license plate identifier dynamically
		$(buttonId).html(data.license_plate);

		// Updated button color/status dynamically
		if(data.status === STATUS_AVAILABLE) 
			$(buttonId).attr( "class", "btn btn-success" );
		if(data.status === STATUS_OUT_OF_SERVICE)
			$(buttonId).attr( "class", "btn btn-default" );
		if(data.status === STATUS_IN_SERVICE)
			$(buttonId).attr( "class", "btn btn-danger" );
		
	});
}

/*
 * postDispatchCall makes an ajax post request to post dispatched ambulance.
 * @param void.
 * @return void.
 */
 function postDispatchCall() {
 	var formData = {};
 	var assigned_ambulances = [];

 	// Extract form value to JSON
 	formData["stmain_number"] = $('#street').val();
 	formData["residential_unit"] = $('#address').val();
 	formData["description"] = $('#comment').val();
 	formData["priority"] = $('input:radio[name=priority]:checked').val();
 	$('input:checkbox[name="ambulance_assignment"]:checked').each(function(i) {
 		assigned_ambulances[i] = $(this).val();
 	});
 	formData["ambulance"] = assigned_ambulances.toString();

 	let postJsonUrl = 'api/calls/';
 	alert(JSON.stringify(formData) + '\n' + postJsonUrl);

 	var csrftoken = getCookie('csrftoken');

 	$.ajaxSetup({
 		beforeSend: function(xhr, settings) {
 			if(!csrfSafeMethod(settings.type) && !this.crossDomain) {
 				xhr.setRequestHeader("X-CSRFToken", csrftoken);
 			}
 		}
 	})

 	$.ajax({
 		url: postJsonUrl,
 		type: 'POST',
 		dataType: 'json',
 		data: formData,
 		success: function(data) {
 			// alert(JSON.stringify(data));
 			$('.modal-title').append('Successfully Dispached');
 			$('.modal-body').append(JSON.stringify(data));
 			$("#dispatchModal").modal('show');
 		},
 		error: function(jqXHR, textStatus, errorThrown) {
 			alert(JSON.stringify(jqXHR) + ' ' + textStatus);
 			$('.modal-title').append('Dispatch failed');
 			$("#dispatchModal").modal('show');
 		}
 	});
 }

 function csrfSafeMethod(method) {
 	return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
 }

 function getCookie(name) {
 	var cookieValue = null;
 	if(document.cookie && document.cookie !== '') {
 		var cookies = document.cookie.split(';');
 		for(var i = 0; i < cookies.length; i++) {
 			var cookie = $.trim(cookies[i]);
 			if(cookie.substring(0, name.length + 1) === (name + '=')) {
 				cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
 				break;
 			}
 		}
 	}
 	return cookieValue;
 }