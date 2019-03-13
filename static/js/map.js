import $ from "jquery";

import L from "leaflet";
import "leaflet-rotatedmarker";
import "leaflet/dist/leaflet.css";

import { Geocoder } from "./geocoder";

// Dispatching data

const markersGroup = new L.LayerGroup();
let isDispatching = false;
let isFilterOpen = false;
const placeIcon = L.icon({
    iconUrl: '/static/icons/place_marker.png',
    iconSize: [40, 40],
    iconAnchor: [20, 40],
    popupAnchor: [0, -40]
});

let dispatchingAmbulances = {};
let numberOfDispatchingAmbulances = 0;

let currentAddress;
let currentLocation;
let currentPatients;

// Map data

const ambulanceMarkers = {};  // Store ambulance markers
const ambulances = {};        // Store ambulance details

const hospitalMarkers = {};   // Store hospital markers
const hospitals = {};	        // Store hospital details

const locationMarkers = {};   // Store location markers
const locations = {};	        // Store location details

const calls = {};             // Store call details
const patientMarkers = {};    // Store hospital markers

// Initialize category panes
const visibleCategory = {};

// Initialize ambulance icons
const ambulance_icons = {};
const ambulance_buttons = {};
for (const key in ambulance_css) {
    // skip loop if the property is from prototype
    if (!ambulance_css.hasOwnProperty(key))
        continue;

    const settings = ambulance_css[key];
    ambulance_icons[key] = L.icon(settings['icon']);
    ambulance_buttons[key] = 'btn-' + settings['class'];
}

// Initialize ambulance call status
const ambulance_call_buttons = {
    R: 'btn-danger', // 'Requested'
    A: 'btn-success', // 'Accepted'
    D: 'btn-secondary', // 'Declined'
    S: 'btn-primary', // 'Suspended'
    C: 'btn-dark' // 'Completed'
};

function newFontAwesomeStackedIcon(options) {
        return new L.divIcon({
            html: '<span class="fa-stack fa-2x ' + options.extraClasses + '">' +
                  '<i class="fas fa-map-marker fa-stack-2x"></i>' +
                  '<i class="fas fa-' + options.icon + ' fa-stack-1x fa-inverse" style="margin-top:0.2em"></i>' +
                  '</span>',
            popupAnchor: [0, -15],
            className: 'myDivIcon'
        });
    }

// Creates a red marker with the coffee icon
// L.AwesomeMarkers.Icon.prototype.options.prefix = 'fa';

function callDate(call) {

    // Get relevant date
    let date = call.updated_on;
    if (status === 'P')
        date = call.pending_at;
    else if (status === 'S')
        date = call.started_at;

    // Format date
    return (new Date(Date.parse(date))).toLocaleTimeString();

}

function waypointIcon(waypoint) {

    const location = waypoint['location'];
    let icon;
    if (location.type === 'i') {
        icon = 'plus';
    } else if (location.type === 'h') {
        icon = 'hospital';
    } else if (location.type === 'w') {
        icon = 'map';
    } else if (location.type === 'b') {
        icon = 'home';
    } else {
        console.log("Unknown waypoint location type '" + location.type + "'.");
        icon = 'question';
    }

    let color_class;
    if (waypoint.status === 'C') {
        color_class = 'text-danger';
    } else if (waypoint.status === 'V') {
        color_class = 'text-primary';
    } else if (waypoint.status === 'D') {
        color_class = 'text-success';
    } else if (waypoint.status === 'S') {
        color_class = 'text-muted';
    } else {
        console.log("Unknown waypoint class '" + waypoint.status + "'.");
        color_class = 'text-warning';
    }

    return newFontAwesomeStackedIcon({
        icon: icon,
        extraClasses: 'fa-stack-marker-xs ' + color_class
    });

}


const patientMarker = newFontAwesomeStackedIcon({
    icon: 'plus',
    extraClasses: 'fa-stack-marker-xs text-danger'
});

const hospitalMarker = newFontAwesomeStackedIcon({
    icon: 'hospital',
    extraClasses: 'fa-stack-marker-xs text-warning'
});

const waypointMarker = newFontAwesomeStackedIcon({
    icon: 'map',
    extraClasses: 'fa-stack-marker-xs text-primary'
});

const baseMarker = newFontAwesomeStackedIcon({
    icon: 'home',
    extraClasses: 'fa-stack-marker-xs text-success'
});


const patientIcon = L.icon({
    iconUrl: '/static/icons/maki/marker-15.svg',
    iconSize: [15, 15]
});

const hospitalIcon = L.icon({
    iconUrl: '/static/icons/maki/hospital-15.svg',
    iconSize: [15, 15]
});

const incidentIcon = L.icon({
    iconUrl: '/static/icons/maki/marker-15.svg',
    iconSize: [15, 15]
});

const defibrillatorIcon = L.icon({
    iconUrl: '/static/icons/maki/defibrillator-15.svg',
    iconSize: [15, 15]
});

const baseIcon = L.icon({
    iconUrl: '/static/icons/maki/home-15.svg',
    iconSize: [15, 15]
});

const otherIcon = L.icon({
    iconUrl: '/static/icons/maki/marker-15.svg',
    iconSize: [15, 15],
    iconAnchor: [7, 15],
    popupAnchor: [0, -15]
});

const locationIcon = L.icon({
    iconUrl: '/static/icons/maki/marker-15.svg',
    iconSize: [15, 15],
    iconAnchor: [7, 15],
    popupAnchor: [0, -15]

});

/**
 * Ambulance statuses
 */
const STATUS_AVAILABLE = "AV";
const STATUS_OUT_OF_SERVICE = "OS";

// global variable for mqttClient
let mqttClient;

/**
 * This is a handler for when the page is loaded.
 */
let mymap;
const geocoder = new Geocoder({map_provider: map_provider});

// resize map
function resizeMap() {
    $("#live-map").height($(window).height() - $('#base-navbar').outerHeight() - $('#map-navbar').outerHeight() - 5);
    mymap.invalidateSize();
};

