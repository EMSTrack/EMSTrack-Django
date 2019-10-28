import { LeafletPolylineWidget } from "./leaflet/LeafletWidget";

import {addAmbulanceRoute, breakSegments, calculateLenghtAndSpeed} from "./map-tools";

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

    // set date
    $('#beginDate').text(today);
    $('#endDate').text(tomorrow);

    // Retrieve vehicles
    apiClient.httpClient.get('ambulance/')
        .then( response => {

            // retrieve vehicles
            logger.log('debug', "Got ambulance data from API");

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

                let totalLength = .0;
                let totalTime = .0;
                const length = [];
                const maxSegmentSpeed = [];
                // const avgSegmentSpeed = [];

                let maxSpeed = undefined;
                let avgSpeed = undefined;
                if (history.length) {

                    // break segments
                    const segments = breakSegments(history);
                    segments.map((segment) => {

                        // calculate length, speed and total length
                        const [segmentTotalLength, segmentTotalTime, segmentLength, segmentSpeed] =
                            calculateLenghtAndSpeed(segment);

                        // calculate max and avg
                        maxSegmentSpeed.push(Math.max(...segmentSpeed));
                        // avgSegmentSpeed.push(3.6 * (segmentSpeed.reduce((a, b) => a + b, 0) / segmentSpeed.length));
                        length.push(segmentTotalLength);
                        totalLength += segmentTotalLength;
                        totalTime += segmentTotalTime;

                    });

                    maxSpeed = 3.6 * Math.max(...maxSegmentSpeed);
                    avgSpeed = 3.6 * totalLength / totalTime;

                }

                // length in km
                totalLength /= 1000;

                $('#vehiclesTable> tbody:last-child').append(
                    '<tr>\n' +
                    '  <td>' + vehicle['identifier'] + '</td>\n' +
                    '  <td>' + totalLength.toFixed(2) + ' </td>\n' +
                    '  <td>' + (typeof avgSpeed === 'undefined' ? '&mdash;' : avgSpeed.toFixed(2)) + ' </td>\n' +
                    '  <td>' + (typeof maxSpeed === 'undefined' ? '&mdash;' : maxSpeed.toFixed(2)) + ' </td>\n' +
                    '  <td></td>\n' +
                    '</tr>');
            }

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
