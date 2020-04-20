import L from "leaflet";
import "leaflet-rotatedmarker";
import "leaflet/dist/leaflet.css";

import { Settings } from "./settings";

import { LeafletWidget } from "./leaflet/LeafletWidget";

import { GeocoderFactory } from "./geocoder";

import { logger } from './logger';

import { waypointIcon } from './app-icons';

import { alert } from './alert';

import { Patients } from './components/patients';

import { Select } from './components/select';

import { Waypoints } from './components/waypoints';

import { Dialog } from "./components/dialog";

const sprintf = require('sprintf-js').sprintf;

// Initialize settings
const settings = new Settings(html_settings);
console.log(settings);

// Remove waypoints and incidents from location_type
const reduced_location_type_order = [...settings.location_type_order];
delete reduced_location_type_order[reduced_location_type_order.indexOf('w')];
delete reduced_location_type_order[reduced_location_type_order.indexOf('i')];

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
const hospitals = {};	      // Store hospital details

const locationMarkers = {};   // Store location markers

const calls = {};             // Store call details
const patientMarkers = {};    // Store hospital markers

// Dialog
const dialog = new Dialog({label: "messages"});

// Initialize category panes
let visibleCategory = {};

// Initialize ambulance icons
const ambulance_icons = {};
const ambulance_buttons = {};

for (const [key, value] of Object.entries(settings.ambulance_css)) {
    ambulance_icons[key] = L.icon(value['icon']);
    ambulance_buttons[key] = 'btn-' + value['class'];
}

// Initialize ambulance call status
const ambulance_call_buttons = {
    R: 'btn-danger', // 'Requested'
    A: 'btn-success', // 'Accepted'
    D: 'btn-secondary', // 'Declined'
    S: 'btn-primary', // 'Suspended'
    C: 'btn-dark' // 'Completed'
};

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

const locationIcon = L.icon({
    iconUrl: '/static/icons/maki/marker-15.svg',
    iconSize: [15, 15],
    iconAnchor: [7, 15],
    popupAnchor: [0, -15]

});

const notifications = {
    'ambulance-status': { enabled: true, style: 'success' },
    'ambulance-online': { enabled: true, style: 'warning' }
};

let priority_classification = {};
let priority_code = {};
let radio_code = {};

/**
 * Ambulance statuses
 */
const STATUS_AVAILABLE = "AV";

/**
 * This is a handler for when the page is loaded.
 */
let mymap;
let apiClient;
const geocoder = GeocoderFactory(mapProvider);
settings.geocoder = geocoder;

// resize map
function resizeMap() {
    $("#live-map").height($(window).height() - $('#base-navbar').outerHeight() - $('#map-navbar').outerHeight() - 5);
    mymap.invalidateSize();
}

// add initialization hook
add_init_function(init);

// initialization function
function init( client ) {

    logger.log('info', '> map.js');

    // set apiClient
    apiClient = client;

    // retrieve priority classification
    logger.log('info', 'Retrieving priority classification');
    apiClient.getCallPriorityClassification()
        .then( (value) => {
            logger.log('info', '%d priority classifications retrieved', Object.keys(value).length);
            priority_classification = value;
        })
        .catch( (error) => {
            logger.log('error', 'Failed to retrieve priority classification from ApiClient: %j', error);
        })
        .then( () => {

            if (Object.keys(priority_classification).length > 0) {
                logger.log('info', 'Will disable priority buttons');
                // Disable button clicking
                $('#priority-buttons').on("click", ".btn", function (event) {
                    event.preventDefault();
                    return false;
                });
            }

            // retrieve priority code
            logger.log('info', 'Retrieving priority code');
            return apiClient.getCallPriorityCode();
        })
        .then( (value) => {

            logger.log('info', '%d priority codes retrieved', Object.keys(value).length);
            priority_code = value;

            // retrieve radio code
            logger.log('info', 'Retrieving radio code');
            return apiClient.getCallRadioCode();
        })
        .then( (value) => {
            logger.log('info', '%d radio codes retrieved', Object.keys(value).length);
            radio_code = value;
        })
        .catch( (error) => {
            logger.log('error', 'Failed to retrieve priority and radio codes from ApiClient: %j', error);
        })
        .then( () => {

            // setup ambulances
            setupAmbulances();

            // signup for ambulance updates
            logger.log('info', 'Signing up for ambulance updates');
            apiClient.observe('ambulance/+/data', (message) => { updateAmbulance(message.payload) } );

            // signup for ambulance call status updates
            logger.log('info', 'Signing up for ambulance call status updates');
            apiClient.observe('ambulance/+/call/+/status', (message) => {
                const topics = message.topic.split('/');
                const ambulance_id = topics[1];
                const call_id = topics[3];
                updateAmbulanceCall(ambulance_id, call_id, message.payload);
            });

            // setup calls
            setupCalls();

            // signup for call updates
            logger.log('info', 'Signing up for call updates');
            apiClient.observe('call/+/data', (message) => { updateCall(message.payload) } );

        });


    // Retrieve hospitals
    logger.log('info', 'Retrieving hospitals');
    apiClient.getHospitals()
        .then( (hospitals) => {
            logger.log('info', '%d hospitals retrieved', Object.keys(hospitals).length);

            // setup hospitals
            setupHospitals();

            // signup for hospital updates
            logger.log('info', 'Signing up for hospital updates');
            apiClient.observe('hospital/+/data', (message) => { updateHospital(message.payload) } );

            logger.log('info', 'Retrieving bases');
            return apiClient.getLocations('b');
        })
        .then( (bases) => {
            logger.log('info', '%d bases retrieved', Object.keys(bases).length);

            // Setup bases
            setupLocations(apiClient.locations['b'], 'base');

            logger.log('info', 'Retrieving other locations');
            return apiClient.getLocations('o');
        })
        .then( (locations) => {
            logger.log('info', "%d locations of type 'other' retrieved", Object.keys(locations).length);

            // Setup other locations
            setupLocations(apiClient.locations['o'], 'other');
        })
        .catch( (error) => {
            logger.log('error', 'Failed to retrieve hospitals, bases, and other locations from ApiClient: %j', error);
        });

    // save visibleCategory when unloading
    logger.log('info', 'Setting up beforeunload method');
    $( window ).on( 'beforeunload', saveToLocalStorage );

}

