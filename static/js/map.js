var ambulanceMarkers = {};  // Store ambulance markers
var ambulances = {};	// Store ambulance details

var hospitalMarkers = {};  // Store hospital markers
var hospitals = {};	// Store hospital details

var locationMarkers = {};  // Store location markers
var locations = {};	// Store location details

// Initialize category layers
var visibleCategory = {};
var markersByCategory = {};
var categoryGroupLayers = {};

// add ambulance_status and ambulance_capability
Object.keys(ambulance_status).forEach(function(status) {
    Object.keys(ambulance_capability).forEach(function(capability) {
        markersByCategory[status+"|"+capability] = [];
    });
    visibleCategory[status] = true;
});
Object.keys(ambulance_capability).forEach(function(capability) {
    visibleCategory[capability] = true;
});

// add hospital
var category = 'Hospital';
markersByCategory[category] = [];
visibleCategory[category] = true;

// add location_type
Object.keys(location_type).forEach(function(type) {
    markersByCategory[type] = [];
    visibleCategory[type] = false;
});

// Initialize ambulance icons
var ambulance_settings = [
    [
        L.icon({
            iconUrl: '/static/icons/cars/ambulance_blue.svg',
            iconSize: [15, 30],
        }), 'btn-primary'
    ],
    [
        L.icon({
            iconUrl: '/static/icons/cars/ambulance_green.svg',
            iconSize: [15, 30],
        }), 'btn-success'
    ],
    [
        L.icon({
            iconUrl: '/static/icons/cars/ambulance_gray.svg',
            iconSize: [15, 30],
        }), 'btn-secondary'
    ],
    [
        L.icon({
            iconUrl: '/static/icons/cars/ambulance_red.svg',
            iconSize: [15, 30],
        }), 'btn-danger'
    ],
    [
        L.icon({
            iconUrl: '/static/icons/cars/ambulance_yellow.svg',
            iconSize: [15, 30],
        }), 'btn-warning'
    ],
    [
        L.icon({
            iconUrl: '/static/icons/cars/ambulance_purple.svg',
            iconSize: [15, 30],
        }), 'btn-info'
    ],
    [
        L.icon({
            iconUrl: '/static/icons/cars/ambulance_orange.svg',
            iconSize: [15, 30],
        }), 'btn-dark'
    ],
];

var ambulance_icons = {};
var ambulance_buttons = {};
Object.keys(ambulance_status).forEach(function(type, index) {
    var settings = ambulance_settings[index];
    ambulance_icons[type] = settings[0];
    ambulance_buttons[type] = settings[1];
});

var hospitalIcon = L.icon({
	iconUrl: '/static/icons/maki/hospital-15.svg',
	iconSize: [15, 15]
});
var defibrillatorIcon = L.icon({
	iconUrl: '/static/icons/maki/defibrillator-15.svg',
	iconSize: [15, 15]
});
var baseIcon = L.icon({
	iconUrl: '/static/icons/maki/home-15.svg',
	iconSize: [15, 15]
});
var otherIcon = L.icon({
	iconUrl: '/static/icons/maki/marker-15.svg',
	iconSize: [15, 15],
	iconAnchor: [7, 15],
	popupAnchor: [0,-15]
});

var locationIcon = L.icon({
	iconUrl: '/static/icons/maki/marker-15.svg',
	iconSize: [15, 15],
	iconAnchor: [7, 15],
	popupAnchor: [0,-15]

});

// TODO: different icons for different location types
// TODO: different colors for ambulance status

/**
 * Ambulance statuses 
 */

var STATUS_AVAILABLE = "AV";
var STATUS_OUT_OF_SERVICE = "OS";

// global variable for mqttClient
var mqttClient;

// TODO: remove hardcoded mapbox access_token

/**
 * This is a handler for when the page is loaded.
 */
var mymap;
var accessToken = 'pk.eyJ1IjoieWFuZ2Y5NiIsImEiOiJjaXltYTNmbTcwMDJzMzNwZnpzM3Z6ZW9kIn0.gjEwLiCIbYhVFUGud9B56w';
var geocoder = new Geocoder({ access_token: accessToken });

