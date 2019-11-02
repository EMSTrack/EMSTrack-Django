import { LeafletPolylineWidget } from "./leaflet/LeafletWidget";

import { logger } from './logger';

import {addAmbulanceRoute} from "./map-tools";

let map;
let apiClient;

// add initialization hook
add_init_function(init);

// initialization function
function init (client) {

    console.log('> ambulance.js');

    // set apiClient
    apiClient = client;

 	// get page and page_size parameters
    const searchParams = new URLSearchParams(window.location.search);
    const page = searchParams.has('page') ? searchParams.get('page') : 1;
	const page_size = searchParams.has('page_size') ? searchParams.get('page_size') : 500;

 	// Retrieve ambulances via AJAX
    retrieveAmbulanceData(ambulance_id, page, page_size);

}

// Ready function
$(function() {

 	// Set up map widget options
 	let options = {
 		map_id: "map",
 		zoom: 12,
        map_provider: mapProvider
 	};
 	map = new LeafletPolylineWidget(options);

});

function retrieveAmbulanceData(ambulance_id, page, page_size) {

    // Build url
    const url = `ambulance/${ambulance_id}/updates?page=${page}&page_size=${page_size}`;

    apiClient.httpClient.get(url)
        .then( (response) => {

            logger.log('debug', "Got '%s' ambulance '%d' updates from API", response.data.length, ambulance_id);
            addAmbulanceRoute(map, response.data, ambulance_status, true);
            // addAmbulanceRoute(response.data);

        })
        .catch( (error) => {
            logger.log('info', 'Failed to retrieve ambulance data: %s', error);
        });

}
