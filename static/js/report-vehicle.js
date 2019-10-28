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
    const today = new Date();
    today.setHours(0,0,0,0);
    const tomorrow = new Date();
    tomorrow.setDate(today.getDate()+1);

    const range = today.toISOString() + "," + tomorrow.toISOString();
    logger.log('debug', 'range = %j', range)
    retrieveVehicles(map, range);

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

function retrieveVehicles(map, range) {

    // Build url
    const url = 'ambulance/';

    apiClient.httpClient.get(url)
        .then( (response) => {

            logger.log('debug', "Got ambulance data from API");

            // loop through ambulancecall records
            response.data.forEach( (vehicle)  => {

                logger.log('debug', 'Adding vehicle %s', vehicle['identifier']);

                // add ambulance updates
                retrieveVehicleUpdates(map, vehicle['id'], range);

            });

        })
        .catch( (error) => {
            logger.log('error', 'Failed to retrieve ambulance data: %s', error);
        });

}

function retrieveVehicleUpdates(map, ambulance_id, range) {

    logger.log('info', "Retrieving ambulance '%d' updates from API", ambulance_id);

    // Build url
    const url = 'ambulance/' + ambulance_id + '/updates/?filter=' + range;

    apiClient.httpClient.get(url)
        .then( (response) => {

            logger.log('debug', "Got '%s' ambulance '%d' updates from API", response.data.length, ambulance_id);
            addAmbulanceRoute(map, response.data, ambulance_status, false);

        })
        .catch( (error) => {
            logger.log('error', "'Failed to retrieve ambulance '%d' updates: %s", ambulance_id, error);
        });

}