// Ready function
$(function () {

    // token and attribution
    var attribution = 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="http://mapbox.com">Mapbox</a>';

    // Set map view
    mymap = L.map('live-map').setView([32.5149, -117.0382], 12);

    // geocoder = L.mapbox.geocoder('mapbox.places');

    // Add layer to map.
    L.tileLayer(
        'https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token=' + accessToken,
        {
            attribution: attribution,
            maxZoom: 18,
            id: 'mapbox.streets',
            accessToken: accessToken
        }
    ).addTo(mymap);

    // Add the drawing toolbar and the layer of the drawings.
    var drawnItems = new L.FeatureGroup();
    mymap.addLayer(drawnItems);
    var drawControl = new L.Control.Draw({
        edit: {
            featureGroup: drawnItems
        }
    });
    mymap.addControl(drawControl);

    // Event handler for when some1pxg is drawn. Only handles 
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

    // Create category filter on the right hand top corner
    createCategoryFilter();

    // Make ambulance-selection droppable
    $('#ambulance-selection')
        .on('dragover', function(e) {
            e.preventDefault();
        })
        .on('drop', function(e) {
            e.preventDefault();
            // Dropped button, get data
            var ambulance_id = e.originalEvent.dataTransfer.getData("text/plain");
            var ambulance = ambulances[ambulance_id];
            console.log('dropped ambulance ' + ambulance['identifier']);
            // and add to dispatching list
            addToDispatchingList(ambulance);
        });

    // retrieve temporary password for mqttClient and connect to broker
    $.getJSON(APIBaseUrl + 'user/' + username + '/password/', function (password) {

        // create mqtt broker client
        mqttClient = new Paho.MQTT.Client(MQTTBroker.host,
            MQTTBroker.port,
            clientId);

        // set callback handlers
        mqttClient.onMessageArrived = onMessageArrived;

        // attempt to connect to MQTT broker
        mqttClient.connect({
            //connection attempt timeout in seconds
            timeout: 60,
            userName: username,
            password: password,
            useSSL: true,
            cleanSession: true,
            onSuccess: onConnect,
            onFailure: onConnectFailure,
        });

    })
        .fail(function (jqxhr, testStatus, error) {

            bsalert("Connection to MQTT broker failed: \"" +
                testStatus + "," + error + "\"\n" +
                "Information will not be updated in real time.");

        });

});

// alert using bootstrap modal
var bsalert = function(message, alertClass, title) {

    // Show modal
    alertClass = alertClass || 'alert-danger';
    title = title || 'Failure';

    $('.modal-title').html(title);
    $('.modal-body').html(message).addClass(alertClass);
    $("#dispatchModal").modal('show');

}

/* Handle connect */
function onConnect() {

    console.log("Connected to MQTT broker");

    // retrieve profile from api
    console.log("Retrieving profile from API");
    $.getJSON(APIBaseUrl + 'user/' + username + '/profile/', function (data) {

        // Subscribe to hospitals
        $.each(data.hospitals, function (index) {
            let topicName = "hospital/" + data.hospitals[index].hospital_id + "/data";
            mqttClient.subscribe(topicName);
            console.log('Subscribing to topic: ' + topicName);
        });

        // Subscribe to ambulances
        $.each(data.ambulances, function (index) {
            let topicName = "ambulance/" + data.ambulances[index].ambulance_id + "/data";
            mqttClient.subscribe(topicName);
            console.log('Subscribing to topic: ' + topicName);
        });

    });

    // retrieve locations from api
    console.log("Retrieving locations from API");
    $.getJSON(APIBaseUrl + 'location/', function (data) {

        // add location
        $.each(data, function (index) {
        	addLocationToMap(data[index]);
        });
        
    });

    // publish to mqtt on status change from details options dropdown
    $('#ambulance-detail-status-select').change(function () {

        // Get status
        status = JSON.stringify({'status': this.value});

        // Send message
        let id = $('#ambulance-detail-id').val();
        let topic = "user/" + username + "/ambulance/" + id + "/data";
        let message = new Paho.MQTT.Message(status);
        message.destinationName = topic
        message.qos = 2;
        mqttClient.send(message);
        console.log('Sent message: "' + topic + ':' + status + '"');

    });

};

