import { LeafletPolylineWidget } from "./leaflet/LeafletWidget";

import {addAmbulanceRoute, addCallWaypoints } from "./map-tools";

import { logger } from './logger';

let map;
let apiClient;
const vehicles = {};

// add initialization hook
add_init_function(init);

// initialization function
function init (client) {

    logger.log('info', '> report-vehicle.js');

    // set apiClient
    apiClient = client;

    // Set range
    const today = new Date();
    today.setHours(0,0,0,0);
    const tomorrow = new Date();
    tomorrow.setDate(today.getDate()+1);

    const range = today.toISOString() + "," + tomorrow.toISOString();
    logger.log('debug', 'range = %j', range)

    // Retrieve vehicles
    apiClient.httpClient.get('ambulance/')
        .then( response => {

            logger.log('debug', "Got ambulance data from API");

            // loop through vehicle records
            const requests = response.data.map( vehicle  => {

                logger.log('debug', 'Adding vehicle %s', vehicle['identifier']);

                // save vehicle
                vehicles[vehicle['id']] = vehicle;
                vehicles[vehicle['id']]['history'] = [];

                const url = 'ambulance/' + vehicle['id'] + '/updates/?filter=' + range;
                const promise = apiClient.httpClient.get(url);
                logger.log('debug', "promise = %s", promise);
                return promise;

            });

            logger.log('debug', "requests = %s", requests);
            return Promise.all(requests);

        })
        .then( responses => responses.forEach(
            response => {

                logger.log('debug', 'IN PROMISE');

                // save updates
                const updates = response.data;
                if (updates.length) {
                    const id = updates[0]['ambulance_id'];
                    vehicles[id]['history'] = updates;

                    // add to map
                    logger.log('debug', "Got '%s' vehicle '%d' updates from API", updates.length, id);
                    addAmbulanceRoute(map, updates, ambulance_status, false);

                }

            }

        ))
        .catch( (error) => {
            logger.log('error', "'Failed to retrieve vehicles: %s ", error);
        });

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
