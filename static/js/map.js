var ambulanceMarkers = {};  // Store ambulance markers
var ambulances = {};	// Store ambulance details

var hospitalMarkers = {};  // Store hospital markers
var hospitals = {};	// Store hospital details

var visibleStatus = {};
var markersByStatus = {};
Object.keys(ambulance_status).forEach(function(status) {
    markersByStatus[status] = [];
    visibleStatus[status] = true;
});
var statusGroupLayers = {};

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

/**
 * Ambulance statuses 
 */

var AmbulanceStatus = {
    'UK': 'Unknown',
    'AV': 'Available',
    'OS': 'Out of service',
    'PB': 'Patient bound',
    'AP': 'At patient',
    'HB': 'Hospital bound',
    'AH': 'At hospital'
}
var STATUS_IN_SERVICE = "IS";
var STATUS_AVAILABLE = "AV";
var STATUS_OUT_OF_SERVICE = "OS";

// global client variable for mqtt
var client;


/**
 * This is a handler for when the page is loaded.
 */
var mymap;
$(document).ready(function() {

    // Set map view
    mymap = L.map('live-map').setView([32.5149, -117.0382], 12);

    // Add layer to map.
    L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token=pk.eyJ1IjoieWFuZ2Y5NiIsImEiOiJjaXltYTNmbTcwMDJzMzNwZnpzM3Z6ZW9kIn0.gjEwLiCIbYhVFUGud9B56w', {
	attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="http://mapbox.com">Mapbox</a>',
	maxZoom: 18,
	id: 'mapbox.streets',
	accessToken: 'pk.eyJ1IjoieWFuZ2Y5NiIsImEiOiJjaXltYTNmbTcwMDJzMzNwZnpzM3Z6ZW9kIn0.gjEwLiCIbYhVFUGud9B56w'
    }).addTo(mymap);
    
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
    mymap.on(L.Draw.Event.CREATED,
	     function (e) {
    		 var type = e.layerType;
		 layer = e.layer;
   		 if (type === 'marker') {
       		     // Do marker specific actions
   		 }
   		 // Do whatever else you need to. (save to db; add to map etc)
   		 mymap.addLayer(layer);
	     });

    // Create status filter on the right hand top corner
    createStatusFilter(mymap);
    
    // Submit form
    $('#dispatchForm').submit(function(e) {
	e.preventDefault();
	postDispatchCall();
    })
    
    // Create a client instance
    // TODO: client id must be unique
    // TODO: password cannot be hardcoded
    client = new Paho.MQTT.Client(MQTTBroker.host,
				  MQTTBroker.port,
				  "clientId");
    
    // set callback handlers
    client.onMessageArrived = onMessageArrived;
    
    var options = {
	//connection attempt timeout in seconds
	timeout: 60,
	userName: "admin",
	password: "cruzrojaadmin",
	useSSL: true,
	cleanSession: true,
	onSuccess: onConnect,
	onFailure: onConnectFailure,
    };

    // connect to MQTT broker
    client.connect(options);
    
    // Publish to mqtt on status change from details options dropdown
    $('#ambulance-detail-status-select').change(function() {

	// Get status
	status = JSON.stringify({ 'status': this.value });

	// Send message
	let id = $('#ambulance-detail-id').val();
	let topic = "user/" + username + "/ambulance/" + id + "/data";
	let message = new Paho.MQTT.Message(status);
	message.destinationName = topic
	message.qos = 2;
	client.send(message);
	console.log('Sent message: "' + topic + ':' + status + '"');
	
    });
    
});

/* Handle connect */
function onConnect() {

    console.log("Connected to MQTT broker")
    
    // Subscribes to ambulance/{id}/data
    $.getJSON(APIBaseUrl + 'ambulance/', function(data) {
	$.each(data, function(index) {
	    let topicName = "ambulance/" + data[index].id + "/data";
	    client.subscribe(topicName);
	    console.log('Subscribing to topic: ' + topicName);
	});
    })

    // Subscribes to hospital/{id}/data
    $.getJSON(APIBaseUrl + 'hospital/', function(data) {
	$.each(data, function(index) {
	    let topicName = "hospital/" + data[index].id + "/data";
	    client.subscribe(topicName);
	    console.log('Subscribing to topic: ' + topicName);
	});
    })
    
};