function setupAmbulances() {

    // Retrieve ambulances from ApiClient
    logger.log('info', "Setup ambulances");

    // Update ambulances
    let n = 0;
    let lat = 0;
    let lon = 0;
    Object.entries(apiClient.ambulances).forEach((entry) => {
        const ambulance = entry[1];
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
        logger.log('info', 'Center at lat = %f, lon = %f', lat, lon);

        mymap.setView([lat, lon], 12);
    }

}

function setupCalls() {

    // Retrieve calls from ApiClient
    logger.log('info', "Setup calls");

    Object.entries(apiClient.calls).forEach( (entry) => {
        const call = entry[1];
        updateCall(call);
    });

}

function setupHospitals() {

    // Retrieve hospitals from ApiClient
    logger.log('info', "Setup hospitals");

    // Update hospitals
    Object.entries(apiClient.hospitals).forEach((entry) => {
        const hospital = entry[1];
        updateHospital(hospital);
    });

}

function setupLocations(locations, type) {

    // Retrieve locations from ApiClient
    logger.log('info', "Setup locations of type '" + type + "'");

    Object.entries(locations).forEach((entry) => {
        addLocationToMap(entry[1]);
    });

}

function updateAmbulance(ambulance) {

    // retrieve id
    const id = ambulance.id;

    // already exists?
    if (id in ambulances) {

        // get ambulance's old status
        const old_status = ambulances[id].status;
        const status = ambulance.status;

        const old_online = (ambulances[id].client_id != null);
        const online = (ambulance.client_id != null);

        // Remove existing marker
        mymap.removeLayer(ambulanceMarkers[id]);

        // update ambulance
        ambulances[id].status = status;
        ambulances[id].capability = ambulance.capability;
        ambulances[id].location.latitude = ambulance.location.latitude;
        ambulances[id].location.longitude = ambulance.location.longitude;
        ambulances[id].orientation = ambulance.orientation;
        ambulances[id].client_id = ambulance.client_id;

        // Overwrite ambulance
        ambulance = ambulances[id];

        if (old_status !== status) {

            // Move and update grid button
            const btnClass = 'btn btn-sm ' + ambulance_buttons[status]
                + ' ' + ambulanceVisibleClass(ambulance);
            $("#grid-button-" + id).attr("class", btnClass)
                .detach()
                .appendTo($('#ambulance-grid-' + status));

            // update count labels
            updateStatusHeaderCount(old_status);
            updateStatusHeaderCount(status);

            // alert
            if ( notifications['ambulance-status'].enabled )
                alert(sprintf(settings.translation_table["'%s' is now '%s'"],
                              ambulance.identifier, settings.ambulance_status[ambulance.status]),
                    notifications['ambulance-status'].style );

        } else if (old_online !== online) {

            $("#grid-button-" + id).removeClass('d-none d-block').addClass(ambulanceVisibleClass(ambulance));
            updateStatusHeaderCount(status);

            if ( notifications['ambulance-online'].enabled )
                alert(sprintf(settings.translation_table["'%s' is now '%s'"],
                              ambulance.identifier, online ? 'online' : 'offline'),
                    notifications['ambulance-online'].style );

        }

    } else {

        // Add ambulance to grid
        addAmbulanceToGrid(ambulance);

    }

    // add ambulance to map
    addAmbulanceToMap(ambulance);

}

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
    const location = hospital;
    location.type = 'h';
    addLocationToMap(location);

}

function ambulanceVisibleClass(ambulance) {
    const online = ambulance.client_id != null ? 'online' : 'offline';
    const classNames = ['status-' + ambulance.status, 'capability-' + ambulance.capability, 'service-' + online];
    if (visibleCategory[online] && visibleCategory[ambulance.status] && visibleCategory[ambulance.capability])
        classNames.push('d-block');
    else
        classNames.push('d-none');
    return classNames.join(' ');
}


function addAmbulanceToGrid(ambulance) {

    logger.log('info', "Adding ambulance '%s' [id:'%d', status:'%s', btn='%s'] to grid", 
        ambulance.identifier, ambulance.id, ambulance.status, ambulance_buttons[ambulance.status]);

    // make grid visible
    if (ambulance.status === 'AV')
        $('#ambulance-' + ambulance.status).addClass('show');

    // Add button to ambulance grid
    $('#ambulance-grid-' + ambulance.status)
        .append('<button type="button"'
            + ' id="grid-button-' + ambulance.id + '"'
            + ' class="btn btn-sm ' + ambulance_buttons[ambulance.status]
            + ' ' + ambulanceVisibleClass(ambulance) + '"'
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
    updateStatusHeaderCount(ambulance.status);

}

function updateCall(call) {

    // retrieve id
    const id = call.id;
    const status = call.status;

    // already exists?
    if (id in calls) {

        // retrieve old status
        const matches = $('#call-item-' + id)
            .attr('class')
            .match(/status-(\w)/);
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

                // remove old visible category
                delete visibleCategory[old_status + "|" + 'call_' + id];

                // status changed
                if (status !== 'E') {

                    // move to new category
                    $('#call-item-' + id)
                        .detach()
                        .appendTo($('#call-grid-' + status));

                } else { // status == 'E'

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

            // update date
            $('#call-date-' + call.id).html( date );

            // update patients
            setCallPatientPopover(call.id, call.patient_set, true);

            // Update waypoints
            if (status === 'E') {

                // remove waypoints
                call.ambulancecall_set.forEach(function (ambulance_call) {

                    // Remove waypoints
                    removeWaypoints(call.id, ambulance_call.ambulance_id);

                });

            } else {

                // update waypoints
                for (const ambulance_call of call.ambulancecall_set) {

                    // Remove waypoints
                    removeWaypoints(call.id, ambulance_call.ambulance_id);

                    // add waypoints
                    let nextWaypoint = addWaypoints(call, ambulance_call.ambulance_id,
                        ambulance_call['waypoint_set'], date);

                    // set next waypoint
                    ambulance_call['next_waypoint'] = nextWaypoint;

                    // update progress bar
                    updateCallProgress(call, ambulance_call);

                }

            }

        } else
            logger.log('error', 'Could not match current call status');

    } else {

        // add call to grid
        addCallToGrid(call);

        // add call to map
        addCallToMap(call);
        
    }

}

function updateAmbulanceCall(ambulance_id, call_id, status) {

    if (status !== 'C') {

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

        }

    }
}

