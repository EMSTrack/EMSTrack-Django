import {LeafletPolylineWidget} from "./leaflet/LeafletWidget";

import {logger} from './logger';
import {addAmbulanceRoute, segmentHistory, calculateMotionStatistics} from "./map-tools";
import {validateDateRange, getOrCreateElement} from "./util";

let map;
let apiClient;
const vehicles = {};
let detail = null;

// add initialization hook
add_init_function(init);

// report detail
function reportDetail(id) {

    logger.log('info', "Generating detail report for id '%d'", id);

    const vehicle = vehicles[id];

    // get detail element information
    const detailElement = $('#detail');
    const isDetailVisible = detailElement.is( ":visible" );

    const idElement = $('#detail_id');
    const currentId = idElement.text();

    if (isDetailVisible) {

        logger.log('info', "detail is visible, current id is '%s'", currentId);

        if (currentId === vehicle['identifier']) {

            logger.log('info', "hiding");

            // same vehicle, collapse and return
            detailElement.collapse('hide');
            return;

        }

        // otherwise, this is another element, go ahead

    } else {

        // not visible, set it up and display

        logger.log('info', "detail is not visible, current id is '%s'", currentId);

    }

    // setup detail
    logger.log('info', "setting up");

    // set new detail title
    idElement.text(vehicle['identifier']);

    logger.log('info', "showing...");
    detailElement.collapse('show');

}

// report summary
function reportSummary() {

    logger.log('info', 'Generating summary report');

    // add vehicles to table
    let noActivities = false;
    for (const vehicle of Object.values(vehicles)) {

        // get history
        const history = vehicle['history'];

        // nothing to do?
        if (Object.entries(history).length === 0) {
            continue;
        }

        // set no activities to false
        noActivities = false;

        // retrieve segments
        const segments = history['segments'];

        // calculate statistics
        let [totalDistance, totalTime, totalMovingDistance, totalMovingTime, maxSpeed]
            = calculateMotionStatistics(10 / 3.6, ...segments);
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

        const element = getOrCreateElement(`vehicle_${vehicle['id']}`, (id) => {
            $('#vehiclesTable> tbody:last-child').append(`<tr id="${id}"></tr>`);
        });

        element.html(`
<td><a href="#" id="detail_${vehicle['id']}">${vehicle['identifier']}</a></td>
<td>${totalDistance.toFixed(2)}</td>
<td>${totalTime.toFixed(2)}</td>
<td>${avgSpeed.toFixed(1)}</td>
<td>${totalMovingDistance.toFixed(2)}</td>
<td>${totalMovingTime.toFixed(2)}</td>
<td>${avgMovingSpeed.toFixed(1)}</td>
<td>${maxSpeed.toFixed(1)}</td>`);

        // attach detail handler
        $(`#detail_${vehicle['id']}`).click(function(){ reportDetail(vehicle['id']); return false; });

    }

    if (noActivities) {
        // say no activities
        $('#vehiclesTable> tbody:last-child').append(`<tr><td colspan="8">No activities were recorded in this period.</td></tr>`);
    }

}

function retrieveData(range) {

    // Retrieve vehicles
    return apiClient.httpClient.get('ambulance/')
        .then(response => {

            // retrieve vehicles
            logger.log('debug', "Got vehicle data from API");

            // loop through vehicle records
            const requests = response.data.map(vehicle => {

                logger.log('debug', 'Adding vehicle %s', vehicle['identifier']);

                // save vehicle
                vehicles[vehicle['id']] = vehicle;
                vehicles[vehicle['id']]['history'] = {};

                const url = 'ambulance/' + vehicle['id'] + '/updates/?filter=' + range;
                return apiClient.httpClient.get(url);

            });

            return Promise.all(requests);

        })
        .then(responses =>
            responses.forEach(
                response => {

                    // retrieve updates
                    const history = response.data;
                    if (history.length) {

                        // get id
                        const id = history[0]['ambulance_id'];
                        vehicles[id]['history'] = history;

                        // segment and store
                        const [segments, durations, status, user] = segmentHistory(history);
                        vehicles[id]['history'] = {
                            'history': history,
                            'segments': segments,
                            'durations': durations,
                            'status': status,
                            'user': user
                        };

                        // add to map
                        logger.log('debug', "Got '%s' vehicle '%s' updates from API",
                            history.length, vehicles[id]['identifier']);
                        addAmbulanceRoute(map, history, ambulance_status, false);

                    }

                }
            ));

}

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
        .change(function () {

            logger.log('debug', 'beginDate has changed!');

            const endDateElement = $('#endDate');
            const endDate = new Date(endDateElement.val());
            const beginDate = $(this).val();
            logger.log('debug', 'beginDate = %s, endDate = %s', beginDate, endDate);

            const [_beginDate, _endDate, _minDate] = validateDateRange(beginDate, endDate);
            logger.log('debug', '_beginDate = %s, _endDate = %s, _minDate = %s', _beginDate, _endDate, _minDate);

            // replace endDate if necessary
            endDateElement
                .prop('min', _minDate.toISOString().substr(0, 10));

            if (endDate < _minDate)
                endDateElement.prop('value', _endDate.toISOString().substr(0, 10));

        });

    $('#endDate')
        .prop('value', endDate.toISOString().substr(0, 10))
        .prop('min', minDate.toISOString().substr(0, 10));

    // set range
    const range = beginDate.toISOString() + "," + endDate.toISOString();
    logger.log('debug', 'range = %j', range);

    // retrieve data
    retrieveData(range)
        .then(() => {

            // report summary
            reportSummary();

            // enable generate report button
            $('#submitButton')
                .prop('disabled', false);

            // hide please wait sign
            $('#pleaseWait')
                .hide();

        })
        .catch((error) => {
            logger.log('error', "'Failed to retrieve vehicles: %s ", error);
        })

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
