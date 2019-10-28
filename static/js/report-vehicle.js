import { LeafletPolylineWidget } from "./leaflet/LeafletWidget";

import {addAmbulanceRoute, breakSegments, calculateMotionStatistics} from "./map-tools";

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

    // get parameters
    const urlParams = new URLSearchParams(window.location.search);

    // set beginDate
    let beginDate = urlParams.get('beginDate');
    if (beginDate == null) {
        beginDate = new Date();
        beginDate.setHours(0,0,0,0);
    } else {
        new Date(beginDate);
    }

    /// set minDate
    let minDate = new Date();
    minDate.setDate(beginDate.getDate()+1);

    // set endDate
    let endDate = urlParams.get('endDate');
    if (endDate == null) {
        endDate = minDate;
    } else {
        endDate = new Date(endDate);
        if (endDate < beginDate) {
            endDate = minDate;
        } else {
            endDate.setHours(0,0,0,0);
        }
    }
    logger.log('debug', 'beginDate = %s, minDate = %s, endDate = %s', beginDate, minDate, endDate);

    // set datepickers
    $('#beginDate')
        .prop('value', beginDate.toISOString().substr(0, 10));

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
                const segments = breakSegments(history);

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
                    '  <td>' + totalDistance.toFixed(0) + ' </td>\n' +
                    '  <td>' + totalTime.toFixed(2) + ' </td>\n' +
                    '  <td>' + avgSpeed.toFixed(1) + ' </td>\n' +
                    '  <td>' + totalMovingDistance.toFixed(0) + ' </td>\n' +
                    '  <td>' + totalMovingTime.toFixed(1) + ' </td>\n' +
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