function updateCallCounter() {

    let total = 0;
    settings.call_status_order.forEach(function(status) {
        if (status !== 'E') {
            const count = $('#call-grid-' + status).children().length;
            total += count;
            if (count > 0)
                $('#call-' + status + '-header-count').html(count).show();
            else
                $('#call-' + status + '-header-count').hide();
        }
    });

    if (total > 0)
        $('#call-header-count').html(total).show();
    else
        $('#call-header-count').hide();

}

const waypointProgressColor = {
    'D': 'bg-success',
    'S': 'bg-secondary',
    'V': 'bg-warning',
    'C': 'bg-light'
};

function updateCallProgress(call, ambulance_call) {

    // get ambulance
    const ambulance = ambulances[ambulance_call.ambulance_id];

    const progress_bar = $('#call-progress-bar-' + call.id + '-' + ambulance.id);
    progress_bar.empty();

    // waypoints
    const waypoint_set = ambulance_call['waypoint_set'];

    if (waypoint_set.length > 0) {

        // sort waypoints
        waypoint_set.sort(function (a, b) {
            return (a.order - b.order);
        });

        const value = 100 / waypoint_set.length;
        let nextWaypoint = null;
        waypoint_set.forEach((waypoint) => {

            // set color
            let color = waypointProgressColor[waypoint.status];

            // is it next?
            if ((waypoint.status === 'C' || waypoint.status === 'V') && nextWaypoint === null) {
                nextWaypoint = waypoint;
                if (waypoint.status === 'C')
                    color = 'bg-primary';
                color = 'progress-bar-animated ' + color;
            }

            progress_bar.append(
                '<div class="progress-bar progress-bar-striped ' + color + '"'
                + '         role="progressbar" style="width: ' + value + '%"'
                + '         aria-valuenow="' + value + '" aria-valuemin="0" aria-valuemax="100">'
                + '</div>'
            );

        });
    }
}

function abortCall(call) {

    dialog.dialog(
        sprintf(settings.translation_table["Do you want to abort call %d?"], call.id),
        (retval) => {

            if (retval === Dialog.OK) {

                // Abort call
                apiClient.abortCall(call)
                    .then( (call) => {
                        logger.log('info', 'call %d successfully aborted', call.id);
                    })
                    .catch( (error) => {
                        logger.log('error', 'Failed to abort call %d: %j', call.id, error);
                    });

            }
        }
    );
}

function setCallWaypointPopover(call_id, ambulance_id, waypoint_set, destroy = false) {

    // create waypoint object
    const placeholder = 'call-' + call_id + '-' + ambulance_id + '-waypoints';
    const buttons_placeholder = 'call-' + call_id + '-' + ambulance_id + '-waypoints-buttons';
    const selector = $('#call-' + call_id + '-' + ambulance_id + '-waypoints-button');

    // destroy?
    if (destroy)
        selector.popover('dispose');

    // Add popover to waypoint button
    selector
        .popover({
            title: settings.translation_table['Waypoints'],
            // language=HTML
            content:
            `<div>  
    <div id="${placeholder}">
    </div>
    <div id="${buttons_placeholder}" class="btn-group d-flex">
    </div>
</div>`,
            html: true,
            placement: 'left',
            trigger: 'manual',
            container: 'body',
            template: `<div class="popover popover-large" role="tooltip">
    <div class="arrow"></div>
    <h3 class="popover-header"></h3>
    <div class="popover-body"></div>
</div>`
        })
        .on('click', function(e) {
            $(this).popover('show');
            e.stopPropagation();
        })
        .on('inserted.bs.popover', () => {

            // create waypoint form
            const waypoint_set_clone = JSON.parse(JSON.stringify(waypoint_set));
            console.log(waypoint_set_clone);

            const waypoints = new Waypoints(waypoint_set_clone, call_id + '-' + ambulance_id, '#' + placeholder);
            const waypointsString = JSON.stringify(waypoints.getData());

            waypoints.render();
            waypoints.postRender();

            // add buttons
            $(`#${buttons_placeholder}`)
                .html(`
        <button id="call-${call_id}-${ambulance_id}-waypoints-cancel-button" 
                type="button" 
                class="btn btn-secondary w-100">
            ${settings.translation_table["Cancel"]}    
        </button>
        <button id="call-${call_id}-${ambulance_id}-waypoints-save-button" 
                type="button" 
                class="btn btn-primary w-100">
            ${settings.translation_table["Save"]}
        </button>`);

            // toggle on cancel
            $('#call-' + call_id + '-' + ambulance_id + '-waypoints-cancel-button')
                .on('click', function (event) {

                    $('#call-' + call_id + '-' + ambulance_id + '-waypoints-button')
                        .popover('toggle');
                    event.stopPropagation();

                });

            // toggle on save
            $('#call-' + call_id + '-' + ambulance_id + '-waypoints-save-button')
                .on('click', function (event) {

                    // retrieve waypoints
                    const newWaypoints = waypoints.getData();
                    const newWaypointsString = JSON.stringify(newWaypoints);

                    console.log(newWaypoints);
                    console.log(waypointsString);
                    console.log(newWaypointsString);

                    if ( waypointsString === newWaypointsString ) {

                        // no changes
                        logger.log('info', 'No changes, no savings!');

                        $('#call-' + call_id + '-' + ambulance_id + '-waypoints-button')
                            .popover('toggle');
                        event.stopPropagation();

                    } else {

                        dialog.dialog(
                            settings.translation_table["Do you want to save the modified waypoints?"],
                            (retval) => {

                                if (retval === Dialog.OK) {

                                    for (const waypoint of newWaypoints) {

                                        if (waypoint.id === null) {

                                            // new waypoint
                                            logger.log('info', 'New waypoint, post');

                                            apiClient.postWaypoint(call_id, ambulance_id, waypoint)
                                                .then((waypoint) => {
                                                    logger.log('info', "Successfully created waypointg");
                                                })
                                                .catch((error) => {
                                                    logger.log('error', "Could not create waypoint: '%j'", error);
                                                });

                                        } else {

                                            // existing waypoint
                                            logger.log('info', 'Existing waypoint, patch');

                                            apiClient.patchWaypoint(call_id, ambulance_id, waypoint.id, waypoint)
                                                .then((waypoint) => {
                                                    logger.log('info', "Successfully updated waypoint");
                                                })
                                                .catch((error) => {
                                                    logger.log('error', "Could not update waypoint: '%j'", error);
                                                });

                                        }
                                    }
                                }

                                $('#call-' + call_id + '-' + ambulance_id + '-waypoints-button')
                                    .popover('toggle');
                                event.stopPropagation();

                            });

                    }

                });

        });
}