// Ready function
$(function () {

    // token and attribution
    const attribution = 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="http://mapbox.com">Mapbox</a>';

    // Set map view
    mymap = L.map('live-map').setView([32.5149, -117.0382], 12);

    // Map to fill the view
    resizeMap();

    // Take care of resizing
    $(window).on("resize", function () { resizeMap(); }).trigger("resize");

    // geocoder = L.mapbox.geocoder('mapbox.places');

    if (map_provider['provider'] === 'mapbox') {

        // Add layer to map
        L.tileLayer(
            'https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token=' + map_provider['access_token'],
            {
                attribution: attribution,
                maxZoom: 18,
                id: 'mapbox.streets',
                accessToken: map_provider['access_token']
            }
        ).addTo(mymap);

    }

    /*
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
            var layer = e.layer;
            if (type === 'marker') {
                // Do marker specific actions
            }
            // Do whatever else you need to. (save to db; add to map etc)
            mymap.addLayer(layer);
        });
    */

    // Handle begin dispatching button
    $('#dispatchBeginButton').click(function(event) {

        // call end dispatching
        beginDispatching();

    });

    // Handle submit dispatching button
    $('#dispatchSubmitButton').click(function(event) {

        // call end dispatching
        submitDispatching();

    });

    // Handle cancel dispatching button
    $('#dispatchCancelButton').click(function(event) {

        // Stop propagation to avoid collapse
        event.stopPropagation();

        // call end dispatching
        endDispatching();

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

        /*
        // set will message
        var willMessage = new Paho.MQTT.Message('D');
        willMessage.destinationName = 'user/' + username + '/client/' + clientId + '/status';
        willMessage.qos = 2;
        willMessage.retained = false;
        */

        // attempt to connect to MQTT broker
        mqttClient.connect({
            //connection attempt timeout in seconds
            timeout: 60,
            userName: username,
            password: password,
            useSSL: true,
            cleanSession: true,
            onSuccess: onConnect,
            onFailure: onConnectFailure
            // , willMessage: willMessage,
        });

    })
        .fail(function (jqxhr, textStatus, error) {

            bsalert("Connection to MQTT broker failed: \"" +
                textStatus + "," + error + "\"\n" +
                "Information will not be updated in real time.");

        });

});

// alert using bootstrap modal
function bsalert(message, alertClass, title) {

    // Show modal
    alertClass = alertClass || 'alert-danger';
    title = title || 'Alert';

    $('.modal-title').html(title);
    $('.modal-body').html(message).addClass(alertClass);
    $('#modal-button-ok').hide();
    $('#modal-button-cancel').hide();
    $('#modal-button-close').show();
    $("#dispatchModal").modal('show');

}

// alert using bootstrap modal
function bsdialog(message, alertClass, title) {

    // Show modal
    alertClass = alertClass || 'alert-danger';
    title = title || 'Attention';

    $('.modal-title').html(title);
    $('.modal-body').html(message).addClass(alertClass);
    return $("#dispatchModal");

}

function getData(subscribe) {

    // default is true
    subscribe = subscribe || true;

    // Retrieve ambulances from API
    console.log("Retrieving ambulances from API");
    $.getJSON(APIBaseUrl + 'ambulance/', function (data) {

        let n = 0;
        let lat = 0;
        let lon = 0;

        // Update ambulances
        data.forEach((ambulance) => {

            // update ambulance
            updateAmbulance(ambulance);

            // calculate center of the ambulances
            n = n + 1;
            lat += ambulance.location.latitude;
            lon += ambulance.location.longitude;


        });

        // Center map
        if (n > 0) {
            // Set map view
            lat = lat / n;
            lon = lon / n;
            console.log('Center at lat = ' + lat + ', lon = ' + lon);

            mymap.setView([lat, lon], 12);
        }

        if (subscribe) {

            data.forEach((ambulance) => {

                // Subscribe to ambulance
                let topicName = "ambulance/" + ambulance.id + "/data";
                mqttClient.subscribe(topicName);
                console.log('Subscribing to topic: ' + topicName);

                // Subscribe to ambulance calls
                topicName = "ambulance/" + ambulance.id + "/call/+/status";
                mqttClient.subscribe(topicName);
                console.log('Subscribing to topic: ' + topicName);

            });

        }

    });

    // Retrieve hospitals from API
    console.log("Retrieving hospitals from API");
    $.getJSON(APIBaseUrl + 'hospital/', function (data) {

        // Retrieve hospitals
        $.each(data, function (i, hospital) {

            // update hospital
            updateHospital(hospital);

            if (subscribe) {

                // subscribe to hospital
                const topicName = "hospital/" + hospital.id + "/data";
                mqttClient.subscribe(topicName);
                console.log('Subscribing to topic: ' + topicName);

            }

        });
    });

    // Retrieve hospitals from API
    console.log("Retrieving locations from API");
    $.getJSON(APIBaseUrl + 'location/Hospital/', function (data) {

        // add location
        $.each(data, function (index) {
            const location = data[index];
            addLocationToMap(location);
        });
    });

    // Retrieve bases from API
    $.getJSON(APIBaseUrl + 'location/Base/', function (data) {

        // add location
        $.each(data, function (index) {
            const location = data[index];
            addLocationToMap(location);
        });
    });


    // retrieve calls from api
    console.log("Retrieving calls from API");
    $.getJSON(APIBaseUrl + 'call/', function (data) {

        // Subscribe to current calls
        $.each(data, function (i, call) {

            // update call
            updateCall(call);

            if (subscribe) {

                const topicName = "call/" + call.id + "/data";
                mqttClient.subscribe(topicName);
                console.log('Subscribing to topic: ' + topicName);
            }

        });

    });

}

/* Handle connect */
function onConnect() {

    console.log("Connected to MQTT broker");

    /*
    // handshake online
    var onlineMessage = new Paho.MQTT.Message('O');
    onlineMessage.destinationName = 'user/' + username + '/client/' + clientId + '/status';
    onlineMessage.qos = 2;
    onlineMessage.retained = false;
    mqttClient.send(onlineMessage);
    console.log('Sent online message');
    */

    // get data
    getData();

};

/* Handle missconnection */
function onConnectFailure(message) {

    bsalert("Connection to MQTT broker failed: " + message.errorMessage +
        "Information will not be updated in real time.");

    // get data without subscribing
    getData(false);

};