/* Handle missconnection */
function onConnectFailure(message) {
	
    alert("Connection to MQTT broker failed: " + message.errorMessage +
	  "Information will not be updated in real time.");

    // Load data from API
    $.ajax({
	type: 'GET',
	datatype: "json",
	url: APIBaseUrl + 'ambulance/',
	
	error: function(msg) {
	    
	    alert('Could not retrieve data from API:' + msg)
	    
	},
	
	success: function(data) {
	    
	    console.log('Got data from API')
	    
	    $.each(data, function(i, ambulance) {
		
		// update ambulance
		updateAmbulance(ambulance);
		
	    });
	}
    })
	.done(function( data ) {
	    if ( console && console.log ) {
		console.log( "Done retrieving data from API" );
	    }
	});
    
};

/* Handle 'ambulance/+/data' mqtt messages */
function onMessageArrived(message) {

    console.log('Message "' +
		message.destinationName + ':' + message.payloadString +
		'" arrived');
    
    // split topic
    let topic = message.destinationName.split("/");
    
    try {
	
	// parse message
	let data = JSON.parse(message.payloadString);
	
	// Look for ambulance/{id}/data
	if (topic[0] === 'ambulance' &&
	    topic[2] == 'data') {
	    updateAmbulance(data);
	}
	
	// Look for ambulance/{id}/data
	else if(topic[0] === 'hospital' &&
		topic[2] == 'data') {
	    updateHospital(data);
	}
	
    } catch(e) {
	alert('Error processing message "' +
	      message.destinationName + ':' + message.payloadString +
	      '"' + '<br/>' + 'error = "' + e + '"');
    }
    
};

function updateAmbulance(ambulance) {

    // retrieve id
    let id = ambulance.id;

    // already exists?
    if (id in ambulances) {

	// Remove existing marker
	let marker = ambulanceMarkers[id];
	let status = ambulances[id].status;
	let index = markersByStatus[status].indexOf(marker);
	if (index >= 0)  {
	    markersByStatus[status].splice(index, 1);
	}
	mymap.removeLayer(marker);
	
	// update ambulance
	ambulances[id].status = ambulance.status;
	ambulances[id].location.latitude = ambulance.location.latitude;
	ambulances[id].location.longitude = ambulance.location.longitude;
	
	// Overwrite ambulance
	ambulance = ambulances[id]

	// Update ambulance grid
	var buttonId = "#grid-button" + id;
	
	// Updated button color/status
	if(ambulance.status === STATUS_AVAILABLE) 
	    $(buttonId).attr( "class", "btn btn-success" );
	else if(ambulance.tatus === STATUS_OUT_OF_SERVICE)
	    $(buttonId).attr( "class", "btn btn-default" );
	else
	    $(buttonId).attr( "class", "btn btn-danger" );
	
    } else {

	// Add ambulance to grid
	addAmbulanceToGrid(ambulance);
    }

    // add ambulance to map
    addAmbulanceToMap(ambulance);

    // update detail panel
    updateDetailPanel(ambulance);
    
};

function updateHospital(hospital) {

    // retrieve id
    let id = hospital.id;

    // already exists?
    if (id in hospitals) {

	// update hospital
	hospitals[id].location.latitude = hospital.location.latitude;
	hospitals[id].location.longitude = hospital.location.longitude;
	
	// Remove existing marker
	mymap.removeLayer(hospitalMarkers[id]);
	
	// Overwrite hospital
	hospital = hospitals[id]

    } 

    // add hospital to map
    addHospitalToMap(hospital);
    
};