function setCallPatientPopover(call_id, patient_set, destroy = false) {

    // create patient object
    const placeholder = 'call-' + call_id + '-patients';
    const buttons_placeholder = 'call-' + call_id + '-patients-buttons';
    const patients = new Patients(patient_set, call_id, '#' + placeholder);
    const selector = $('#call-' + call_id + '-patients-button');

    // destroy?
    if (destroy)
        selector.popover('dispose');

    // Add popover to patient button
    selector
        .popover({
            title: settings.translation_table['Patients'],
            // language=HTML
            content:
            `<div>  
    <div id="${placeholder}">
    </div>
    <div id="${buttons_placeholder}" class="float-right my-2">
    </div>
</div>`,
            html: true,
            placement: 'left',
            trigger: 'manual'
        })
        .on('click', function(e) {
            $(this).popover('show');
            e.stopPropagation();
        })
        .on('inserted.bs.popover', () => {

            // create patient form
            patients.render();

            // add buttons
            $(`#${buttons_placeholder}`)
                .html(`
<button id="call-${call_id}-patients-cancel-button" type="button" class="btn btn-secondary">
    ${settings.translation_table["Cancel"]}
</button>
<button id="call-${call_id}-patients-save-button" type="button" class="btn btn-primary">
    ${settings.translation_table["Save"]}
</button>`);

            // toggle on cancel
            $('#call-' + call_id + '-patients-cancel-button')
                .on('click', function (event) {

                    $('#call-' + call_id + '-patients-button')
                        .popover('toggle');
                    event.stopPropagation();

                });

            // toggle on save
            $('#call-' + call_id + '-patients-save-button')
                .on('click', function (event) {

                    // retrieve patients
                    const newPatients = patients.getData();
                    console.log(newPatients);
                    console.log(patient_set);
                    if ( patients.same(newPatients) ) {

                        // no changes
                        logger.log('info', 'No changes, no savings!');

                        $('#call-' + call_id + '-patients-button')
                            .popover('toggle');
                        event.stopPropagation();

                    } else {


                        dialog.dialog(
                            settings.translation_table["Do you want to save the modified patients?"],
                            (retval) => {

                                if (retval === Dialog.OK) {

                                    // update call
                                    const data = { patient_set: newPatients };
                                    apiClient.patchCall(call_id, data)
                                        .then( (call) => {
                                            logger.log('info', "Successfully updated call");
                                        })
                                        .catch( (error) => {
                                            logger.log('error', "Could not update call: '%j'", error);
                                        });

                                }

                                $('#call-' + call_id + '-patients-button')
                                    .popover('toggle');
                                event.stopPropagation();

                            });

                    }

                });

        });

}

function addCallToGrid(call) {

    logger.log('info', "Adding call '%d'[status:'%s'] to grid", call.id, call.status);

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

    // set priority
    let priority_prefix = '';
    let priority_suffix = '';
    if (call.priority_code != null) {
        const priority = priority_code[call.priority_code];
        priority_prefix = priority.prefix;
        priority_suffix = priority.suffix;
    }

    // Add item to call grid
    // language=HTML
    $('#call-grid-' + status)
        .append(
            `<div class="card status-${status}" id="call-item-${call.id}">
  <div class="card-header px-1 py-1" id="call-${call.id}">
    <div class="d-flex">      
        <div>
            <input class="filter-checkbox" value="call" data-status="${status}|call_${call.id}"
                   type="checkbox" id="call-checkbox-${call.id}" 
                   ${visibleCategory[status + "|" + 'call_' + call.id] ? 'checked' : ''}>
        </div>
        <div data-toggle="collapse"
             data-target="#call-${call.id}-body"
             aria-expanded="true" aria-controls="call-${call.id}-body">        
            <span class="ml-1">${call.id}:</span>        
            <span class="font-weight-bold">${priority_prefix}</span>        
            <button id="call-${call.id}-button"
                    class="btn btn-${settings.call_priority_css[call.priority].class} btn-sm">           
                ${settings.call_priority_css[call.priority].html}
            </button>
            <span class="font-weight-bold">${priority_suffix}</span>
        </div>
        <div>
            <span id="call-details-${call.id}">${call.details}</span>
        </div>
        <div class="ml-auto" data-toggle="collapse"
             data-target="#call-${call.id}-body"
             aria-expanded="true" aria-controls="call-${call.id}-body">
            <span id="call-date-${call.id}">${date}</span>        
            <button id="call-${call.id}-patients-button"                 
                    type="button" class="btn btn-outline-dark btn-sm" aria-label="Patients">
                <span class="fas fa-user fa-sm"></span> 
            </button>
            <button id="call-${call.id}-info-button"                 
                    type="button" class="btn btn-outline-dark btn-sm" aria-label="Info">
                <span class="fas fa-info-circle fa-sm"></span> 
            </button>
        </div>
        <div>
            <button id="call-${call.id}-abort" type="button" class="close ml-1" aria-label="Close">
                <span aria-hidden="true">&times;</span>
            </button>
        </div>    
    </div>  
  </div>
    <div class="collapse"
         id="call-${call.id}-body"
         aria-labelledby="call-${call.id}">
        <div class="card-body px-1 py-1" id="call-item-grid-${call.id}">
        </div>
    </div>
</div>`);

    // Make call button clickable
    $('#call-' + call.id + '-button')
        .click(function (e) {
            onCallButtonClick(call);
        });

    // Make call abort button clickable
    $('#call-' + call.id + '-abort')
        .click(function (e) {
            abortCall(call);
        });

    // set call patient popover
    setCallPatientPopover(call.id, call.patient_set);

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
            .append(
                `<div class="row no-gutters" style="display:flex; align-items:center;">  
    <div class="col-sm-4">   
        <button type="button"        
                id="call-grid-button-${call.id}-${ambulance.id}"
                class="btn btn-sm ${ambulance_call_buttons[ambulance_call.status]} status-${ambulance_call.status}" 
                style="margin: 2px 2px;" 
                draggable="true">
            ${ambulance.identifier}
        </button>  
    </div> 
    <div class="col-sm-6"> 
        <div id="call-progress-bar-${call.id}-${ambulance.id}"   
             class="progress mr-1" style="height: 20px;">
        </div>  
    </div>  
    <div class="col-sm-1"> 
        <button type="button" 
                id="call-${call.id}-${ambulance.id}-waypoints-button" 
                class="btn btn-outline-dark btn-sm" aria-label="Waypoints">  
            <span class="fas fa-map-marker fa-sm"></span>  
        </button>
    </div> 
    <div class="col-sm-1">  
        <button type="button" class="close" aria-label="Close">
            <span aria-hidden="true">&times;</span>
        </button>
    </div>
</div>`
            );

        // Make button clickable and draggable
        $('#call-grid-button-' + call.id + '-'+ ambulance.id)
            .click(function (e) {
                onGridAmbulanceButtonClick(ambulance);
            });

        // set waypoint popover
        setCallWaypointPopover(call.id, ambulance.id, ambulance_call.waypoint_set);

        // update progress bar
        updateCallProgress(call, ambulance_call);

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
        address_str += location.neighborhood.trim();

    if (address_str !== "")
        address_str = [address_str, location.city, location.state].join(', ').trim();
    else
        address_str = [location.city, location.state].join(', ').trim();

    address_str = [address_str, location.zipcode].join(' ').trim();
    address_str = [address_str, location.country].join(', ').trim();

    // language=HTML
    return (
        `<div>
    <p class="my-0 py-0">
        <em>Address:</em>
    </p>
    <p class="my-0 py-0">
        <span class="text-right">${address_str}</span>
    </p>
    <p class="my-0 py-0">
        <em>Type:</em>
        <span class="float-right">${settings.location_type[location.type]}</span>
    </p>
</div>`
    );

}