/* Handle 'ambulance/+/data' mqtt messages */
function onMessageArrived(message) {

    console.log('Message "' +
        message.destinationName + ':' + message.payloadString +
        '" arrived');

    // split topic
    const topic = message.destinationName.split("/");

    // empty payload?
    if (message.payloadString) {

        try {

            // parse message
            const data = JSON.parse(message.payloadString);

            // Look for ambulance/{id}/data
            if (topic[0] === 'ambulance' &&
                topic[2] === 'data') {
                updateAmbulance(data);
            }

            // Look for hospital/{id}/data
            else if (topic[0] === 'hospital' &&
                topic[2] === 'data') {
                updateHospital(data);
            }

            // Look for call/{id}/data
            else if (topic[0] === 'call' &&
                topic[2] === 'data') {
                updateCall(data);
            }

            // look for ambulance call information
            else if (topic[0] === 'ambulance' &&
                topic[2] === 'call' &&
                topic[4] === 'status') {
                const ambulance_id = topic[1];
                const call_id = topic[3];
                updateAmbulanceCall(ambulance_id, call_id, data);
            }

            else
                console.log('Unknown topic ' + topic);

        } catch (e) {

            bsalert('Error processing message "' +
                message.destinationName + ':' + message.payloadString +
                '"' + '<br/>' + 'error = "' + e + '"');

            throw e;

        }

    } else
        // This can happen if a topic is being unretained
        console.log('Message "' + message.destinationName  + '" has an empty payload');

}

function updateAmbulance(ambulance) {

    // retrieve id
    const id = ambulance.id;

    // already exists?
    if (id in ambulances) {

        // get ambulance's old status
        const old_status = ambulances[id].status;
        const status = ambulance.status;

        let old_grid_length;
        let new_grid_length;
        if (old_status !== status) {
            old_grid_length = $('#ambulance-grid-' + old_status).children().length - 1;
            new_grid_length = $('#ambulance-grid-' + status).children().length + 1;
        } else {
            old_grid_length = new_grid_length = $('#ambulance-grid-' + status).children().length ;
        }

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

        if (old_status !== status) {

            // Move and update grid button
            const btnClass = 'btn btn-sm ' + ambulance_buttons[status]
                + ' status-' + status
                + ' capability-' + ambulance.capability;
            $("#grid-button-" + id).attr("class", btnClass)
                .detach()
                .appendTo($('#ambulance-grid-' + status));

            // update count labels
            $('#ambulance-' + status + '-header-count').html('(' + new_grid_length + ')').show();
            if (old_grid_length)
                $('#ambulance-' + old_status + '-header-count').html('(' + old_grid_length + ')').show();
            else
                $('#ambulance-' + old_status + '-header-count').hide();

            console.log("> oldstatus '" + old_status + "' count = '" + old_grid_length + "'");
            console.log("> newstatus '" + status + "' count = '" + new_grid_length + "'");
        }

    } else {

        // Add ambulance to grid
        addAmbulanceToGrid(ambulance);

    }

    // add ambulance to map
    addAmbulanceToMap(ambulance);

};

function updateHospital(hospital) {

    // retrieve id
    const id = hospital.id;

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
    if (ambulance.status === 'AV')
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

    // Make button clickable and draggable
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
            onGridAmbulanceButtonClick(ambulance);
        })
        .dblclick( function(e) {
            addToDispatchingList(ambulance);
        });

    // Update label
    const status = ambulance.status;
    const count = $('#ambulance-grid-' + status).children().length;
    $('#ambulance-' + status + '-header-count')
        .html('(' + count + ')')
        .show();

    console.log("> status '" + status + "' count = '" + count + "'");

};

function updateCall(call) {

    // retrieve id
    const id = call.id;
    const status = call.status;

    // already exists?
    if (id in calls) {

        // retrieve old status
        const matches = $('#call-item-' + id).attr('class').match(/status-(\w)/);
        let old_status = null;
        if (matches.length > 1) {

            // call exists!
            old_status = matches[1];
            if (status !== old_status) {

                // Create new visible category
                visibleCategory[status + "|" + 'call_' + call.id] = true;

                // Create new pane
                let pane = mymap.createPane(status + "|" + 'call_' + call.id);
                pane.style.display = (visibleCategory[status + "|" + 'call_' + call.id] ? 'block' : 'none');

                // remove old visibile category
                delete visibleCategory[old_status + "|" + 'call_' + id]

                // status changed
                if (status !== 'E') {

                    // move to new category
                    $('#call-item-' + id)
                        .detach()
                        .appendTo($('#call-grid-' + status));

                } else { // status == 'E'

                    // Completed call, unsubscribe
                    const topicName = "call/" + id + "/data";
                    mqttClient.unsubscribe(topicName);
                    console.log('Unsubscribing from topic: ' + topicName);

                    // remove from grid
                    $('#call-item-' + id).remove();

                    // Remove from calls
                    delete calls[id];

                }

            }

            // update call counter
            updateCallCounter();

            // Get call date
            const date = callDate(call);

            // update label
            $('#call-text-' + call.id)
                .html( callToHtmlShort(call, date) );

            // Update waypoints
            if (status === 'E') {

                // remove waypoints
                call.ambulancecall_set.forEach(function (ambulance_call) {

                    // Remove waypoints
                    removeWaypoints(call.id, ambulance_call.ambulance_id);

                });

            } else {

                // get patients
                const patients = compilePatients(call);

                // update waypoints
                for (const ambulance_call of call.ambulancecall_set) {

                    // Remove waypoints
                    removeWaypoints(call.id, ambulance_call.ambulance_id);

                    // add waypoints
                    let nextWaypoint = addWaypoints(call, ambulance_call.ambulance_id,
                        ambulance_call['waypoint_set'], date, patients);

                    // set next waypoint
                    ambulance_call['next_waypoint'] = nextWaypoint;

                }

            }

        } else

            console.log('Could not match current call status');

    } else {

        // add call to grid
        addCallToGrid(call);

        // add call to map
        addCallToMap(call);
        
    }

}

function updateAmbulanceCall(ambulance_id, call_id, status) {

    let topicName;
    if (status === 'C') {

        // Completed ambulance call, unsubscribe
        topicName = "ambulance/" + ambulance_id + "/call/+/status";
        mqttClient.unsubscribe(topicName);
        console.log('Unsubscribing from topic: ' + topicName);

    } else {

        if (call_id in calls) {

            // retrieve old status
            const matches = $('#call-grid-button-' + call_id + '-' + ambulance_id).attr('class').match(/status-(\w)/);
            let old_status = null;
            if (matches.length > 1) {

                // ambulance call exists!
                old_status = matches[1];
                if (status !== old_status) {

                    // update button class
                    $('#call-grid-button-' + ambulance_id)
                        .removeClass(ambulance_call_buttons[old_status])
                        .addClass(ambulance_call_buttons[status]);

                }

            }

        } else {

            // retrieve call from api
            console.log("Retrieving call from API");
            $.getJSON(APIBaseUrl + 'call/' + call_id + '/', function (call) {

                // update call
                updateCall(call);

                // subscribe to call
                topicName = "call/" + call_id + "/data";
                mqttClient.subscribe(topicName);
                console.log('Subscribing to topic: ' + topicName);

            });

        }

    }
}