function addAmbulanceToGrid(ambulance) {
    
    console.log('Adding ambulance "' + ambulance.identifier +
		'[id=' + ambulance.id + ']"' +
		' to grid');

    let button_class_name = 'btn-danger';
    if(ambulance.status === STATUS_AVAILABLE) {
	button_class_name = 'btn-success';

	$('#ambulance-selection')
	    .append('<label><input type="checkbox"' +
		    ' name="ambulance_assignment" value="' +
		    ambulance.id + '"> Ambulance ' +
		    ambulance.identifier + ' </label><br/>');
	
    }
    else if (ambulance.status === STATUS_OUT_OF_SERVICE) {
	
	button_class_name = 'btn-default';
    
    }

    // Add to grid
    $('#ambulance-grid')
	.append('<button type="button"' +
		' id="' + 'grid-button' + ambulance.id + '"' +
		' class="btn ' + button_class_name + '"' +
		' style="margin: 5px 5px;">' +
		ambulance.identifier + '</button>');
    
    // Open popup on panel click.
    // For some reason, only works when I create a separate function as opposed to creating a function within the click(...)
    $('#grid-button' + ambulance.id).click(
	onGridButtonClick(ambulance.id, mymap)
    );
    
};

function addAmbulanceToMap(ambulance) {

    console.log('Adding ambulance "' + ambulance.identifier +
		'[id=' + ambulance.id + ']"' +
		'[' + ambulance.location.latitude + ' ' +
		ambulance.location.longitude + '] ' +
		' to map');
    
    // store ambulance details in an array
    ambulances[ambulance.id] = ambulance;
    
    // set icon by status
    let coloredIcon = ambulanceIcon;
    if(ambulance.status === STATUS_AVAILABLE)
	coloredIcon = ambulanceIconBlue;
    else if(ambulance.status === STATUS_OUT_OF_SERVICE)
	coloredIcon = ambulanceIconBlack;
    
    // Add marker
    ambulanceMarkers[ambulance.id] = L.marker([ambulance.location.latitude,
					       ambulance.location.longitude],
					      {icon: coloredIcon})
	.bindPopup("<strong>" + ambulance.identifier +
		   "</strong><br/>" + ambulance.status).addTo(mymap);
    
    // Bind id to icons
    ambulanceMarkers[ambulance.id]._icon.id = ambulance.id;
    
    // Collapse panel on icon hover.
    ambulanceMarkers[ambulance.id]
	.on('mouseover',
	    function(e){
		// open popup bubble
		this.openPopup().on('mouseout',
				    function(e){
					this.closePopup();
				    });
	    })
	.on('click',
	    function(e){
		// update details panel
		updateDetailPanel(ambulance);
	    });
    
    // Add to a map to differentiate the layers between statuses.
    markersByStatus[ambulance.status].push(ambulanceMarkers[ambulance.id]);

    // If layer is not visible, remove marker
    if (!visibleStatus[ambulance.status]) {
	let marker = ambulanceMarkers[ambulance.id];
	statusGroupLayers[ambulance.status].removeLayer(marker);
	mymap.removeLayer(marker);
    }
    
};

function addHospitalToMap(hospital) {

    console.log('Adding hospital "' + hospital.name +
		'[id=' + hospital.id + ']"' +
		'[' + hospital.location.latitude + ' ' +
		hospital.location.longitude + '] ' +
		' to map');
    
    // store hospital details in an array
    hospitals[hospital.id] = hospital;
    
    // set icon by status
    let coloredIcon = hospitalIcon;
    
    // If hospital marker doesn't exist
    hospitalMarkers[hospital.id] = L.marker([hospital.location.latitude,
					     hospital.location.longitude],
					    {icon: coloredIcon})
	.bindPopup("<strong>" + hospital.name + "</strong>")
	.addTo(mymap);
    
    // Bind id to icons
    hospitalMarkers[hospital.id]._icon.id = hospital.id;
    
    // Collapse panel on icon hover.
    hospitalMarkers[hospital.id]
	.on('mouseover',
	    function(e){
		// open popup bubble
		this.openPopup().on('mouseout',
				    function(e){
					this.closePopup();
				    });		
	    });
    
};

