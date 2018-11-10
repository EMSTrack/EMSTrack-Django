var ambulanceMarkers = {};  // Store ambulance markers
var ambulances = {};        // Store ambulance details

var hospitalMarkers = {};   // Store hospital markers
var hospitals = {};	        // Store hospital details

var locationMarkers = {};   // Store location markers
var locations = {};	        // Store location details

var calls = {};             // Store call details

// Initialize category panes
var visibleCategory = {};

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

// resize map
var resizeMap = function() {
    $("#live-map").height($(window).height() - $('#base-navbar').outerHeight() - $('#map-navbar').outerHeight() - 5);
    mymap.invalidateSize();
};

// Ready function
$(function () {

    // token and attribution
    var attribution = 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="http://mapbox.com">Mapbox</a>';

    // Set map view
    mymap = L.map('live-map').setView([32.5149, -117.0382], 12);

    // Map to fill the view
    resizeMap();

    // Take care of resizing
    $(window).on("resize", function () { resizeMap(); }).trigger("resize");

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

    // Handle cancel dispatching button
    $('#dispatchCancelButton').click(function(event) {

        // Stop propagation to avoid collapse
        event.stopPropagation();

        // call end dispatching
        endDispatching();

    });

    // Event handler for when some1pxg is drawn. Only handles
    // when a new drawing is made for now.
    mymap.on(L.Draw.Event.CREATED,
        function (e) {
            var type = e.layerType;
            var layer = e.layer;
            if (type === 'marker') {
                // Do marker specific actions
            }
            // Do whatever else you need to. (save to db; add to map etc)
            mymap.addLayer(layer);
        });

    // Create category panes and filters
    createCategoryPanesAndFilters();

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
    $('#modal-button-ok').hide();
    $('#modal-button-cancel').hide();
    $('#modal-button-close').show();
    $("#dispatchModal").modal('show');

}

// alert using bootstrap modal
var bsdialog = function(message, alertClass, title) {

    // Show modal
    alertClass = alertClass || 'alert-danger';
    title = title || 'Attention';

    $('.modal-title').html(title);
    $('.modal-body').html(message).addClass(alertClass);
    return $("#dispatchModal");

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

        // Subscribe to ambulances
        $.each(data.ambulances, function (index) {
            var topicName = "ambulance/" + data.ambulances[index].ambulance_id + "/data";
            mqttClient.subscribe(topicName);
            console.log('Subscribing to topic: ' + topicName);
        });

        // Subscribe to hospitals
        $.each(data.hospitals, function (index) {
            var topicName = "hospital/" + data.hospitals[index].hospital_id + "/data";
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

    // retrieve calls from api
    console.log("Retrieving calls from API");
    $.getJSON(APIBaseUrl + 'call/', function (data) {

        console.log('calls = ' + calls);

        // Subscribe to current calls
        $.each(data, function (index) {
            console.log('data[index] = ' + data[index]);
            var topicName = "call/" + data[index].id + "/data";
            mqttClient.subscribe(topicName);
            console.log('Subscribing to topic: ' + topicName);
        });

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

        // Look for hospital/{id}/data
        else if (topic[0] === 'hospital' &&
            topic[2] == 'data') {
            updateHospital(data);
        }

        // Look for call/{id}/data
        else if (topic[0] === 'call' &&
            topic[2] == 'data') {
            updateCall(data);
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

        // get ambulance's old status
        var old_status = ambulances[id].status;
        var status = ambulance.status;
        var old_grid_length = $('#ambulance-grid-' + old_status).children().length - 1;
        var new_grid_length = $('#ambulance-grid-' + status).children().length + 1;

        // Remove existing marker
        mymap.removeLayer(ambulanceMarkers[id]);

        // update ambulance
        ambulances[id].status = status;
        ambulances[id].capability = ambulance.capability;
        ambulances[id].location.latitude = ambulance.location.latitude;
        ambulances[id].location.longitude = ambulance.location.longitude;
        ambulances[id].orientation = ambulance.orientation;

        // Overwrite ambulance
        ambulance = ambulances[id]

        // Move and update grid button
        var btnClass = 'btn btn-sm ' + ambulance_buttons[status]
            + ' status-' + status
            + ' capability-' + ambulance.capability;
        $("#grid-button-" + id).attr("class", btnClass)
            .detach()
            .appendTo($('#ambulance-grid-' + status));

        // update labels
        $('#ambulance-' + status + '-header').html(ambulance_status[status] + ' (' + new_grid_length + ')');
        if (old_grid_length)
            $('#ambulance-' + old_status + '-header').html(ambulance_status[old_status] +
                ' (' + old_grid_length + ')');
        else
            $('#ambulance-' + old_status + '-header').html(ambulance_status[old_status]);

    } else {

        // Add ambulance to grid
        addAmbulanceToGrid(ambulance);

    }

    // add ambulance to map
    addAmbulanceToMap(ambulance);

    // update detail panel
    // updateDetailPanel(ambulance);

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

function updateCall(call) {
    
    // retrieve id
    var id = call.id;

    // already exists?
    if (id in calls) {

        // Remove from calls
        delete calls[call.id];

        // Remove existing call
        $('#current-call-item-' + call.id).remove();

    }

    // add call to grid
    addCallToGrid(call);
    
}

function addAmbulanceToGrid(ambulance) {

    console.log('Adding ambulance "' + ambulance.identifier +
        '[id=' + ambulance.id + ', status=' + ambulance.status + ', btn=' + ambulance_buttons[ambulance.status] + ']"' +
        ' to grid');

    // make grid visible
    if (ambulance.status == 'AV')
        $('#ambulance-' + ambulance.status).addClass('show');

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
            this.style.opacity = '0.4';
            e.originalEvent.dataTransfer.setData("text/plain", ambulance.id);
        })
        .on('dragend', function (e) {
            // Restore opacity
            this.style.opacity = '1.0';
        })
        .click( function(e) {
            onGridButtonClick(ambulance);
        })
        .dblclick( function(e) {
            addToDispatchingList(ambulance);
        });

    // Update label
    var status = ambulance.status;
    $('#ambulance-' + status + '-header').html(ambulance_status[status] +
        ' (' + $('#ambulance-grid-' + status).children().length + ')');

};

function addCallToGrid(call) {

    console.log('Adding call "' + call.id + '[status=' + call.status + ']" to grid');

    // Add call to calls
    calls[call.id] = call;

    // Format date
    var date = (new Date(Date.parse(call.updated_on))).toLocaleString()

    // Add item to current-call grid
    $('#call-grid-' + call.status)
        .append(
            '<div class="form-group form-check mt-0 mb-1" id="current-call-item-' + call.id + '">\n' +
            '     <input type="checkbox" class="form-check-input" id="current-call-' + call.id + '">\n' +
            '     <label class="form-check-label" for="current-call-' + call.id + '">\n' +
            '       <strong>' + call.id + '</strong>: ' + date + '\n' +
            '     </label>\n' +
            '</div>\n');

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
            ambulance_status[ambulance.status] +
            "<br/>" +
            ambulance_capability[ambulance.capability] +
            "<br/>" +
            (new Date(Date.parse(ambulance.updated_on))).toLocaleString()
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
                // updateDetailPanel(ambulance);

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
function createCategoryPanesAndFilters() {

    // Initialize visibleCategories

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

    // Initialize panes

    // Create ambulance status category panes
    Object.keys(ambulance_status).forEach(function (status) {
        Object.keys(ambulance_capability).forEach(function (capability) {
            var pane = mymap.createPane(status+"|"+capability);
            pane.style.display = (visibleCategory[status] || visibleCategory[capability] ? 'block' : 'none');
        });
    });

    // Create hospital category pane
    var pane = mymap.createPane('hospital');
    pane.style.display = (visibleCategory['hospital'] ? 'block' : 'none');

    // Create location category panes
    Object.keys(location_type).forEach(function (type) {
        var pane = mymap.createPane(type);
        pane.style.display = (visibleCategory[type] ? 'block' : 'none');
    });

    // Create call status grids
    Object.keys(call_status).forEach(function (status) {

        $("#call-status").append(
            '<div class="card form-group mb-1 mt-0" id="call-card-' + status + '">\n' +
            '    <div class="card-header px-1 pb-0 pt-1"\n' +
            '         id="call-heading-' + status + '">\n' +
            '         <h6 style="cursor: pointer;"\n' +
            '             data-toggle="collapse"\n' +
            '             data-target="#call-' + status + '"\n' +
            '             aria-expanded="true" aria-controls="call-' + status + '">\n' +
            '             <input class="filter-checkbox" value="status" data-status="call-' + status + '"\n' +
            '                    type="checkbox" id="call-checkbox-' + status + '">\n' +
            '             <span role="button">' + call_status[status] + '</span>\n' +
            '          </h6>\n' +
            '    </div>\n' +
            '    <div class="collapse"\n' +
            '         id="call-' + status + '"\n' +
            '         aria-labelledby="call-heading-' + status + '"\n' +
            '         data-parent="#call-status">\n' +
            '         <div class="card-body py-1 px-1"\n' +
            '              id="call-grid-' + status + '">\n' +
            '         </div>\n' +
            '    </div>\n' +
            '</div>');
    });

    // Create ambulance status grids
    Object.keys(ambulance_status).forEach(function (status) {

        // Create grid
        $("#ambulance-status").append(
            '<div class="card form-group mb-1 mt-0" id="ambulance-card-' + status + '">\n' +
            '    <div class="card-header px-1 pb-0 pt-1"\n' +
            '         id="ambulance-heading-' + status + '">\n' +
            '         <h6 style="cursor: pointer;"\n' +
            '             data-toggle="collapse"\n' +
            '             data-target="#ambulance-' + status + '"\n' +
            '             aria-expanded="true" aria-controls="ambulance-' + status + '">\n' +
            '             <input class="filter-checkbox" value="status" data-status="' + status + '"\n' +
            '                    type="checkbox" id="ambulance-checkbox-' + status + '" ' +
            (visibleCategory[status] ? 'checked' : '') + '>\n' +
            '             <span id="ambulance-' + status + '-header" role="button">' +
            '                    ' + ambulance_status[status] + '\n' +
            '             </span>\n' +
            '          </h6>\n' +
            '    </div>\n' +
            '    <div class="collapse"\n' +
            '         id="ambulance-' + status + '"\n' +
            '         aria-labelledby="ambulance-heading-' + status + '"\n' +
            '         data-parent="#ambulance-status">\n' +
            '         <div class="card-body py-1 px-0"\n' +
            '              id="ambulance-grid-' + status + '">\n' +
            '         </div>\n' +
            '    </div>\n' +
            '</div>');

        // Make them dropable
        $('#ambulance-card-' + status)
            .on('dragover', function(e) {
                e.preventDefault();
            })
            .on('drop', function(e) {
                e.preventDefault();
                // Dropped button, get data
                var ambulance_id = e.originalEvent.dataTransfer.getData("text/plain");
                var ambulance = ambulances[ambulance_id];
                console.log('dropped ambulance ' + ambulance['identifier']);
                // change status
                updateAmbulanceStatus(ambulance, status);
            });

    });

    // Create capability options
    Object.keys(ambulance_capability).forEach(function (capability) {

        $("#ambulance-capability").append(
            '<div class="form-group form-check mt-0 mb-1">\n' +
            '     <input class="form-check-input filter-checkbox" value="capability" data-status="' + capability + '"\n' +
            '            type="checkbox" id="capability-' + capability + '" ' +
            (visibleCategory[capability] ? 'checked' : '') + '>\n' +
            '     <label class="form-check-label"\n' +
            '            for="capability-' + capability + '">' + ambulance_capability[capability] + '</label>\n' +
            '</div>');
    });

    // Create location options
    $("#location-type").append(
        '<div class="form-group form-check mt-0 mb-1">\n' +
        '     <input class="form-check-input filter-checkbox" value="location" data-status="hospital"\n' +
        '            type="checkbox" id="location-hospital" ' +
        (visibleCategory['hospital'] ? 'checked' : '') + '>\n' +
        '     <label class="form-check-label"\n' +
        '            for="location-hospital">Hospital</label>\n' +
        '</div>');
    Object.keys(location_type).forEach(function (type) {

        $("#location-type").append(
            '<div class="form-group form-check mt-0 mb-1">\n' +
            '     <input class="form-check-input filter-checkbox" value="location" data-status="' + type + '"\n' +
            '            type="checkbox" id="location-' + type + '" ' +
            (visibleCategory[type] ? 'checked' : '') + '>\n' +
            '     <label class="form-check-label"\n' +
            '            for="location-' + type + '">' + location_type[type] + '</label>\n' +
            '</div>');
    });

    // Add listener to remove or add layer when filter checkbox is clicked
    $('.filter-checkbox').click(function (event) {

        // Stop propagation to avoid collapse
        event.stopPropagation();

    });

    $('.filter-checkbox').change(function (event) {

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

        // Modify panes
        if (this.value == 'status') {
            // Add to all visible capability panes
            Object.keys(ambulance_capability).forEach(function (capability) {
                if (visibleCategory[capability]) {
                    mymap.getPane(layer+"|"+capability).style.display = display;
                }
            });
        } else if (this.value == 'capability') {
            // Add to all visible status layers
            Object.keys(ambulance_status).forEach(function (status) {
                if (visibleCategory[status]) {
                    mymap.getPane(status+"|"+layer).style.display = display;
                }
            });
        } else {
            mymap.getPane(layer).style.display = display;
        }

    });


};

function onGridButtonClick(ambulance) {

    // Update detail panel
    // updateDetailPanel(ambulance);

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

function updateAmbulanceStatus(ambulance, status) {

    // return in case of no change
    if (ambulance.status == status)
        return;

    // Show modal
    $('#modal-button-ok').show();
    $('#modal-button-cancel').show();
    $('#modal-button-close').hide();
    bsdialog('Are you sure you want to modify ambulance "<b>'
        + ambulance.identifier
        + '</b>" status?', 'alert-danger', 'Attention')
        .on('hide.bs.modal', function(event) {

            var $activeElement = $(document.activeElement);

            if ($activeElement.is('[data-toggle], [data-dismiss]')) {

                if ($activeElement.attr('id') == 'modal-button-ok') {
                    // Do something with the button that closed the modal
                    // Update status
                    doUpdateAmbulanceStatus(ambulance, status);

                }

            }

        })
        .modal('show');

}

function doUpdateAmbulanceStatus(ambulance, status) {

    // form
    var form = { status: status };

    // make json call
    var postJsonUrl = APIBaseUrl + 'ambulance/' + ambulance.id + '/';

    var CSRFToken = Cookies.get('csrftoken');

    // retrieve csrf token
    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!CSRFSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", CSRFToken);
            }
        }
    });

    // make ajax call
    $.ajax({
        url: postJsonUrl,
        type: 'PATCH',
        dataType: 'json',
        contentType: 'application/json',
        data: JSON.stringify(form),
        success: function (data) {

            // Log success
            console.log("Succesfully posted ambulance status update: status = " + status);

            // show target card
            $('#ambulance-' + status).collapse('show');

        },
        error: function (jqXHR, textStatus, errorThrown) {

            // Log failure
            console.log("Failed to post ambulance status update.");
            console.log(jqXHR.responseText);

        }
    });

}