function updateCallCounter() {

    let total = 0;
    call_status_order.forEach(function(status) {
        if (status !== 'E') {
            const count = $('#call-grid-' + status).children().length;
            total += count;
            if (count > 0)
                $('#call-' + status + '-header-count').html('(' + count + ')').show();
            else
                $('#call-' + status + '-header-count').hide();
        }
    });

    if (total > 0)
        $('#call-header-count').html('(' + total+ ')').show();
    else
        $('#call-header-count').hide();

}

function addCallToGrid(call) {

    console.log('Adding call "' + call.id + '[status=' + call.status + ']" to grid');

    // Add call to calls
    calls[call.id] = call;

    // Get status
    const status = call.status;

    // Get relevant date
    const date = callDate(call);

    // Create visible category
    visibleCategory[status + "|" + 'call_' + call.id] = true;

    // Create pane
    let pane = mymap.createPane(status + "|" + 'call_' + call.id);
    pane.style.display = (visibleCategory[status + "|" + 'call_' + call.id] ? 'block' : 'none');

    // Add item to call grid
    $('#call-grid-' + status)
        .append(
            '<div class="card status-' + status + '" id="call-item-' + call.id + '">\n' +
            '  <div class="card-header px-1 py-1" id="call-' + call.id + '">\n' +
            '     <input class="filter-checkbox" value="call" data-status="' + status + '|call_' + call.id + '"\n' +
            '            type="checkbox" id="call-checkbox-' + call.id + '" ' +
            (visibleCategory[status + "|" + 'call_' + call.id] ? 'checked' : '') + '>\n' +
            '     <button type="button"\n' +
            '             id="call-' + call.id + '-button"\n' +
            '             style="margin: 2px 2px;"\n' +
            '             class="btn btn-outline-' + call_priority_css[call.priority].class + '">' +
            '       ' + call_priority_css[call.priority].html + '\n' +
            '     </button>\n' +
            '     <div class="float-right" id="call-text-' + call.id + '">' + callToHtmlShort(call, date) + '</div>\n' +
            '  </div>\n' +
            '  <div class="card-body px-1 py-1" id="call-item-grid-' + call.id + '">\n' +
            '  </div>\n' +
            '</div>\n');

    // Make call button clickable
    $('#call-' + call.id + '-button')
        .click(function (e) {
            onCallButtonClick(call);
        });

    // Add listener to remove or add layer when filter checkbox is clicked
    $('#call-checkbox-' + call.id)
        .click(function (event) {

            // Stop propagation to avoid collapse
            event.stopPropagation();

        })
        .change(function () { visibilityCheckbox(this); } );

    // add ambulances
    for (const ambulance_call of call.ambulancecall_set) {

        // get ambulance
        const ambulance = ambulances[ambulance_call.ambulance_id];

        // Add ambulance button to call item grid
        $('#call-item-grid-' + call.id)
            .append('<button type="button"'
                + ' id="call-grid-button-' + call.id + '-' + ambulance.id + '"'
                + ' class="btn btn-sm '
                + ambulance_call_buttons[ambulance_call.status]
                + ' status-' + ambulance_call.status + '"'
                + ' style="margin: 2px 2px;"'
                + ' draggable="true">'
                + ambulance.identifier
                + '</button>');

        // Make button clickable and draggable
        $('#call-grid-button-' + call.id + '-'+ ambulance.id)
            .click(function (e) {
                onGridAmbulanceButtonClick(ambulance);
            });

    }

    // update call counter
    updateCallCounter();

}

function locationToHtml(location) {

    // format address
    let address_str = [location.number, location.street, location.unit].join(' ').trim();

    if (address_str !== "") {
        if (location.neighborhood !== "")
            address_str = [address_str, location.neighborhood].join(', ').trim();
    } else
        address_str += location.neighborhood.trim()

    if (address_str !== "")
        address_str = [address_str, location.city, location.state].join(', ').trim();
    else
        address_str = [location.city, location.state].join(', ').trim();

    address_str = [address_str, location.zipcode].join(' ').trim();
    address_str = [address_str, location.country].join(', ').trim();

    return (
        '<div>' +
        '<p class="my-0 py-0"><em>Address:</em></p>' +
        '<p class="my-0 py-0"><span class="text-right">' + address_str + '</span></p>' +
        '<p class="my-0 py-0"><em>Type:</em>' +
        '<span class="float-right">' + location_type[location.type] + '</span></p>' +
        '</div>'
    );

}

function callToHtml(call, date, patients, number_of_waypoints, waypoint) {

    return (
        '<div>' +
        '<p class="my-0 py-0"><strong>Priority:</strong>' +
        '<span class="float-right">' + call.priority + '</span></p>' +
        '<p class="my-0 py-0"><strong>Date:</strong>' +
        '<span class="float-right">' + date + '</span></p>' +
        '<p class="my-0 py-0"><strong>Details:</strong>' +
        '<span class="float-right">' + call.details + '</span></p>' +
        '<p class="my-0 py-0"><strong>Patients:</strong>' +
        '<span class="float-right">' + patients + '</span></p>' +
        '<p class="my-0 py-0"><strong>Number of waypoints:</strong>' +
        '<span class="float-right">' + number_of_waypoints + '</span></p>' +
        '<p class="my-0 py-0"><strong>Next waypoint:</strong></p>' +
        locationToHtml(waypoint.location) +
        '</div>'
    );
}

function callToHtmlShort(call, date) {

    let patients;
    if (call.patient_set.length === 0) {
        patients = "no patients";
    } else if (call.patient_set.length === 1) {
        patients = '1 patient';
    } else if (call.patient_set.length > 1) {
        patients = call.patient_set.length + ' patients';
    }

    return (date + ', ' + patients);
}