/*
 * updateDetailPanel updates the detail panel with the ambulance's details.
 * @param ambulanceId is the unique id used in the ajax call url.
 * @return void.
 */
function updateDetailPanel(ambulance) {

    $('#ambulance-detail-name')
	.html(ambulance.identifier);
    $('#ambulance-detail-capability')
	.html(ambulance_capability[ambulance.capability]);
    $('#ambulance-detail-updated-on')
	.html(ambulance.updated_on);

    $('#ambulance-detail-status-select')
	.val(ambulance.status);
    $('#ambulance-detail-id')
	.val(ambulance.id);
    
}

/* Create status filter on the top right corner of the map */
function createStatusFilter(mymap) {

    // Add the checkbox on the top right corner for filtering.
    var container = L.DomUtil.create('div', 'filter-options');
    
    //Generate HTML code for checkboxes for each of the statuses.
    var filterHtml = "";
    Object.keys(ambulance_status).forEach(function(status) {

	statusGroupLayers[status] = L.layerGroup(markersByStatus[status]);
	statusGroupLayers[status].addTo(mymap);
    
	filterHtml += '<div class="checkbox"><label><input class="chk" data-status="' + status + '" type="checkbox" value="" checked>' + ambulance_status[status] + "</label></div>";
	
    });
    
    // Append html code to container 
    container.innerHTML = filterHtml;

    // Add the checkboxes.
    var customControl = L.Control.extend({
	
	options: {
	    position: 'topright' 
	},
	
	onAdd: function (map) {
	    return container;
	}
	
    });
    mymap.addControl(new customControl());

    // Add listener to remove status layer when filter checkbox is clicked
    $('.chk').change(function() {

	// Which layer?
	status = this.getAttribute('data-status');

	// Clear layer
	statusGroupLayers[status].clearLayers();
	
	if (this.checked) {

	    // Add the ambulances in the layer if it is checked.
	    markersByStatus[status].forEach(function(marker) {
		statusGroupLayers[status].addLayer(marker)
	    });
	    visibleStatus[status] = true;

	} else {
	    
	    // Remove from layer if it is not checked.
	    markersByStatus[status].forEach(function(marker) {
		statusGroupLayers[status].removeLayer(marker);
		mymap.removeLayer(marker);
	    });
	    visibleStatus[status] = false;
	    
	}
	
    });
    
};


function onGridButtonClick(ambulanceId, mymap) {
    return function(e) {

	let ambulance = ambulances[ambulanceId]
	
	// Update detail panel
	updateDetailPanel(ambulance);

	if (visibleStatus[ambulance.status]) {

	    // Center icon on map
	    var position = ambulanceMarkers[ambulanceId].getLatLng();
	    mymap.setView(position, mymap.getZoom());
	    
	    // Open popup for 2.5 seconds.
	    ambulanceMarkers[ambulanceId].openPopup();
	    setTimeout(function(){
		ambulanceMarkers[ambulanceId].closePopup();
	    }, 2500);
	    
	}
	
    }
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
 	formData["latitude"] = document.getElementById('curr-lat').innerHTML;
 	formData["longitude"] = document.getElementById('curr-lng').innerHTML;
 	formData["active"] = true
 	formData["name"] = "Make Dynamic for Future"
 	console.log(formData["active"])

 	console.log(formData["latitude"]);
 	formData["description"] = $('#comment').val();
 	formData["priority"] = $('input:radio[name=priority]:checked').val();
 	$('input:checkbox[name="ambulance_assignment"]:checked').each(function(i) {
 		assigned_ambulances[i] = $(this).val();
 	});

 	if(formData["priority"] == undefined) {
 		alert("Please click one of priorities");
 		return;
 	}

 	if(assigned_ambulances.length == 0) {
 		alert("Please dispatch at least one ambulance");
 		return;
 	}

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
 			 var successMsg = '<strong>Success</strong><br/>' + 
 			 	+ 'Ambulance: ' + data['ambulance']
 				+ ' dispatched to <br/>' + data['residential_unit']
 				+ ', '+ data['stmain_number'] + ', ' + data['latitude'] + ', ' + data['longitude'];
 			$('.modal-body').html(successMsg).addClass('alert-success');
 			$('.modal-title').append('Successfully Dispached');
 			$("#dispatchModal").modal('show');
 			finishDispatching();
 		},
 		error: function(jqXHR, textStatus, errorThrown) {
 			alert(JSON.stringify(jqXHR) + ' ' + textStatus);
 			$('.modal-title').append('Dispatch failed');
 			$("#dispatchModal").modal('show');
 			finishDispatching();
 		}
 	});
 }

 function csrfSafeMethod(method) {
 	return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
 }

