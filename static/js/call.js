import { LeafletPolylineWidget } from "./leaflet/LeafletWidget";

import {addAmbulanceRoute, addCallWaypoints } from "./map-tools";

import { logger } from './logger';

let map;
let apiClient;

// add initialization hook
add_init_function(init);

// initialization function
function init (client) {

    logger.log('info', '> call.js');

    // set apiClient
    apiClient = client;

    // Retrieve call
    retrieveCall(call_id, map);

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

function retrieveCall(call_id, map) {

    // Build url
    const url = 'call/' + call_id + '/?exclude=';

    apiClient.httpClient.get(url)
        .then( (response) => {

            logger.log('debug', "Got call data from API");
            addCallToMap(response.data, map);

        })
        .catch( (error) => {
            logger.log('error', 'Failed to retrieve call data: %s', error);
        });

}

function retrieveAmbulanceUpdates(ambulance_id, call_id, map) {

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

function addCallToMap(call, map, icon) {

    logger.log('info', 'Adding call to map');

    // loop through ambulancecall records
    call['ambulancecall_set'].forEach( (ambulancecall)  => {

        logger.log('debug', 'Adding ambulancecall');

        // add waypoints
        addCallWaypoints(ambulancecall['waypoint_set']);

        // add ambulance updates
        retrieveAmbulanceUpdates(ambulancecall['ambulance_id'], call['id'], map);

    });

}