function addWaypoints(call, ambulance_id, waypoint_set, date, patients) {

    // sort waypoints
    waypoint_set.sort(function(a,b) {return (a.order - b.order);});

    // waypoints layer id
    const id = call.id + '_' + ambulance_id;

    // create group layer
    patientMarkers[id] = L.layerGroup();

    // waypoint center
    let nextWaypoint = null;

    // loop over waypoints
    waypoint_set.forEach(function (waypoint) {

        // get icon
        const location = waypoint.location;
        const icon = waypointIcon(waypoint);

        // is it next?
        if (waypoint.status === 'C' || waypoint.status === 'V' &&
            nextWaypoint === null)
            nextWaypoint = waypoint;

        // create marker
        let marker = L.marker(
            [location.location.latitude, location.location.longitude],
            {
                icon: icon,
                pane:  call.status + "|" + 'call_' + call.id
            });

        // Add popup to the incident location
        if (waypoint === nextWaypoint) {

            // bind popup to next waypoint
            marker.bindPopup( callToHtml(call, date, patients,
                waypoint_set.length, waypoint) );

            // Collapse panel on icon hover.
            marker
                .on('mouseover',
                    function (e) {
                        // open popup bubble
                        this.openPopup().on('mouseout',
                            function (e) {
                                this.closePopup();
                            });
                    });

        }

        // add layer to group layer
        patientMarkers[id].addLayer( marker );

    });

    // add group layer to map
    patientMarkers[id].addTo(mymap);

    // return next waypoint
    return nextWaypoint;

}

function removeWaypoints(call_id, ambulance_id) {

    // build id
    const id = call_id + '_' + ambulance_id;

    // remove layer
    mymap.removeLayer(patientMarkers[id]);
    delete patientMarkers[id];

}

function compilePatients(call) {

    // get patients
    let patients;
    if (call.patient_set.length === 0) {
        patients = "No patient information";
    } else
        patients = call.patient_set.join(', ');

    return patients;
}

function addCallToMap(call) {

    // get patients
    const patients = compilePatients(call);

    // Get relevant date
    let date = callDate(call);

    // Add incident locations
    call.ambulancecall_set.forEach(function (ambulance_call) {

        // add waypoints
        const nextWaypoint = addWaypoints(call, ambulance_call.ambulance_id,
            ambulance_call['waypoint_set'], date, patients);

        // set next waypoint
        ambulance_call['next_waypoint'] = nextWaypoint;

    });

}

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
            "<strong>" + ambulance.identifier + "</strong>" +
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
    const coloredIcon = hospitalIcon;

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
    let icon = locationIcon;
    if (location.type === 'a')
        icon = defibrillatorIcon;
    else if (location.type === 'b')
        icon = baseIcon;
    else if (location.type === 'i')
        icon = incidentIcon;

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

