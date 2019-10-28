import { LeafletPolylineWidget } from "./leaflet/LeafletWidget";

import {addAmbulanceRoute, addCallWaypoints } from "./map-tools";

import { logger } from './logger';

let map;
let apiClient;

// add initialization hook
add_init_function(init);

// initialization function
function init (client) {

    logger.log('info', '> report-vehicle.js');

    // set apiClient
    apiClient = client;

    // Retrieve vehicles
    // retrieveVehicles(map, call_id);

}

$(function () {

    // Set up map widget
    const options = {
        map_id: "map",
        zoom: 12,
        map_provider: mapProvider
    };

    map = new LeafletPolylineWidget(options);

});

function retrieveCall(map, call_id) {

    // Build url
    const url = 'call/' + call_id + '/?exclude=';

    apiClient.httpClient.get(url)
        .then( (response) => {

            logger.log('debug', "Got call data from API");
            addCallToMap(map, response.data);

        })
        .catch( (error) => {
            logger.log('error', 'Failed to retrieve call data: %s', error);
        });

}

function retrieveAmbulanceUpdates(map, ambulance_id, call_id) {

    logger.log('info', "Retrieving ambulance '%d' updates from API", ambulance_id);

    // Build url
    const url = 'ambulance/' + ambulance_id + '/updates/?call_id=' + call_id;

    apiClient.httpClient.get(url)
        .then( (response) => {

            logger.log('debug', "Got '%s' ambulance '%d' updates from API", response.data.length, ambulance_id);
            addAmbulanceRoute(map, response.data, ambulance_status, true);

        })
        .catch( (error) => {
            logger.log('error', "'Failed to retrieve ambulance '%d' updates: %s", ambulance_id, error);
        });

}

function addCallToMap(map, call) {

    logger.log('info', 'Adding call to map');

    // loop through ambulancecall records
    call['ambulancecall_set'].forEach( (ambulancecall)  => {

        logger.log('debug', 'Adding ambulancecall');

        // add waypoints
        addCallWaypoints(map, ambulancecall['waypoint_set']);

        // add ambulance updates
        retrieveAmbulanceUpdates(map, ambulancecall['ambulance_id'], call['id']);

    });

}

function abortCall() {

    // Show modal
    $('#modal-button-ok').show();
    $('#modal-button-cancel').show();
    $('.modal-title')
        .html(translation_table['Abort Call']);
    $('.modal-body')
        .html(translation_table['Are you sure?'])
        .addClass('alert-danger');
    $("#modal-dialog")
        .on('hide.bs.modal', function () {
            const $activeElement = $(document.activeElement);
            if ($activeElement.is('[data-toggle], [data-dismiss]')) {
                if ($activeElement.attr('id') === 'modal-button-ok') {
                    // {% url 'ambulance:call_abort' pk=call.id %}
                    window.location.href = abort_url;
                }
            }
        })
        .modal('show');

}