function callToHtml(call, date, number_of_waypoints, waypoint) {

    // language=HTML
    return (
        `<div>
    <p class="my-0 py-0">
        <strong>Priority:</strong>
        <span class="float-right">${call.priority}</span>
    </p>
    <p class="my-0 py-0">
        <strong>Date:</strong>
        <span class="float-right">${date}</span>
    </p>
    <p class="my-0 py-0">
        <strong>Details:</strong>
        <span class="float-right">${call.details}</span>
    </p>
    <p class="my-0 py-0">
        <strong>Patients:</strong>
        <span class="float-right">${compilePatients(call)}</span>
    </p>
    <p class="my-0 py-0">
        <strong>Number of waypoints:</strong>
        <span class="float-right">${number_of_waypoints}</span>
    </p>
    <p class="my-0 py-0">
        <strong>Next waypoint:</strong>
    </p>
    ${locationToHtml(waypoint.location)}
</div>`
    );
}

function addWaypoints(call, ambulance_id, waypoint_set, date) {

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
        const icon = new L.divIcon(waypointIcon(waypoint));

        // is it next?
        if ((waypoint.status === 'C' || waypoint.status === 'V') && nextWaypoint === null)
            nextWaypoint = waypoint;

        // create marker
        let marker = L.marker(
            [location.location.latitude, location.location.longitude],
            {
                icon: icon,
                pane: call.status + "|" + 'call_' + call.id
            });

        // Add popup to the incident location
        if (waypoint === nextWaypoint) {

            // bind popup to next waypoint
            marker.bindPopup( callToHtml(call, date, waypoint_set.length, waypoint) );

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
        patients = settings.translation_table["No patient names are available."];
    } else
        patients = call.patient_set.join(', ');

    return patients;
}

function addCallToMap(call) {

    // Get relevant date
    let date = callDate(call);

    // Add incident locations
    call.ambulancecall_set.forEach(function (ambulance_call) {

        // add waypoints
        const nextWaypoint = addWaypoints(call, ambulance_call.ambulance_id,
            ambulance_call['waypoint_set'], date);

        // set next waypoint
        ambulance_call['next_waypoint'] = nextWaypoint;

    });

}