/* Create category filter */
function createCategoryPanesAndFilters() {

    // Initialize visibleCategories

    // add status
    ambulance_status_order.forEach(function(status) {
        visibleCategory[status] = true;
    });

    // add capability
    ambulance_capability_order.forEach(function(capability) {
        visibleCategory[capability] = true;
    });

    // add hospital
    visibleCategory['hospital'] = true;

    // add calls
    call_status_order.forEach(function (status) {
        visibleCategory['call_' + status] = true;
    });

    // add location_type
    location_type_order.forEach(function(type) {
        visibleCategory[type] = false;
    });

    // Initialize panes

    // Create hospital category pane
    let pane = mymap.createPane('hospital');
    pane.style.display = (visibleCategory['hospital'] ? 'block' : 'none');

    // Create location category panes
    location_type_order.forEach(function (type) {
        pane = mymap.createPane(type);
        pane.style.display = (visibleCategory[type] ? 'block' : 'none');
    });

    // Create ambulance status category panes
    ambulance_status_order.forEach(function (status) {
        ambulance_capability_order.forEach(function (capability) {
            pane = mymap.createPane(status + "|" + capability);
            pane.style.display = (visibleCategory[status] || visibleCategory[capability] ? 'block' : 'none');
        });
    });

    // Create call status grids
    call_status_order.forEach(function (status) {

        // ignore ended calls
        if (status != 'E')
            $("#call-status").append(
                '<div class="card form-group mb-1 mt-0" id="call-card-' + status + '">\n' +
                '    <div class="card-header px-1 pb-0 pt-1"\n' +
                '         id="call-heading-' + status + '">\n' +
                '         <h6 style="cursor: pointer;"\n' +
                '             data-toggle="collapse"\n' +
                '             data-target="#call-' + status + '"\n' +
                '             aria-expanded="true" aria-controls="call-' + status + '">\n' +
                '             <input class="filter-checkbox" value="call-status" data-status="' + status + '"\n' +
                '                    type="checkbox" id="call-checkbox-' + status + '" checked>\n' +
                '             <span id="call-' + status + '-header" role="button">' + call_status[status] + '</span>\n' +
                '             <span id="call-' + status + '-header-count"></span>\n' +
                '          </h6>\n' +
                '    </div>\n' +
                '    <div class="collapse"\n' +
                '         id="call-' + status + '"\n' +
                '         aria-labelledby="call-heading-' + status + '"\n' +
                '         data-parent="#call-status">\n' +
                '         <div class="card-body py-0 px-0"\n' +
                '              id="call-grid-' + status + '">\n' +
                '         </div>\n' +
                '    </div>\n' +
                '</div>');

    });

    // Create ambulance status grids
    ambulance_status_order.forEach(function (status) {

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
            '             <span id="ambulance-' + status + '-header-count"></span>\n' +
            '          </h6>\n' +
            '    </div>\n' +
            '    <div class="collapse"\n' +
            '         id="ambulance-' + status + '"\n' +
            '         aria-labelledby="ambulance-heading-' + status + '">\n' +
            '         <div class="card-body py-1 px-0"\n' +
            '              id="ambulance-grid-' + status + '">\n' +
            '         </div>\n' +
            '    </div>\n' +
            '</div>');
            //'         data-parent="#ambulance-status">\n' +

        // Make them dropable
        $('#ambulance-card-' + status)
            .on('dragover', function(e) {
                e.preventDefault();
            })
            .on('drop', function(e) {
                e.preventDefault();
                // Dropped button, get data
                const ambulance_id = e.originalEvent.dataTransfer.getData("text/plain");
                const ambulance = ambulances[ambulance_id];
                console.log('dropped ambulance ' + ambulance['identifier']);
                // change status
                updateAmbulanceStatus(ambulance, status);
            });

    });

    // Create capability options
    ambulance_capability_order.forEach(function (capability) {

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
    
    // add hospital
    $("#location-type").append(
        '<div class="form-group form-check mt-0 mb-1">\n' +
        '     <input class="form-check-input filter-checkbox" value="location" data-status="hospital"\n' +
        '            type="checkbox" id="location-hospital" ' + (visibleCategory['hospital'] ? 'checked' : '') + '>\n' +
        '     <label class="form-check-label"\n' +
        '            for="location-hospital">Hospital</label>\n' +
        '</div>');

    location_type_order.forEach(function (type) {
        $("#location-type").append(
            '<div class="form-group form-check mt-0 mb-1">\n' +
            '     <input class="form-check-input filter-checkbox" value="location" data-status="' + type + '"\n' +
            '            type="checkbox" id="location-' + type + '" ' + (visibleCategory[type] ? 'checked' : '') + '>\n' +
            '     <label class="form-check-label"\n' +
            '            for="location-' + type + '">' + location_type[type] + '</label>\n' +
            '</div>');
    });

    // Add listener to remove or add layer when filter checkbox is clicked
    $('.filter-checkbox')
        .click(function (event) {

            // Stop propagation to avoid collapse
            event.stopPropagation();

        })
        .change(function () { visibilityCheckbox(this); } );

}

function visibilityCheckbox(checkbox) {

    // Which layer?
    let layer = checkbox.getAttribute('data-status');

    // special prefix for calls =
    if (checkbox.value === 'call-status')
        layer = 'call_' + layer;

    // Display or hide?
    let display;
    if (checkbox.checked) {
        display = 'block';
        visibleCategory[layer] = true;
    } else {
        display = 'none';
        visibleCategory[layer] = false;
    }

    // Modify panes
    if (checkbox.value === 'status') {
        // Add to all visible capability panes
        ambulance_capability_order.forEach(function (capability) {
            if (visibleCategory[capability]) {
                mymap.getPane(layer+"|"+capability).style.display = display;
            }
        });
    } else if (checkbox.value === 'capability') {
        // Add to all visible status layers
        ambulance_status_order.forEach(function (status) {
            if (visibleCategory[status]) {
                mymap.getPane(status+"|"+layer).style.display = display;
            }
        });
    } else if (checkbox.value === 'call-status') {
        // Add to all visible call layers
        let status = checkbox.getAttribute('data-status');
        const checked = checkbox.checked;
        for (const key in calls) {
            if (calls.hasOwnProperty(key)) {
                const call = calls[key];
                if (call.status === status) {

                    // change pane visibility
                    mymap.getPane(status + "|" + 'call_' + call.id).style.display = display;

                    // check/uncheck call checkbox
                    $('#call-checkbox-' + call.id)
                        .prop('checked', checked);

                }
            }
        }
    } else {
        mymap.getPane(layer).style.display = display;
    }

}

function onGridAmbulanceButtonClick(ambulance) {

    if (visibleCategory[ambulance.status]) {

        // Center icon on map
        const position = ambulanceMarkers[ambulance.id].getLatLng();
        mymap.setView(position, mymap.getZoom());

        // Open popup for 2.5 seconds.
        ambulanceMarkers[ambulance.id].openPopup();
        setTimeout(function () {
            ambulanceMarkers[ambulance.id].closePopup();
        }, 2500);

    }

}

function onCallButtonClick(call) {

    if (visibleCategory[call.status + '|call_' + call.id] === true) {

        // calculate center of next waypoints
        let center = {lon: 0., lat: 0.};
        let n = 0;
        for (const ambulance_call of call.ambulancecall_set) {

            const nextWaypoint = ambulance_call['next_waypoint'];
            if (nextWaypoint != null) {
                const location = nextWaypoint.location;
                center.lon += location.location.longitude;
                center.lat += location.location.latitude;
                n++;
            }

        }

        // center map
        if (n > 0) {
            center.lon /= n;
            center.lat /= n;
            mymap.setView(center, mymap.getZoom());
        }

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
    bsdialog('Do you want to modify ambulance <strong>'
        + ambulance.identifier
        + '</strong> status to <strong>'
        + ambulance_status[status]
        + '</strong>?', 'alert-danger', 'Attention')
        .on('hide.bs.modal', function(event) {

            const $activeElement = $(document.activeElement);

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
    const form = {status: status};

    // make json call
    const postJsonUrl = APIBaseUrl + 'ambulance/' + ambulance.id + '/';

    const CSRFToken = Cookies.get('csrftoken');

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

            bsalert("Could not update ambulance status \"" +
                textStatus + "," + errorThrown + "\"\n" +
                "You likely have not enough rights to update this ambulance.");


        }
    });

}

// Dispatching

function submitDispatching() {

    // submit form
    $('#dispatch-form-collapse').submit();

};

function beginDispatching() {

    isDispatching = true;
    const filtersDiv = $('#filtersDiv');
    isFilterOpen = filtersDiv.hasClass('show');
    console.log('Begin dispatching.');

    $('#dispatchBeginButton').hide();
    $('#dispatchSubmitButton').show();
    $('#dispatchCancelButton').show();

    // open filter and available ambulances
    filtersDiv.addClass('show');
    $('#ambulance_status').addClass('show');
    $('#ambulance_AV').addClass('show');

    // Handle double click
    mymap.doubleClickZoom.disable();
    mymap.on('dblclick', function(e) {
	// update marker location
	updateCurrentMarker(e.latlng);
    });

    // Update current location
    updateCurrentLocation(mymap.getCenter());

    // Update current address
    updateCurrentAddress(currentLocation);

    // Clear current currentPatients
    currentPatients = {};

    // Initialize patient form
    $('#patients').empty();

    // add new patient form entry
    addPatientForm(0);

    // resize size
    resizeMap();

    // center map
    mymap.setView(currentLocation, mymap.getZoom());

}

function endDispatching() {

    isDispatching = false;
    dispatchingAmbulances = {};
    console.log('End dispatching.');

    // remove marker
    markersGroup.clearLayers();

    // unselect priority
    $('#priority-buttons label.btn').removeClass('active');
    $('input:radio[name=priority]').prop('checked', false);

    // clear description
    $('#comment').val('');

    // clear ambulances buttons
    $('#ambulance-selection :button').remove();
    $('#ambulance-selection-message').show();

    // clear patients
    $('#patients').find('.btn-new-patient').off('click');
    $('#patients').empty();

    // show buttons
    $('#dispatchBeginButton').show();
    $('#dispatchSubmitButton').hide();
    $('#dispatchCancelButton').hide();

    // close dispatch panel
    $('#dispatchDiv').removeClass('show');

    if (!isFilterOpen) {
        // close filter panel
        $('#filtersDiv').removeClass('show');
    }

    // remove dblclick handler
    mymap.off('dblclick');
    mymap.doubleClickZoom.enable();

    // invalidate map size
    mymap.invalidateSize();

}

function removeFromDispatchingList(ambulance) {

    // delete from dispatching list
    delete dispatchingAmbulances[ambulance.id];
    numberOfDispatchingAmbulances--;

    // show message if last button
    if (numberOfDispatchingAmbulances == 0)
        $('#ambulance-selection-message').show();

}

function addToDispatchingList(ambulance) {

    // quick return if null or not dispatching
    if (ambulance == null || !isDispatching)
        return;

    // add ambulance to dispatching list
    console.log('Adding ambulance ' + ambulance.identifier + ' to dispatching list');

    // already in?
    if (ambulance.id in dispatchingAmbulances) {
        console.log('Already in dispatching list, skip');
        return;
    }

    // not available?
    if (ambulance.status != STATUS_AVAILABLE) {
        console.log('Ambulance is not available');
        bsalert('Can only dispatch available ambulances!');
        return;
    }

    // hide message if first button
    if (numberOfDispatchingAmbulances == 0)
        $('#ambulance-selection-message').hide();

    // add ambulance to list of dispatching ambulances
    dispatchingAmbulances[ambulance.id] = ambulance;
    numberOfDispatchingAmbulances++;

    // add button to ambulance dispatch grid
    $('#ambulance-selection').append(
        '<button id="dispatch-button-' + ambulance.id + '"'
        + ' value="' + ambulance.id + '"'
        + ' type="button" class="btn btn-sm '+ ambulance_buttons['AV'] + '"'
        + ' style="margin: 2px 2px;"'
        + ' draggable="true">'
        + ambulance.identifier
        + '</button>'
    );
    $('#dispatch-button-' + ambulance.id)
        .on('dragstart', function (e) {
            // on start of drag, copy information and fade button
            this.style.opacity = '0.4';
            e.originalEvent.dataTransfer.setData("text/plain", ambulance.id);
        })
        .on('dragend', function (e) {
            if (e.originalEvent.dataTransfer.dropEffect == 'none') {
                // Remove button if not dropped back
                removeFromDispatchingList(ambulance);
                // Remove button
                $(this).remove();
            } else {
                // Restore opacity if dropped back in
                this.style.opacity = '1.0';
            }
        });
}

function updateCurrentMarker(latlng) {

    // update current location
    updateCurrentLocation(latlng);

    // update address?
    if ($('#update-address').prop('checked'))
        updateCurrentAddress(latlng);

}

function updateCurrentLocation(location) {

    console.log('Setting current location to: ' + location.lat + ', ' + location.lng);

    // set currentLocation
    currentLocation = location;

    // update coordinates on form
    $('#curr-lat').html(currentLocation.lat.toFixed(6));
    $('#curr-lng').html(currentLocation.lng.toFixed(6));

    // remove existing marker
    markersGroup.clearLayers();

    // laydown marker
    const marker = L.marker(location,
        {
            icon: placeIcon,
            draggable: true
        })
        .addTo(markersGroup);
    markersGroup.addTo(mymap);

    // pan to location: kaung and mauricio though it made more sense to not pan
    // mymap.panTo(location);

    // marker can be dragged on the dispatch map
    marker.on('dragend', function(e) {

        // update current marker
        updateCurrentMarker(marker.getLatLng());

    });
}

function updateCurrentAddress(location) {

    const options = {
        types: 'address',
        limit: 1
    };
    geocoder.reverse(location, options,
        function (results, status) {

            if ("success" !== status) {
                bsalert("Could not geocode:\nError " + status + ", " + results['error']);
                return;
            }

        // quick return if found nothing
        if (results.length === 0) {
            console.log('Got nothing from geocode');
            return;
        }

        // parse features into current address
        currentAddress = geocoder.parse_feature(results[0]);

        console.log(
            'Setting currentAddress to:'
            + '\nnumber: ' + currentAddress['number']
            + '\nstreet: ' + currentAddress['street']
            + '\nunit: ' + currentAddress['unit']
            + '\nlocation: ' + currentAddress['location']['latitude']
            + ',' + currentAddress['location']['longitude']
            + '\nneighborhood: ' + currentAddress['neighborhood']
            + '\nzipcode: ' + currentAddress['zipcode']
            + '\ncity: ' + currentAddress['city']
            + '\nstate: ' + currentAddress['state']
            + '\ncountry: ' + currentAddress['country']
        );

        // set input text
        $('#street').val(currentAddress['street_address']);

    });

}

function updateCoordinates() {

    // when the user changes the street address
    const address = $('#street').val();

    // quick return if no address
    if (!address)
        return;

    // otherwise geocode and update
    const options = {
        types: 'address',
        limit: 1,
        autocomplete: 'true'
    };
    geocoder.geocode(address, options,
        function (results, status) {

            if ("success" !== status) {
                bsalert("Could not geocode:\nError " + status + ", " + results['error']);
                return;
            }

            // quick return if found nothing
            if (results.length === 0) {
                console.log('Got nothing from geocode');
                return;
            }

            // parse features into address
            const address = geocoder.parse_feature(results[0]);

            console.log(
                'Setting currentLocation to:'
                + '\nnumber: ' + address['number']
                + '\nstreet: ' + address['street']
                + '\nunit: ' + address['unit']
                + '\nlocation: ' + address['location']['latitude']
                + ',' + address['location']['longitude']
                + '\nneighborhood: ' + address['neighborhood']
                + '\nzipcode: ' + address['zipcode']
                + '\ncity: ' + address['city']
                + '\nstate: ' + address['state']
                + '\ncountry: ' + address['country']
            );

            // set current location
            updateCurrentLocation({
                lat: address['location']['latitude'],
                lng: address['location']['longitude']
            });

        });
}

function dispatchCall() {

    let obj;
    const form = {};

    // call information
    const street_address = $('#street').val().trim();
    form['details'] = $('#comment').val().trim();
    form['priority'] = $('input:radio[name=priority]:checked').val();

    // checks
    if (form["priority"] === undefined) {
        bsalert("Please select the priority level.");
        return;
    }
    if (numberOfDispatchingAmbulances === 0) {
        bsalert("Please dispatch at least one ambulance.");
        return;
    }

    // location information
    const location = {};
    location['type'] = 'i';
    location['location'] = currentAddress['location'];

    // overwrite location
    location['location'] = {'latitude': currentLocation['lat'], 'longitude': currentLocation['lng']};

    // location information
    location['neighborhood'] = currentAddress['neighborhood'];
    location['city'] = currentAddress['city'];
    location['state'] = currentAddress['state'];
    location['country'] = currentAddress['country'];
    location['zipcode'] = currentAddress['zipcode'];

    // Has the user modified the street address?
    if (!(street_address === currentAddress['street_address'])) {

        // parse street location
        const address = geocoder.parse_street_address(street_address, location['country']);

        location['number'] = address['number'];
        location['street'] = address['street'];
        location['unit'] = address['unit'];

    } else {

        location['number'] = currentAddress['number'];
        location['street'] = currentAddress['street'];
        location['unit'] = currentAddress['unit'];

    }

    // Make sure blanks are undefined
    if (location['number'] === "") {
        location['number'] = undefined;
    }

    // incident single waypoint information, for now
    const waypoints = [];
    const waypoint = {};
    waypoint['order'] = 0;
    waypoint['location'] = location;

    // add waypoint
    waypoints.push(waypoint);

    // ambulances
    const ambulances = [];
    for (const id in dispatchingAmbulances) {
        if (dispatchingAmbulances.hasOwnProperty(id))
            ambulances.push({ 'ambulance_id': id, 'waypoint_set': waypoints });
		}
    form['ambulancecall_set'] = ambulances;

    // patients
    const patients = [];
    for (const index in currentPatients)
        if (currentPatients.hasOwnProperty(index)) {
            const patient = currentPatients[index];
            obj = { 'name': patient[0] };
            if (patient[1])
                // add age
                obj['age'] = parseInt(patient[1]);
            patients.push(obj);
        }

    // retrieve last patient
    const lastPatientForm = $('#patients div.form-row:last');
    const lastPatientName = lastPatientForm.find('input[type="text"]').val().trim();
    if (lastPatientName) {
        obj = {'name': lastPatientName};
        const lastPatientAge = lastPatientForm.find('input[type="number"]').val().trim();
        if (lastPatientAge)
            // add age
            obj['age'] = parseInt(lastPatientAge);
        patients.push(obj);
    }

    // add to patient set
    form['patient_set'] = patients;

    // make json call
    const postJsonUrl = APIBaseUrl + 'call/';
    console.log("Form:");
    console.log(form);
    console.log("Will post:");
    console.log(JSON.stringify(form));

    const CSRFToken = Cookies.get('csrftoken');
    console.log('csrftoken = ' + CSRFToken);

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
        type: 'POST',
        dataType: 'json',
        contentType: 'application/json',
        data: JSON.stringify(form),
        success: function () {

            // Log success
            console.log("Succesfully posted new call.");

            // End dispatching
            endDispatching();

        },
        error: function (jqXHR) {

            // Log failure
            console.log("Failed to post new call.");
            console.log(jqXHR.responseText);

            // Show modal
            bsalert(jqXHR.responseText, 'alert-danger', 'Failure');

            // Do not end dispatching to give user chance to make changes
            // endDispatching();

        }
    });
}


