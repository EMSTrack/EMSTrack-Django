import {LeafletPolylineWidget} from "./leaflet/LeafletWidget";

import {addAmbulanceRoute, segmentHistory, calculateMotionStatistics} from "./map-tools";

import {logger} from './logger';
import {validateDateRange} from "./util";

let map;
let apiClient;
const vehicles = {};

// add initialization hook
add_init_function(init);

// setdates

// initialization function
function init (client) {

    logger.log('info', '> report-vehicle-mileage.js');

    // set apiClient
    apiClient = client;

    // get parameters
    const urlParams = new URLSearchParams(window.location.search);

    // set beginDate
    const [beginDate, endDate, minDate] = validateDateRange(urlParams.get('beginDate'), urlParams.get('endDate'));
    logger.log('debug', 'beginDate = %s, endDate = %s, minDate = %s', beginDate, endDate, minDate);

    // set datepickers
    $('#beginDate')
        .prop('value', beginDate.toISOString().substr(0, 10))
        .change(function() {

            logger.log('debug', 'beginDate has changed!');

            const endDateElement = $('#endDate');
            const endDate = new Date(endDateElement.val());
            const beginDate = $( this ).val();
            logger.log('debug', 'beginDate = %s, endDate = %s', beginDate, endDate);

            const [_beginDate, _endDate, _minDate] = validateDateRange(beginDate, endDate);
            logger.log('debug', '_beginDate = %s, _endDate = %s, _minDate = %s', _beginDate, _endDate, _minDate);

            // replace endDate if necessary
            endDateElement
                .prop('min', _minDate.toISOString().substr(0, 10))
                .prop('value', _endDate.toISOString().substr(0, 10));

        });

    $('#endDate')
        .prop('value', endDate.toISOString().substr(0, 10))
        .prop('min', minDate.toISOString().substr(0, 10));

    // set range
    const range = beginDate.toISOString() + "," + endDate.toISOString();
    logger.log('debug', 'range = %j', range)

    // Retrieve vehicles
    apiClient.httpClient.get('ambulance/')
        .then( response => {

            // retrieve vehicles
            logger.log('debug', "Got vehicle data from API");

            // loop through vehicle records
            const requests = response.data.map( vehicle  => {

                logger.log('debug', 'Adding vehicle %s', vehicle['identifier']);

                // save vehicle
                vehicles[vehicle['id']] = vehicle;
                vehicles[vehicle['id']]['history'] = [];

                const url = 'ambulance/' + vehicle['id'] + '/updates/?filter=' + range;
                return apiClient.httpClient.get(url);

            });

            return Promise.all(requests);

        })
        .then( responses =>
            responses.forEach(
                response => {

                    // retrieve updates
                    const updates = response.data;
                    if (updates.length) {
                        const id = updates[0]['ambulance_id'];
                        vehicles[id]['history'] = updates;

                        // add to map
                        logger.log('debug', "Got '%s' vehicle '%s' updates from API",
                                   updates.length, vehicles[id]['identifier']);
                        addAmbulanceRoute(map, updates, ambulance_status, false);

                    }

                }
        ))
        .then( () => {

            // add vehicles to table
            for (const vehicle of Object.values(vehicles)) {

                // get history
                const history = vehicle['history'];

                // break segments
                const segments = segmentHistory(history, false, false);

                // calculate statistics
                let [totalDistance, totalTime, totalMovingDistance, totalMovingTime, maxSpeed]
                    = calculateMotionStatistics(10/3.6, ...segments);
                let avgSpeed = totalTime > 0 ? totalDistance / totalTime : 0.0;
                let avgMovingSpeed = totalMovingTime > 0 ? totalMovingDistance / totalMovingTime : 0.0;

                // convert to proper units
                totalTime /= 3600;             // h
                totalMovingTime /= 3600;       // h

                totalDistance /= 1000;         // km
                totalMovingDistance /= 1000;   // km

                maxSpeed *= 3.6;               // km/h
                avgSpeed *= 3.6;               // km/h
                avgMovingSpeed *= 3.6;         // km/h

                $('#vehiclesTable> tbody:last-child').append(
                    '<tr>\n' +
                    '  <td>' + vehicle['identifier'] + '</td>\n' +
                    '  <td>' + totalDistance.toFixed(2) + ' </td>\n' +
                    '  <td>' + totalTime.toFixed(2) + ' </td>\n' +
                    '  <td>' + avgSpeed.toFixed(1) + ' </td>\n' +
                    '  <td>' + totalMovingDistance.toFixed(2) + ' </td>\n' +
                    '  <td>' + totalMovingTime.toFixed(2) + ' </td>\n' +
                    '  <td>' + avgMovingSpeed.toFixed(1) + ' </td>\n' +
                    '  <td>' + maxSpeed.toFixed(1) + ' </td>\n' +
                    '</tr>');
            }

            // enable geneate report button
            $('#submitButton')
                .prop('disabled', false);

        })
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