/*
 * getCookie extracts the csrf token for form submit
 */
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

/* Functions to fill autocomplete AND to click specific locations */
function initAutocomplete() {
    // Create the autocomplete object, restricting the search to geographical
    autocomplete = new google.maps.places.Autocomplete((document.getElementById('street')),
						       {types: ['geocode']});
    //autocomplete.addListener('place_changed', fillInAddress);
}

/* Dispatch area - Should be eliminate after dispatching */

var circlesGroup = new L.LayerGroup();
var markersGroup = new L.LayerGroup();
var is_dispatching;

$("#street").change(function(data){

    var addressInput = document.getElementById('street').value;
	//console.log(addressInput);
	circlesGroup.clearLayers();

	var geocoder = new google.maps.Geocoder();

	geocoder.geocode({address: addressInput}, function(results, status) {
		if (status == google.maps.GeocoderStatus.OK) {
      		var coordinate = results[0].geometry.location;

      		document.getElementById('curr-lat').innerHTML = coordinate.lat();
      		document.getElementById('curr-lng').innerHTML = coordinate.lng();

      		var placeIcon = L.icon({
			    iconUrl: '/static/icons/place_marker.png',
			    iconSize:     [50, 50], // size of the icon
			});

      		L.marker([coordinate.lat(),coordinate.lng()],{icon: placeIcon}).addTo(markersGroup);
      		markersGroup.addTo(mymap);
      		mymap.setView(new L.LatLng(coordinate.lat(), coordinate.lng()),17);
		}
		else {
			alert("There is error from Google map server");
		}
	});
});

var dispatching = function() {
	console.log('Click dispatching button');
	is_dispatching = true;
	document.getElementById('dispatch_work').innerHTML = '<button type="button" class="btn btn-link" onclick="finishDispatching()"><span class="glyphicon glyphicon-chevron-left"></span> Go back</button>';
	$('#dispatchForm').collapse('show');
	$('#collapse1').collapse('hide');
	$('#collapse2').collapse('hide');

	mymap.on('click', function(e){
		markersGroup.clearLayers();
		//console.log(e.latlng.lat);
		document.getElementById('curr-lat').innerHTML = e.latlng.lat;
		document.getElementById('curr-lng').innerHTML = e.latlng.lng;
		if(is_dispatching) {
			var placeIcon = L.icon({
			    iconUrl: '/static/icons/place_marker.png',
			    iconSize:     [50, 50], // size of the icon
			});
			L.marker([e.latlng.lat,e.latlng.lng],{icon: placeIcon}).addTo(markersGroup);
			markersGroup.addTo(mymap);
		}
	});

}

var finishDispatching = function() {
	is_dispatching = false;
	markersGroup.clearLayers();
	console.log('Click dispatching button');
	document.getElementById('dispatch_work').innerHTML = '<button class="btn btn-primary" style="display: block; width: 100%;" data-toggle="collapse" href="#dispatchForm" onclick="dispatching()">Dispatch</button>';
	$('#dispatchForm').collapse('hide');
	$('#collapse1').collapse('show');
	$('#collapse2').collapse('show');
}