function addAmbulanceToMap(ambulance) {

    logger.log('info', "Adding ambulance '%s [id:%d, latlon:%f,%f] to map",
        ambulance.identifier, ambulance.id, ambulance.location.latitude, ambulance.location.longitude);

    // store ambulance details in an array
    ambulances[ambulance.id] = ambulance;
    const online = (ambulance.client_id == null ? 'offline' : 'online');

    // Add marker
    // logger.log('debug', 'orientation = ' + ambulance.orientation);
    ambulanceMarkers[ambulance.id] = L.marker(
        [ambulance.location.latitude,
            ambulance.location.longitude],
        {
            icon: ambulance_icons[ambulance.status],
            rotationAngle: ambulance.orientation % 360,
            rotationOrigin: 'center center',
            pane: ambulance.status + "|" + ambulance.capability + "|" + online
        })
        .bindPopup(
            "<strong>" + ambulance.identifier + "</strong>" +
            "<br/>" +
            settings.ambulance_status[ambulance.status] +
            "<br/>" +
            settings.ambulance_capability[ambulance.capability] +
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

}

function addLocationToMap(location) {

    logger.log('info', "Adding location '%s'[id:'%d, latlon:%f,%f] to map",
        location.name, location.id, location.location.latitude, location.location.longitude);

    // store location details in an object, create first if needed
    if (!settings.locations.hasOwnProperty(location.type))
        settings.locations[location.type] = {};

    settings.locations[location.type][location.id] = location;

    // set icon by status
    let icon = locationIcon;
    if (location.type === 'a')
        icon = defibrillatorIcon;
    else if (location.type === 'b')
        icon = baseIcon;
    else if (location.type === 'i')
        icon = incidentIcon;
    else if (location.type === 'h')
        icon = hospitalIcon;

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

}

/* Create category filter */
function createCategoryPanesAndFilters() {

    logger.log('info', 'Setting up category panes and filters');

    // Initialize visibleCategories

    // add status
    settings.ambulance_status_order.forEach(function(status) {
        visibleCategory[status] = true;
    });

    // add capability
    settings.ambulance_capability_order.forEach(function(capability) {
        visibleCategory[capability] = true;
    });

    // add online/offline
    settings.ambulance_online_order.forEach(function(online) {
        visibleCategory[online] = true;
    });

    // add hospital
    // visibleCategory['hospital'] = true;

    // add calls
    settings.call_status_order.forEach(function (status) {
        visibleCategory['call_' + status] = true;
    });

    // add location_type
    reduced_location_type_order.forEach(function(type) {
        visibleCategory[type] = false;
    });

    // load visibleCategory from local storage
    Object.assign(visibleCategory, loadFromLocalStorage( 'visibleCategory' ) );

    // Initialize panes

    // Create location category panes
    reduced_location_type_order.forEach(function (type) {
        const pane = mymap.createPane(type);
        pane.style.display = (visibleCategory[type] ? 'block' : 'none');
    });

    // Create ambulance status category panes
    settings.ambulance_online_order.forEach(function(online) {
        settings.ambulance_status_order.forEach(function (status) {
            settings.ambulance_capability_order.forEach(function (capability) {
                const pane = mymap.createPane(status + "|" + capability + "|" + online);
                pane.style.display = ((visibleCategory[status] &&
                                       visibleCategory[capability] &&
                                       visibleCategory[online]) ? 'block' : 'none');
            });
        });
    });

    // Create call status grids
    settings.call_status_order.forEach(function (status) {

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
                '             <span id="call-' + status + '-header" role="button">' + settings.call_status[status] + '</span>\n' +
                '             <span id="call-' + status + '-header-count" class="badge badge-primary"></span>\n' +
                '          </h6>\n' +
                '    </div>\n' +
                '    <div class="collapse"\n' +
                '         id="call-' + status + '"\n' +
                '         aria-labelledby="call-heading-' + status + '">\n' +
                /* '         data-parent="#call-status">\n' + */
                '         <div class="card-body py-0 px-0"\n' +
                '              id="call-grid-' + status + '">\n' +
                '         </div>\n' +
                '    </div>\n' +
                '</div>');

    });

    // Create online options
    settings.ambulance_online_order.forEach(function (online) {

        $("#ambulance-online-status").append(
            '<div class="d-inline-block form-group form-check mt-0 mb-1 mr-2">\n' +
            '     <input class="form-check-input filter-checkbox" value="online" data-status="' + online + '"\n' +
            '            type="checkbox" id="online-' + online + '" ' +
            (visibleCategory[online] ? 'checked' : '') + '>\n' +
            '     <label class="form-check-label"\n' +
            '            for="online-' + online + '">' + settings.ambulance_online[online] + '</label>\n' +
            '</div>');

    });

    // Create ambulance status grids
    settings.ambulance_status_order.forEach(function (status) {

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
            '                    ' + settings.ambulance_status[status] + '\n' +
            '             </span>\n' +
            '             <span id="ambulance-' + status + '-header-count" class="badge badge-primary"></span>\n' +
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
                logger.log('debug', "dropped ambulance '%s'", ambulance['identifier']);
                // change status
                updateAmbulanceStatus(ambulance, status);
            });

    });

    // Create capability options
    settings.ambulance_capability_order.forEach(function (capability) {

        $("#ambulance-capability").append(
            '<div class="form-group form-check mt-0 mb-1">\n' +
            '     <input class="form-check-input filter-checkbox" value="capability" data-status="' + capability + '"\n' +
            '            type="checkbox" id="capability-' + capability + '" ' +
            (visibleCategory[capability] ? 'checked' : '') + '>\n' +
            '     <label class="form-check-label"\n' +
            '            for="capability-' + capability + '">' + settings.ambulance_capability[capability] + '</label>\n' +
            '</div>');
    });

    // Create location options

    reduced_location_type_order.forEach(function (type) {
        $("#location-type").append(
            '<div class="form-group form-check mt-0 mb-1">\n' +
            '     <input class="form-check-input filter-checkbox" value="location" data-status="' + type + '"\n' +
            '            type="checkbox" id="location-' + type + '" ' + (visibleCategory[type] ? 'checked' : '') + '>\n' +
            '     <label class="form-check-label"\n' +
            '            for="location-' + type + '">' + settings.location_type[type] + '</label>\n' +
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

function updateStatusHeaderCount(status) {
    // Update label
    const count = $('#ambulance-grid-' + status).find('.status-' + status + '.d-block').length;
    if (count > 0)
        $('#ambulance-' + status + '-header-count').html(count).show();
    else
        $('#ambulance-' + status + '-header-count').hide();
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
        settings.ambulance_online_order.forEach(function(online) {
            if (visibleCategory[online]) {
                settings.ambulance_capability_order.forEach(function (capability) {
                    if (visibleCategory[capability]) {
                        mymap.getPane(layer + "|" + capability + "|" + online).style.display = display;
                    }
                });
            }
        });

    } else if (checkbox.value === 'capability') {

        // Add to all visible status layers
        settings.ambulance_online_order.forEach(function(online) {
            if (visibleCategory[online]) {
                settings.ambulance_status_order.forEach(function (status) {
                    if (visibleCategory[status]) {
                        mymap.getPane(status + "|" + layer + "|" + online).style.display = display;

                        // toggle buttons visibility
                        $('.status-' + status + '.capability-' + layer + '.service-' + online)
                            .removeClass('d-block d-none')
                            .addClass('d-' + display);

                    }
                });
            }
        });

        // update status header count
        settings.ambulance_status_order.forEach( (status) => { updateStatusHeaderCount(status); } );

    } else if (checkbox.value === 'online') {
        // Add to all visible status layers
        settings.ambulance_status_order.forEach(function (status) {
            if (visibleCategory[status]) {
                // Add to all visible capability panes
                settings.ambulance_capability_order.forEach(function (capability) {
                    if (visibleCategory[capability]) {
                        mymap.getPane(status + "|" + capability + "|" + layer).style.display = display;

                        // toggle buttons visibility
                        $('.status-' + status + '.capability-' + capability + '.service-' + layer)
                            .removeClass('d-block d-none')
                            .addClass('d-' + display);

                    }
                });
            }
        });

        // update status header count
        settings.ambulance_status_order.forEach( (status) => { updateStatusHeaderCount(status); } );

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

function saveToLocalStorage() {

    logger.log('info', 'Saving state to local storage');

    // save visibleCategory to localStorage
    localStorage.setItem('visibleCategory', JSON.stringify(visibleCategory));

}

function loadFromLocalStorage(key) {

    // load visibleCategory from localStorage
    let value = {};
    if (localStorage.hasOwnProperty(key)) {

        // get the value from localStorage
        value = localStorage.getItem(key);

        // parse the localStorage string and setState
        try {
            // overload visibleCategory
            value =  JSON.parse(value);
            logger.log('info', "> Parsed '" + key + "' from local storage");
        } catch (e) {
            logger.log('error', "> Could not parse '" + key + "' from local storage");
        }
    }
    return value;

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
    if (ambulance.status === status)
        return;

    dialog.dialog(
        sprintf("Do you want to modify ambulance <strong>%s</strong> status to <strong>%s</strong>?",
            ambulance.identifier, settings.ambulance_status[status]),
        (retval) => {

            if (retval === Dialog.OK) {

                // Update status
                doUpdateAmbulanceStatus(ambulance.id, status);

            }
        }
    )

}

function doUpdateAmbulanceStatus(ambulance_id, status) {

    // patch ambulance
    const data = { status: status };
    apiClient.patchAmbulance(ambulance_id, data)
        .then( (ambulance) => {

            logger.log('info', 'Successfully patched ambulance');

            // show target card
            $('#ambulance-' + status)
                .collapse('show');

        })
        .catch( (error) => {

            logger.log('error', 'Failed to patch ambulance: %j', error);

            // modal alert
            dialog.alert(settings.translation_table["Could not update ambulance status"]);

        });
}

// Dispatching

// sms-notifications select element
const select = new Select({
    list: 'sms-notifications-list',
    prefix: 'sms-notifications',
    label: settings.translation_table['Select username']
});

function beginDispatching() {

    // quick return if not dispatching
    if (isDispatching)
        return;

    isDispatching = true;
    const filtersDiv = $('#filtersDiv');
    isFilterOpen = filtersDiv.hasClass('show');
    logger.log('info', 'Begin dispatching.');

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

    // add sms notifications
    select.resetItems();
    $('#sms-notifications')
        .html(select.render());
    select.postRender();

    // resize size
    resizeMap();

    // center map
    mymap.setView(currentLocation, mymap.getZoom());

}

function endDispatching() {

    // quick return if not dispatching
    if (!isDispatching)
        return;

    isDispatching = false;
    dispatchingAmbulances = {};
    logger.log('info', 'End dispatching.');

    // remove marker
    markersGroup.clearLayers();

    // unselect priority
    $('#priority-buttons label.btn').removeClass('active');
    $('input:radio[name=priority]').prop('checked', false);

    // clear priority code
    $('#priority-code-input').val('');
    $('#priority-classification').html('<span class="text-muted">' + settings.translation_table["Priority Classification"] + '</span>');
    $('#priority-code').html('<span class="text-muted">' + settings.translation_table["Priority Code"] + '</span>');
    $("#priority-buttons .btn").removeClass("active");

    // clear radio code
    $('#radio-code-input').val('');
    $('#radio-code').html('<span class="text-muted">' + settings.translation_table["Radio Code"] + '</span>');

    // clear description
    $('#comment').val('');

    // clear ambulances buttons
    $('#ambulance-selection :button').remove();
    $('#ambulance-selection-message').show();

    // clear patients
    $('#patients')
        .find('.btn-new-patient')
        .off('click')
        .empty();

    // clear sms notifications
    $('#sms-notifications').empty();

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
    if (numberOfDispatchingAmbulances === 0)
        $('#ambulance-selection-message').show();

}

function addToDispatchingList(ambulance) {

    // quick return if null or not dispatching
    if (ambulance == null || !isDispatching)
        return;

    // add ambulance to dispatching list
    logger.log('info', "Adding ambulance '%s' to dispatching list",  ambulance.identifier);

    // already in?
    if (ambulance.id in dispatchingAmbulances) {
        logger.log('info', 'Already in dispatching list, skip');
        return;
    }

    // not available?
    if (ambulance.status !== STATUS_AVAILABLE) {
        logger.log('info', 'Ambulance is not available');
        dialog.alert(settings.translation_table["Can only dispatch available ambulances!"]);
        return;
    }

    // hide message if first button
    if (numberOfDispatchingAmbulances === 0)
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
            if (e.originalEvent.dataTransfer.dropEffect === 'none') {
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

    logger.log('info', 'Setting current location to: %f,%f', location.lat, location.lng);

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

    geocoder.reverse(location)
        .then( (address) => {

            logger.log('debug', "address = '%j'", address);

            // parse features into current address
            currentAddress = address;

            // set input text
            $('#street').val(currentAddress['formatted_address']);

        })
        .catch( (error) => {
            logger.log('warn', "Could not forward geocode. Error: '%s'", error);
        });

}

function updateCoordinates() {

    // when the user changes the street address
    const address = $('#street').val();

    // quick return if no address
    if (!address)
        return;

    // otherwise geocode and update
    geocoder.geocode(address)
        .then( (address) => {

            logger.log('debug', "address = '%j'", address);

            // set current location
            updateCurrentLocation({
                lat: address['location']['latitude'],
                lng: address['location']['longitude']
            });

        })
        .catch( (error) => {
            logger.log('warn', "Could not forward geocode. Error: '%s'", error);
        });

}

function dispatchCall() {

    let obj;
    const form = {};

    // disable dispatch button
    $('#dispatchSubmitButton').attr("disabled", true);

    // call information
    const street_address = $('#street').val().trim();
    form['details'] = $('#comment').val().trim();
    form['priority'] = $('input:radio[name=priority]:checked').val();

    form['radio_code'] = null;
    let selector = $('#radio-code-list option[value="' + $('#radio-code-input').val() + '"]');
    if (selector.length) {
        try {
            form['radio_code'] = selector.attr('id').split('-')[2];
        } catch (err) {
            logger.log('debug', err);
            dialog.alert(settings.translation_table["Invalid radio code"]);

            // enable dispatch button
            $('#dispatchSubmitButton').attr("disabled", false);
            return;
        }
    }

    form['priority_code'] = null;
    selector = $('#priority-code-list option[value="' + $('#priority-code-input').val() + '"]');
    if (selector.length) {
        try {
            form['priority_code'] = selector.attr('id').split('-')[2];
        } catch (err) {
            logger.log('debug', err);
            dialog.alert(settings.translation_table["Invalid priority code"]);

            // enable dispatch button
            $('#dispatchSubmitButton').attr("disabled", false);
            return;
        }
    }

    // checks
    if (form["priority"] === undefined) {
        dialog.alert(settings.translation_table["Please select the priority"]);

        // enable dispatch button
        $('#dispatchSubmitButton').attr("disabled", false);
        return;
    }
    if (numberOfDispatchingAmbulances === 0) {
        dialog.alert(settings.translation_table["Please dispatch at least one ambulance"]);

        // enable dispatch button
        $('#dispatchSubmitButton').attr("disabled", false);
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
            ambulances.push({'ambulance_id': id, 'waypoint_set': waypoints});
    }
    form['ambulancecall_set'] = ambulances;

    // patients
    const patients = [];
    for (const index in currentPatients)
        if (currentPatients.hasOwnProperty(index)) {
            const patient = currentPatients[index];
            obj = {'name': patient[0]};
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

    // add sms-notifications
    form['sms_notifications'] = Object.keys(select.getItems());

    // post new call
    apiClient.postCall(form)
        .then( (call) => {

            logger.log('info', 'Successfully posted new call');

            // End dispatching automatically calls endDispatching
            $('#newDispatchDiv').collapse('hide');

            // enable dispatch button
            $('#dispatchSubmitButton').attr("disabled", false);

        })
        .catch( (error) => {

            logger.log('error', 'Failed to post new call: %j', error);

            // enable dispatch button
            $('#dispatchSubmitButton').attr("disabled", false);

        });
}

// patient functions

function addPatient(index) {

    logger.log('debug', "Adding patient index '%d'", index);

    const name = $('#patient-' + index + '-name').val().trim();
    const age = $('#patient-' + index + '-age').val().trim();

    // is name empty?
    if (!name) {
        dialog.alert(settings.translation_table["Blank name"]);
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

    logger.log('debug', "Removing patient index '%d'", index);

    // remove from storage
    delete currentPatients[index];

    // remove from form
    $('#patients')
        .find('#patient-' + index + '-form')
        .remove();

}

function addPatientForm(index) {

    logger.log('debug', "Adding patient form '%d'", index);

    const patients = $('#patients');

    // add new patient form entry
    patients.append(newPatientForm(index, 'fa-plus'));

    // bind addPatient to click
    patients.find('#patient-' + index + '-button')
        .on('click', function(e) { addPatient(index); });

}

function newPatientForm(index, symbol) {

    // logger.log('debug', 'html = "' + html + '"');

    return '<div class="form-row" id="patient-' + index + '-form">' +
        '<div class="col-md-7 pr-0">' +
        '<input id="patient-' + index + '-name" ' +
        'type="text" ' +
        'class="form-control form-control-sm" ' +
        'placeholder="' + settings.translation_table['Name'] + '">' +
        '</div>' +
        '<div class="col-md-3 px-0">' +
        '<input id="patient-' + index + '-age" ' +
        'type="number" min="0" ' +
        'class="form-control form-control-sm" ' +
        'placeholder="' + settings.translation_table['Age'] + '">' +
        '</div>' +
        '<div class="col-md-2 pl-0">' +
        '<button class="btn btn-default btn-block btn-new-patient btn-sm" ' +
        ' type="button" ' +
        ' id="patient-' + index + '-button">' +
        '<span id="patient-' + index + '-symbol" class="fas ' + symbol + ' fa-sm"></span>' +
        '</button>' +
        '</div>' +
        '</div>';

}

// Ready function
$(function() {

    // Set up dialog
    $('#messages')
        .append(dialog.render());

    // Set up map widget options
 	let options = {
 		map_id: "live-map",
 		zoom: 12,
        map_provider: mapProvider,
        layer_names: [settings.translation_table['Roads'], settings.translation_table['Satellite'], settings.translation_table['Hybrid']]
 	};
 	const map = new LeafletWidget(options);

    // Set map view
    mymap = map.map;

    // Map to fill the view
    resizeMap();

    // Take care of resizing
    $(window).on("resize", function () {
        resizeMap();
    }).trigger("resize");

    // Close popovers if dispatchDiv is hidden
    $('#dispatchDiv')
        .on('hide.bs.collapse', function(event) {

            // hide all popovers
            $('[data-original-title]')
                .popover('hide');

            if (isDispatching)
                $('#newDispatchDiv').collapse('hide');

            /*
            // enable dispatch button
            $('#dispatchSubmitButton').attr("disabled", false);
            */


        });

    // Handle begin dispatching button
    $('#newDispatchDiv')
        .on('show.bs.collapse', function(event) {

            // call begin dispatching
            beginDispatching();

        })
        .on('hide.bs.collapse', function(event) {

            // call end dispatching
            endDispatching();

        });

    $('#dispatch-form-collapse')
        .submit(function (e) {

        // prevent normal form submission
        e.preventDefault();

        // dispatch call
        dispatchCall();

    });

    // Create category panes and filters
    createCategoryPanesAndFilters();

    // Add call priority buttons
    settings.call_priority_order.forEach(function(priority){

        $('#priority-buttons')
            .append(
                '<label id="priority-button-' + priority + '" class="btn btn-outline-' + settings.call_priority_css[priority].class + ' btn-sm">\n' +
                '  <input type="radio" name="priority" autocomplete="off" value="' + priority + '">\n' +
                '  ' + settings.call_priority_css[priority].html + '\n' +
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
            const ambulance_id = e.originalEvent.dataTransfer.getData("text/plain");
            const ambulance = ambulances[ambulance_id];
            logger.log('debug', "dropped ambulance '%s'", ambulance['identifier']);
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

    $('#priority-code-input').on('input', function() {
        const value = $(this).val();
        const option = $('#priority-code-list option[value="'+value+'"]');
        if (option.length) {
            const values = value.split('-', 2);
            const classification = values[0];
            const priority = values[1];
            $('#priority-classification').html(priority_classification[classification]);
            $('#priority-code').html(option.html());
            $('#priority-button-'+priority).button('toggle');
        } else {
            $('#priority-classification').html('<span class="text-muted">' + settings.translation_table["Priority Classification"] + '</span>');
            $('#priority-code').html('<span class="text-muted">' + settings.translation_table["Priority Code"] + '</span>');
            $("#priority-buttons .btn").removeClass("active");
        }
    });

    $('#radio-code-input').on('input', function() {
        const option = $('#radio-code-list option[value="'+$(this).val()+'"]');
        if (option.length)
            $('#radio-code').html(option.html());
        else
            $('#radio-code').html('<span class="text-muted">' + settings.translation_table["Radio Code"] + '</span>');
    });

    if (mapProvider['provider'] === 'google') {
        // Autocomplete address
        const autocompleteFormField = document.getElementById('street');
        const autocompleteOptions = {
            types: ['address'],
        };
        const autocomplete = new google.maps.places.Autocomplete(autocompleteFormField, autocompleteOptions);
        autocomplete.setFields(['address_components', 'formatted_address', 'geometry']);
        google.maps.event.clearInstanceListeners(autocompleteFormField);
        google.maps.event.addListener(autocomplete, 'place_changed', () => {
            // get current location
            const place = autocomplete.getPlace();
            logger.log('debug', "place = %j", place);

            // parse address
            const address = geocoder.parse_feature(place);
            logger.log('debug', "address = '%j'", address);

            // set current location
            updateCurrentLocation({
                lat: address['location']['latitude'],
                lng: address['location']['longitude']
            });

        });
    }

});