// patient functions

function addPatient(index) {

    console.log('Adding patient index ' + index);

    const name = $('#patient-' + index + '-name').val().trim();
    const age = $('#patient-' + index + '-age').val().trim();

    // is name empty?
    if (!name) {
        bsalert('Empty name');
        return;
    }

    // add name
    currentPatients[index] = [name, age];

    // change button symbol
    const symbol = $('#patient-' + index + '-symbol');
    symbol.removeClass('fa-plus');
    symbol.addClass('fa-minus');

    // change button action from add to remove
    $('#patients').find('#patient-' + index + '-button')
        .off('click')
        .on('click', function(e) { removePatient(index); });

    // add new form
    addPatientForm(index + 1);

}

function removePatient(index) {

    console.log('Removing patient index ' + index);

    // remove from storage
    delete currentPatients[index];

    // remove from form
    $('#patients')
        .find('#patient-' + index + '-form')
        .remove();

}

function addPatientForm(index) {

    console.log('Adding patient form ' + index);

    // add new patient form entry
    $('#patients').append(newPatientForm(index, 'fa-plus'));

    // bind addPatient to click
    $('#patients').find('#patient-' + index + '-button')
        .on('click', function(e) { addPatient(index); });

}

function newPatientForm(index, symbol) {

    // console.log('html = "' + html + '"');

    return '<div class="form-row" id="patient-' + index + '-form">' +
        '<div class="col-md-7 pr-0">' +
        '<input id="patient-' + index + '-name" ' +
        'type="text" ' +
        'class="form-control" ' +
        'placeholder="Name">' +
        '</div>' +
        '<div class="col-md-3 px-0">' +
        '<input id="patient-' + index + '-age" ' +
        'type="number" min="0" ' +
        'class="form-control" ' +
        'placeholder="Age">' +
        '</div>' +
        '<div class="col-md-2 pl-0">' +
        '<button class="btn btn-default btn-block btn-new-patient" ' +
        ' type="button" ' +
        ' id="patient-' + index + '-button">' +
        '<span id="patient-' + index + '-symbol" class="fas ' + symbol + '"></span>' +
        '</button>' +
        '</div>' +
        '</div>';

}

// Ready function
$(function() {

    // Add call priority buttons
    call_priority_order.forEach(function(priority){

        $('#priority-buttons')
            .append(
                '<label class="btn btn-outline-' + call_priority_css[priority].class + '">\n' +
                '  <input type="radio" name="priority" autocomplete="off" value="' + priority + '">\n' +
                '  ' + call_priority_css[priority].html + '\n' +
                '</label>\n');

    });

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

    // connect actions to inputs
    $("#street").change(function () {

        // update coordinates?
        if ($('#update-coordinates').prop('checked'))
            updateCoordinates();

    });


    $('#update-coordinates').change(function () {

        // update coordinates?
        if ($('#update-coordinates').prop('checked'))
            updateCoordinates();

    });

    $('#update-address').change(function () {

        // update address?
        if ($('#update-address').prop('checked'))
            updateCurrentAddress(currentLocation);

    });

    $('#dispatch-form-collapse').submit(function (e) {

        // prevent normal form submission
        e.preventDefault();

        // dispatch call
        dispatchCall();

    });

});

// CSRF functions
function CSRFSafeMethod(method) {
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
