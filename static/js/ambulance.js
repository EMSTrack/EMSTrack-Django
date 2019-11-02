import { LeafletPolylineWidget } from "./leaflet/LeafletWidget";

import { logger } from './logger';

import {addAmbulanceRoute} from "./map-tools";

let map;
let page;
let apiClient;

// add initialization hook
add_init_function(init);

// initialization function
function init (client) {

    console.log('> ambulance.js');

    // set apiClient
    apiClient = client;

 	// Retrieve ambulances via AJAX
    retrieveAmbulanceData(ambulance_id);

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

 	// get page and page_size parameters
    const searchParams = new URLSearchParams(window.location.search);
    if (searchParams.has('page'))
        page = searchParams.get('page');
	if (searchParams.has('page_size'))
        page_size = searchParams.get('page_size');

});

function retrieveAmbulanceData(ambulance_id) {

    // Build url
    let url = 'ambulance/' + ambulance_id + '/updates';
    if (page != null) {
        url += "?page=" + page;
        if (page_size != null)
            url += "&page_size=" + page_size;
    } else if (page_size != null)
            url += "?page_size=" + page_size;

    apiClient.httpClient.get(url)
        .then( (response) => {

            logger.log('debug', "Got '%s' ambulance '%d' updates from API", response.data.length, ambulance_id);
            addAmbulanceRoute(map, response.data, ambulance_status, true);
            // addAmbulanceRoute(response.data);

        })
        .catch( (error) => {
            console.log('Failed to retrieve ambulance data');
            console.log(error);
        });

}
