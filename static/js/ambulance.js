import { LeafletPolylineWidget } from "./leaflet/LeafletWidget";

import { logger } from './logger';

import { Settings } from './settings';

import { Pagination, Pages } from './components/pagination';

import {addAmbulanceRoute} from "./map-tools";

// Initialize settings
const settings = new Settings(html_settings);
console.log(settings);

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
    const pages = new Pages(window.location);

    // set page sizes
    $('#page_sizes')
        .html(pages.render("justify-content-end"));

 	// Retrieve ambulances via AJAX
    retrieveAmbulanceData(ambulanceId, pages.page, pages.page_size);

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

function render_page_callback(page, options, ambulanceId, page_size) {
    const element = $(`<a class="page-link" href="#" >${options.label}</a>`);
    element.click( function () {

        // clear map first
        if ( !$('#overlap').is(':checked') )
            map.clearLayers();

        // then retrieve new updates
        retrieveAmbulanceData(ambulanceId, page, page_size);

        return false;
    });
    return element;
}

function retrieveAmbulanceData(ambulanceId, page, page_size) {

    // Build url
    const url = `ambulance/${ambulanceId}/updates?page=${page}&page_size=${page_size}`;

    // set message
    $('#pleaseWait')
        .show();

    apiClient.httpClient.get(url)
        .then( (response) => {

            console.log(response.data);

            // set pagination
            const pagination = new Pagination(response.data.previous, response.data.next, response.data.count,
                page_size, page);
            $('#pagination')
                .html(pagination.render((pg, options) => render_page_callback(pg, options, ambulanceId, page_size)));

            logger.log('debug', "Got '%s' ambulance '%d' updates from API", response.data.length, ambulanceId);
            addAmbulanceRoute(map, response.data, settings.ambulance_status, true);
            // addAmbulanceRoute(response.data);

            $('#pleaseWait')
                .hide();

        })
        .catch( (error) => {
            logger.log('info', 'Failed to retrieve ambulance data: %s', error);
        });

}
