import { LeafletPolylineWidget } from "./leaflet/LeafletWidget";

import { logger } from './logger';

import { Settings } from './settings';

import { Pagination } from './components/pagination';

import {addAmbulanceRoute} from "./map-tools";

const settings = new Settings();

let map;
let apiClient;

// add initialization hook
add_init_function(init);

// initialization function
function init (client) {

    console.log('> ambulance.js');

    // set apiClient
    apiClient = client;

    // get ambulance_id
    const url = window.location.pathname.split('/');
    const ambulanceId = url[url.length - 1];

    logger.log('debug', 'ambulance_id = %s', ambulanceId);

 	// get page and page_size parameters
    const searchParams = new URLSearchParams(window.location.search);
    const page = searchParams.has('page') ? searchParams.get('page') : 1;
	const page_size = searchParams.has('page_size') ? searchParams.get('page_size') : 500;

    logger.log('debug', 'page = %s, page_size = %s', page, page_size);

 	// Retrieve ambulances via AJAX
    retrieveAmbulanceData(ambulanceId, page, page_size);

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

function retrieveAmbulanceData(ambulanceId, page, page_size) {

    // Build url
    const url = `ambulance/${ambulanceId}/updates?page=${page}&page_size=${page_size}`;

    apiClient.httpClient.get(url)
        .then( (response) => {

            console.log(response.data);

            // set pagination
            const pagination = Pagination(response.data.previous, response.data.next, response.data.count,
                page_size, page);
            $('pagination')
                .html(pagination.render());

            logger.log('debug', "Got '%s' ambulance '%d' updates from API", response.data.length, ambulanceId);
            addAmbulanceRoute(map, response.data, settings.ambulance_status, true);
            // addAmbulanceRoute(response.data);

        })
        .catch( (error) => {
            logger.log('info', 'Failed to retrieve ambulance data: %s', error);
        });

}
