var ambulanceMarkers = {};  // Store ambulance markers
var ambulances = {};	// Store ambulance details

var hospitalMarkers = {};  // Store hospital markers
var hospitals = {};	// Store hospital details

var locationMarkers = {};  // Store location markers
var locations = {};	// Store location details

// Initialize category panes
var visibleCategory = {};

// add status
Object.keys(ambulance_status).forEach(function(status) {
    visibleCategory[status] = true;
});

// add capability
Object.keys(ambulance_capability).forEach(function(capability) {
    visibleCategory[capability] = true;
});

// add hospital
visibleCategory['hospital'] = true;

// add location_type
Object.keys(location_type).forEach(function(type) {
    visibleCategory[type] = false;
});

// Initialize ambulance icons
var ambulance_icons = {};
var ambulance_buttons = {};
for (var key in ambulance_css) {
    // skip loop if the property is from prototype
    if (!ambulance_css.hasOwnProperty(key))
        continue;

    var settings = ambulance_css[key];
    ambulance_icons[key] = L.icon(settings['icon']);
    ambulance_buttons[key] = settings['class'];
}

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

    // Create category filters
    createCategoryFilters();

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

        // set will message
        var willMessage = new Paho.MQTT.Message('disconnected');
        willMessage.destinationName = 'user/' + username + '/client/' + clientId + '/status';
        willMessage.qos = 2;
        willMessage.retained = true;

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
            willMessage: willMessage,
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

    // handshake online
    var onlineMessage = new Paho.MQTT.Message('online');
    onlineMessage.destinationName = 'user/' + username + '/client/' + clientId + '/status';
    onlineMessage.qos = 2;
    onlineMessage.retained = true;
    mqttClient.send(onlineMessage);
    console.log('Sent online message');

    // retrieve profile from api
    console.log("Retrieving profile from API");
    $.getJSON(APIBaseUrl + 'user/' + username + '/profile/', function (data) {

        // Subscribe to hospitals
        $.each(data.hospitals, function (index) {
            var topicName = "hospital/" + data.hospitals[index].hospital_id + "/data";
            mqttClient.subscribe(topicName);
            console.log('Subscribing to topic: ' + topicName);
        });

        // Subscribe to ambulances
        $.each(data.ambulances, function (index) {
            var topicName = "ambulance/" + data.ambulances[index].ambulance_id + "/data";
            mqttClient.subscribe(topicName);
            console.log('Subscribing to topic: ' + topicName);
        });

    });

    // retrieve locations from api
    console.log("Retrieving locations from API");
    $.getJSON(APIBaseUrl + 'location/', function (data) {

        // add location
        $.each(data, function (index) {
            var location = data[index];
        	addLocationToMap(location);
        });
        
    });

    // publish to mqtt on status change from details options dropdown
    $('#ambulance-detail-status-select').change(function () {

        // Get status
        status = JSON.stringify({'status': this.value});

        // Send message
        var id = $('#ambulance-detail-id').val();
        var topic = "user/" + username + "/client/" + clientId + "/ambulance/" + id + "/data";
        var message = new Paho.MQTT.Message(status);
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
    var topic = message.destinationName.split("/");

    try {

        // parse message
        var data = JSON.parse(message.payloadString);

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
    var id = ambulance.id;

    // already exists?
    if (id in ambulances) {

        // Remove existing marker
        mymap.removeLayer(ambulanceMarkers[id]);

        // update ambulance
        ambulances[id].status = ambulance.status;
        ambulances[id].capability = ambulance.capability;
        ambulances[id].location.latitude = ambulance.location.latitude;
        ambulances[id].location.longitude = ambulance.location.longitude;
        ambulances[id].orientation = ambulance.orientation;

        // Overwrite ambulance
        ambulance = ambulances[id]

        // Updated grid button class
        var btnClass = 'btn btn-sm ' + ambulance_buttons[ambulance.status]
            + ' status-' + ambulance.status
            + ' capability-' + ambulance.capability;

        console.log('Updating ambulance "' + ambulance.identifier +
        '[id=' + ambulance.id + ', status=' + ambulance.status + ', class=' + btnClass + ']"' +
        ' on grid');

        // Updated button classes
        $("#grid-button-" + id).attr("class", btnClass);

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
    var id = hospital.id;

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
        '[id=' + ambulance.id + ', status=' + ambulance.status + ', btn=' + ambulance_buttons[ambulance.status] + ']"' +
        ' to grid');

    // make grid visible
    if (ambulance.status == 'AV')
        $('#ambulance_' + ambulance.status).addClass('show');

    // Add button to ambulance grid
    $('#ambulance-grid-' + ambulance.status)
        .append('<button type="button"'
            + ' id="grid-button-' + ambulance.id + '"'
            + ' class="btn btn-sm ' + ambulance_buttons[ambulance.status]
            + ' status-' + ambulance.status
            + ' capability-' + ambulance.capability + '"'
            + ' style="margin: 2px 2px;"'
            + ' draggable="true">'
            + ambulance.identifier
            + '</button>');

    // Make button draggable
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
            rotationOrigin: 'center center',
            pane: ambulance.status+"|"+ambulance.capability
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
    var coloredIcon = hospitalIcon;

    // If hospital marker doesn't exist
    hospitalMarkers[hospital.id] = L.marker([hospital.location.latitude,
            hospital.location.longitude],
        {
            icon: coloredIcon,
            pane: 'hospital'
        })
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
    var icon = locationIcon;
    if (location.type === 'a')
        icon = defibrillatorIcon;
    else if (location.type === 'b')
        icon = baseIcon;
    else
        icon = otherIcon;
        
    // If location marker doesn't exist
    locationMarkers[location.id] = L.marker([location.location.latitude,
            location.location.longitude],
        {
            icon: icon,
            pane: location.type
        })
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

/* Create category filter */
function createCategoryFilters() {

    // Create category panes
    Object.keys(ambulance_status).forEach(function (status) {
        Object.keys(ambulance_capability).forEach(function (capability) {
            mymap.createPane(status+"|"+capability);
        });
    });
    mymap.createPane('hospital');
    Object.keys(location_type).forEach(function (type) {
        mymap.createPane(type);
    });

    // Create status grids
    Object.keys(ambulance_status).forEach(function (status) {

        $("#ambulance_status").append(
            '<div class="card form-group mb-1 mt-0" id="ambulance_card_' + status + '">\n' +
            '    <div class="card-header px-1 pb-0 pt-1"\n' +
            '         id="ambulance_heading_' + status + '">\n' +
            '         <h6 style="cursor: pointer;"\n' +
            '             data-toggle="collapse"\n' +
            '             data-target="#ambulance_' + status + '"\n' +
            '             aria-expanded="true" aria-controls="ambulance_' + status + '">\n' +
            '             <input class="form-check-input filter-checkbox" value="status" data-status="' + status + '"\n' +
            '                    type="checkbox" id="ambulance_checkbox_' + status + '">\n' +
            '             <span role="button">' + ambulance_status[status] + '</span>\n' +
            '          </h6>\n' +
            '    </div>\n' +
            '    <div class="collapse"\n' +
            '         id="ambulance_' + status + '"\n' +
            '         aria-labelledby="ambulance_heading_' + status + '"\n' +
            '         data-parent="#ambulance_status">\n' +
            '         <div class="card-body py-1 px-0"\n' +
            '              id="ambulance-grid-' + status + '">\n' +
            '         </div>\n' +
            '    </div>\n' +
            '</div>');
    });

    // Create capability options
    Object.keys(ambulance_capability).forEach(function (capability) {

        $("#ambulance_capability").append(
            '<div class="form-group form-check mt-0 mb-1">\n' +
            '     <input class="form-check-input filter-checkbox" value="capability" data-status="' + capability + '"\n' +
            '            type="checkbox" id="capability-' + capability + '">\n' +
            '     <label class="form-check-label"\n' +
            '            for="capability-' + capability + '">' + ambulance_capability[capability] + '</label>\n' +
            '</div>');
    });

    // Create location options
    $("#location_type").append(
        '<div class="form-group form-check mt-0 mb-1">\n' +
        '     <input class="form-check-input filter-checkbox" value="location" data-status="hospital"\n' +
        '            type="checkbox" id="location-hospital">\n' +
        '     <label class="form-check-label"\n' +
        '            for="location-hospital">Hospital</label>\n' +
        '</div>');
    Object.keys(location_type).forEach(function (type) {

        $("#location_type").append(
            '<div class="form-group form-check mt-0 mb-1">\n' +
            '     <input class="form-check-input filter-checkbox" value="location" data-status="' + type + '"\n' +
            '            type="checkbox" id="location-' + type + '">\n' +
            '     <label class="form-check-label"\n' +
            '            for="location-' + type + '">' + location_type[type] + '</label>\n' +
            '</div>');
    });

    // Add listener to remove or add layer when filter checkbox is clicked
    $('.filter-checkbox').change(function () {

        // Which layer?
        var layer = this.getAttribute('data-status');

        // Display or hide?
        var display;
        if (this.checked) {
            display = 'block';
            visibleCategory[layer] = true;
        } else {
            display = 'none';
            visibleCategory[layer] = false;
        }

        // Modify pane and button
        if (this.value == 'status') {
            // Add to all visible capability panes
            Object.keys(ambulance_capability).forEach(function (capability) {
                if (visibleCategory[capability]) {
                    mymap.getPane(layer+"|"+capability).style.display = display;
                    $('button.status-' + layer + '.capability-' + capability).css('display', display);
                }
            });
        } else if (this.value == 'capability') {
            // Add to all visible status layers
            Object.keys(ambulance_status).forEach(function (status) {
                if (visibleCategory[status]) {
                    mymap.getPane(status+"|"+layer).style.display = display;
                    $('button.status-' + status + '.capability-' + layer).css('display', display);
                }
            });
        } else {
            mymap.getPane(layer).style.display = display;
        }

    });


};

/* Create status filter on the top right corner of the map */
function createCategoryFilter() {

    // Add the checkbox on the top right corner for filtering.
    var container = L.DomUtil.create('div', 'filter-options bg-light');

    // Generate HTML code for checkboxes for each of the statuses.
    var filterHtml = "";

    filterHtml += '<div class="border border-dark rounded-top px-1 pt-1 pb-0">';
    Object.keys(ambulance_status).forEach(function (status) {

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

        // add div
        filterHtml += '<div class="checkbox"><label><input class="chk" '
            + 'data-status="' + capability + '" type="checkbox" value="capability" '
            + (visibleCategory[capability] ? 'checked' : '') + '>'
            + ambulance_capability[capability] + "</label></div>";

    });
    filterHtml += "</div>";
    
    // Generate HTML code for checkboxes for hospital
    filterHtml += '<div class="border border-top-0 border-bottom-0 border-dark px-1 pt-1 pb-0">';
    filterHtml += '<div class="checkbox"><label><input class="chk" '
        + 'data-status="hospital" type="checkbox" value="hospital" '
        + (visibleCategory['hospital'] ? 'checked' : '') + '>'
        + 'Hospital' + "</label></div>";
    filterHtml += "</div>";

    //Generate HTML code for checkboxes for locations
    filterHtml += '<div class="border border-dark rounded-bottom px-1 pt-1 pb-0">';
    Object.keys(location_type).forEach(function (type) {

        // add div
        filterHtml += '<div class="checkbox"><label><input class="chk" '
            + 'data-status="' + type + '" type="checkbox" value="location" '
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

        // Which layer?
        var layer = this.getAttribute('data-status');

        // Display or hide?
        var display;
        if (this.checked) {
            display = 'block';
            visibleCategory[layer] = true;
        } else {
            display = 'none';
            visibleCategory[layer] = false;
        }

        // Modify pane and button
        if (this.value == 'status') {
            // Add to all visible capability panes
            Object.keys(ambulance_capability).forEach(function (capability) {
                if (visibleCategory[capability]) {
                    mymap.getPane(layer+"|"+capability).style.display = display;
                    $('button.status-' + layer + '.capability-' + capability).css('display', display);
                }
            });
        } else if (this.value == 'capability') {
            // Add to all visible status layers
            Object.keys(ambulance_status).forEach(function (status) {
                if (visibleCategory[status]) {
                    mymap.getPane(status+"|"+layer).style.display = display;
                    $('button.status-' + status + '.capability-' + layer).css('display', display);
                }
            });
        } else {
            mymap.getPane(layer).style.display = display;
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