/* Handle missconnection */
function onConnectFailure(message) {

    bsalert("Connection to MQTT broker failed: " + message.errorMessage +
        "Information will not be updated in real time.");

    // Load hospital data from API
    $.ajax({
        type: 'GET',
        datatype: "json",
        url: APIBaseUrl + 'hospital/',

        error: function (msg) {

            bsalert('Could not retrieve data from API:' + msg)

        },

        success: function (data) {

            console.log('Got data from API')

            $.each(data, function (i, hospital) {

                // update hospital
                updateHospital(hospital);

            });
        }
    })
        .done(function (data) {
            if (console && console.log) {
                console.log("Done retrieving hospital data from API");
            }
        });

    // Load ambulance data from API
    $.ajax({
        type: 'GET',
        datatype: "json",
        url: APIBaseUrl + 'ambulance/',

        error: function (msg) {

            bsalert('Could not retrieve data from API:' + msg)

        },

        success: function (data) {

            console.log('Got data from API')

            $.each(data, function (i, ambulance) {

                // update ambulance
                updateAmbulance(ambulance);

            });
        }
    })
        .done(function (data) {
            if (console && console.log) {
                console.log("Done retrieving ambulance data from API");
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
        else if (topic[0] === 'hospital' &&
            topic[2] == 'data') {
            updateHospital(data);
        }

    } catch (e) {
        bsalert('Error processing message "' +
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
        let capability = ambulances[id].capability;
        let index = markersByCategory[status+"|"+capability].indexOf(marker);
        if (index >= 0) {
            markersByCategory[status+"|"+capability].splice(index, 1);
        }
        mymap.removeLayer(marker);

        // update ambulance
        ambulances[id].status = ambulance.status;
        ambulances[id].capability = ambulance.capability;
        ambulances[id].location.latitude = ambulance.location.latitude;
        ambulances[id].location.longitude = ambulance.location.longitude;
        ambulances[id].orientation = ambulance.orientation;

        // Overwrite ambulance
        ambulance = ambulances[id]

        // Update ambulance grid
        var buttonId = "#grid-button-" + id;

        // Updated button color/status
        $(buttonId).attr("class", "btn btn-sm " + ambulance_buttons[ambulance.status]);

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

    // Add button to ambulance grid
    $('#ambulance-grid')
        .append('<button type="button"'
            + ' id="grid-button-' + ambulance.id + '"'
            + ' class="btn btn-sm ' + ambulance_buttons[ambulance.status] + '"'
            + ' style="margin: 2px 2px;"'
            + ' draggable="true">'
            + ambulance.identifier
            + '</button>');
    $('#grid-button-' + ambulance.id)
        .on('dragstart', function (e) {
            // on start of drag, copy information and fade button
            console.log('dragstart');
            this.style.opacity = '0.4';
            e.originalEvent.dataTransfer.setData("text/plain", ambulance.id);
        })
        .on('dragend', function (e) {
            console.log('dragend');
            // Restore opacity
            this.style.opacity = '1.0';
        })
        .click( function(e) {
            onGridButtonClick(ambulance);
        })
        .dblclick( function(e) {
            addToDispatchingList(ambulance);
        });

};

function addAmbulanceToMap(ambulance) {

    console.log('Adding ambulance "' + ambulance.identifier +
        '[id=' + ambulance.id + ']"' +
        '[' + ambulance.location.latitude + ' ' +
        ambulance.location.longitude + '] ' +
        ' to map');

    // store ambulance details in an array
    ambulances[ambulance.id] = ambulance;

    // Add marker
    // console.log('orientation = ' + ambulance.orientation);
    ambulanceMarkers[ambulance.id] = L.marker(
        [ambulance.location.latitude,
            ambulance.location.longitude],
        {
            icon: ambulance_icons[ambulance.status],
            rotationAngle: ambulance.orientation % 360,
            rotationOrigin: 'center center'
        })
        .bindPopup(
            "<strong>" + ambulance.identifier +
            "</strong>" +
            "<br/>" +
            ambulance_capability[ambulance.capability] +
            "<br/>" +
            ambulance_status[ambulance.status]
        ).addTo(mymap);

    // Bind id to icons
    ambulanceMarkers[ambulance.id]._icon.id = ambulance.id;

    // Collapse panel on icon hover.
    ambulanceMarkers[ambulance.id]
        .on('mouseover',
            function (e) {
                // open popup bubble
                this.openPopup().on('mouseout',
                    function (e) {
                        this.closePopup();
                    });
            })
        .on('click',
            function (e) {

                // update details panel
                updateDetailPanel(ambulance);

                // add to dispatching list
                addToDispatchingList(ambulance);

            });

    // Add to a map to differentiate the layers between statuses.
    markersByCategory[ambulance.status+"|"+ambulance.capability].push(ambulanceMarkers[ambulance.id]);

    // If layer is not visible, remove marker
    if (!(visibleCategory[ambulance.status] && visibleCategory[ambulance.capability])) {
        let marker = ambulanceMarkers[ambulance.id];
        categoryGroupLayers[ambulance.status+"|"+ambulance.capability].removeLayer(marker);
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
            function (e) {
                // open popup bubble
                this.openPopup().on('mouseout',
                    function (e) {
                        this.closePopup();
                    });
            });

    // Add to a map to differentiate the layers between statuses.
	let category = 'Hospital'
    markersByCategory[category].push(hospitalMarkers[hospital.id]);

    // If layer is not visible, remove marker
    if (!visibleCategory[category]) {
        let marker = hospitalMarkers[hospital.id];
        categoryGroupLayers[category].removeLayer(marker);
        mymap.removeLayer(marker);
    }

};

function addLocationToMap(location) {

    console.log('Adding location "' + location.name +
        '[id=' + location.id + ', type=' + location.type + ']"' +
        '[' + location.location.latitude + ' ' +
        location.location.longitude + '] ' +
        ' to map');

    // store location details in an array
    locations[location.id] = location;

    // set icon by status
    let icon = locationIcon;
    if (location.type === 'a')
        icon = defibrillatorIcon;
    else if (location.type === 'b')
        icon = baseIcon;
    else
        icon = otherIcon;
        
    // If location marker doesn't exist
    locationMarkers[location.id] = L.marker([location.location.latitude,
            location.location.longitude],
        {icon: icon})
        .bindPopup("<strong>" + location.name + "</strong>")
        .addTo(mymap);

    // Bind id to icons
    locationMarkers[location.id]._icon.id = location.id;

    // Collapse panel on icon hover.
    locationMarkers[location.id]
        .on('mouseover',
            function (e) {
                // open popup bubble
                this.openPopup().on('mouseout',
                    function (e) {
                        this.closePopup();
                    });
            });

    // Add to a map to differentiate the layers between typees.
    markersByCategory[location.type].push(locationMarkers[location.id]);

    // If layer is not visible, remove marker
    if (!visibleCategory[location.type]) {
        let marker = locationMarkers[location.id];
        categoryGroupLayers[location.type].removeLayer(marker);
        mymap.removeLayer(marker);
    }
    
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
        .html((new Date(Date.parse(ambulance.updated_on))).toLocaleString());

    $('#ambulance-detail-status-select')
        .val(ambulance.status);
    $('#ambulance-detail-id')
        .val(ambulance.id);

}

/* Create status filter on the top right corner of the map */
function createCategoryFilter() {

    // Add the checkbox on the top right corner for filtering.
    var container = L.DomUtil.create('div', 'filter-options');

    // Generate HTML code for checkboxes for each of the statuses.
    var filterHtml = "";

    filterHtml += '<div class="border border-dark rounded-top px-1 pt-1 pb-0">';
    Object.keys(ambulance_status).forEach(function (status) {

        // create disjoint group layers
        Object.keys(ambulance_capability).forEach(function (capability) {
            categoryGroupLayers[status+"|"+capability] = L.layerGroup(markersByCategory[status+"|"+capability]);
            categoryGroupLayers[status+"|"+capability].addTo(mymap);
        });

        // add div
        filterHtml += '<div class="checkbox"><label><input class="chk" data-status="'
            + status + '" type="checkbox" value="status" '
            + (visibleCategory[status] ? 'checked' : '') + '>'
            + ambulance_status[status] + "</label></div>";

    });
    filterHtml += "</div>";

    // Generate HTML code for checkboxes for each of the capabilities.
    filterHtml += '<div class="border border-top-0 border-bottom-1 border-dark px-1 pt-1 pb-0">';
    Object.keys(ambulance_capability).forEach(function (capability) {

        // no need to create group layers here

        // add div
        filterHtml += '<div class="checkbox"><label><input class="chk" data-category="'
            + capability + '" type="checkbox" value="category" '
            + (visibleCategory[capability] ? 'checked' : '') + '>'
            + ambulance_capability[capability] + "</label></div>";

    });
    filterHtml += "</div>";
    
    // Generate HTML code for checkboxes for hospital
    filterHtml += '<div class="border border-top-0 border-bottom-0 border-dark px-1 pt-1 pb-0">';
    let category = 'Hospital'
    categoryGroupLayers[category] = L.layerGroup(markersByCategory[category]);
    categoryGroupLayers[category].addTo(mymap);
    filterHtml += '<div class="checkbox"><label><input class="chk" data-status="' 
        + category + '" type="checkbox" value="hospital" '
        + (visibleCategory[category] ? 'checked' : '') + '>'
        + category + "</label></div>";
    filterHtml += "</div>";

    //Generate HTML code for checkboxes for locations
    filterHtml += '<div class="border border-dark rounded-bottom px-1 pt-1 pb-0">';
    Object.keys(location_type).forEach(function (type) {

        categoryGroupLayers[type] = L.layerGroup(markersByCategory[type]);
        categoryGroupLayers[type].addTo(mymap);

        // add div
        filterHtml += '<div class="checkbox"><label><input class="chk" data-status="'
            + type + '" type="checkbox" value="location" '
            + (visibleCategory[type] ? 'checked' : '') + '>'
            + location_type[type] + "</label></div>";

    });
    filterHtml += "</div>";

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

    // Add listener to remove or add layer when filter checkbox is clicked
    $('.chk').change(function () {

        // TODO: add/remove buttons from grid as well

        // Which layer?
        var layer = this.getAttribute('data-status');
        var categoryOrStatus = this.value == 'status' || this.value == 'category'; 
        
        if (categoryOrStatus) {
            if (this.value == 'status') {
                // Clear all capability layers
                Object.keys(ambulance_capability).forEach(function (capability) {
                    categoryGroupLayers[layer+"|"+capability].clearLayers();
                });
            } else {
                // Clear all status layers
                Object.keys(ambulance_status).forEach(function (status) {
                    categoryGroupLayers[status+"|"+layer].clearLayers();
                });
            }
        } else {
            // Clear layer
            categoryGroupLayers[layer].clearLayers();
        }

        if (this.checked) {

            // Add the ambulances in the layer if it is checked.
            if (categoryOrStatus) {
                if (this.value == 'status') {
                    // Add all capability layers
                    Object.keys(ambulance_capability).forEach(function (capability) {
                        markersByCategory[layer+"|"+capability].forEach(function (marker) {
                            categoryGroupLayers[layer+"|"+capability].addLayer(marker)
                        });
                    });
                } else {
                    // Add all status layers
                    Object.keys(ambulance_status).forEach(function (status) {
                        markersByCategory[status+"|"+layer].forEach(function (marker) {
                            categoryGroupLayers[status+"|"+layer].addLayer(marker)
                        });
                    });
                }
            } else {
                markersByCategory[layer].forEach(function (marker) {
                    categoryGroupLayers[layer].addLayer(marker)
                });
            }
            visibleCategory[layer] = true;

        } else {

            // Remove from layer if it is not checked.
            if (categoryOrStatus) {
                if (this.value == 'status') {
                    // Add all capability layers
                    Object.keys(ambulance_capability).forEach(function (capability) {
                        markersByCategory[layer+"|"+capability].forEach(function (marker) {
                            categoryGroupLayers[layer+"|"+capability].removeLayer(marker)
                        });
                    });
                } else {
                    // Add all status layers
                    Object.keys(ambulance_status).forEach(function (status) {
                        markersByCategory[status+"|"+layer].forEach(function (marker) {
                            categoryGroupLayers[status+"|"+layer].removeLayer(marker)
                        });
                    });
                }
            } else {
                markersByCategory[layer].forEach(function (marker) {
                    categoryGroupLayers[layer].removeLayer(marker);
                    mymap.removeLayer(marker);
                });
            }
            visibleCategory[layer] = false;

        }

    });

};


function onGridButtonClick(ambulance) {

    // Update detail panel
    updateDetailPanel(ambulance);

    if (visibleCategory[ambulance.status]) {

        // Center icon on map
        var position = ambulanceMarkers[ambulance.id].getLatLng();
        mymap.setView(position, mymap.getZoom());

        // Open popup for 2.5 seconds.
        ambulanceMarkers[ambulance.id].openPopup();
        setTimeout(function () {
            ambulanceMarkers[ambulance.id].closePopup();
        }, 2500);

    }

}
