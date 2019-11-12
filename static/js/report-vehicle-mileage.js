import {LeafletPolylineWidget} from "./leaflet/LeafletWidget";

import {logger} from './logger';
import {addAmbulanceRoute, segmentHistory, calculateMotionStatistics} from "./map-tools";
import {validateDateRange, getOrCreateElement} from "./util";

import {Chart} from 'chart.js';
import 'chartjs-plugin-zoom';

let map;
let apiClient;
const vehicles = {};
let xAxesMode, detailVehicleId = -1;

let movingSpeedThreshold = 5 / 3.6; // (m/s)
let movingDistanceThreshold = 5;    // m

// add initialization hook
add_init_function(init);

// render detail
function renderDetail(vehicle, xAxesMode) {

    const data = vehicle['data'];

    logger.log('info', "Rendering detail report for vehicle '%s'", vehicle['identifier']);

    // console.log(data);

    const segments = data['segments'];

    const distance = data['distance'];
    const speed = data['speed'];
    const time = data['time'];

    const n = segments.length;
    const plotDataSets = new Array(n);

    let xAxes;
    if (xAxesMode === 'time') {

        for (let i = 0; i < n; i++) {

            const currentTime = time[i];
            const currentSpeed = speed[i];

            const m = currentSpeed.length;
            const plotData = new Array(m);
            for (let j = 0; j < m; j++) {
                plotData[j] = { t: currentTime[j], y: 3.6 * currentSpeed[j] }
            }
            plotDataSets[i] = {
                data: plotData,
                fill: false,
                borderColor: "#3e95cd"
            };
        }

        xAxes = [{
            type: 'time',
            distribution: 'linear'
        }];

    } else { // xAxesMode === 'distance'

        let totalDistance = 0;
        for (let i = 0; i < n; i++) {

            const currentDistance = distance[i];
            const currentSpeed = speed[i];

            const m = currentDistance.length;
            const plotData = new Array(m);
            for (let j = 0; j < m; j++) {
                totalDistance += currentDistance[j];
                plotData[j] = { x: totalDistance / 1000, y: 3.6 * currentSpeed[j] }
            }
            plotDataSets[i] = {
                data: plotData,
                fill: false,
                borderColor: "#3e95cd"
            };
        }

        xAxes = [{
            type: 'linear',
            scaleLabel: {
                display: true,
                labelString: 'distance (km)'
            },
            ticks: {
                max: totalDistance / 1000,
                min: 0
            }
        }];

    }

    const plotOptions = {
        scales: {
            xAxes: xAxes,
            yAxes: [{
                scaleLabel: {
                    display: true,
                    labelString: 'speed (km/h)'
                },
                ticks: {
                    min: 3.6 * movingSpeedThreshold
                }
            }]
        },
        legend: {
            display: false
        },
        tooltips: {
            enabled: false
        },
        elements: {
            point:{
                radius: 0
            },
            line: {
                tension: 0 // disables bezier curves
            },
            animation: {
                duration: 0 // general animation time
            },
            hover: {
                animationDuration: 0 // duration of animations when hovering an item
            },
            //responsiveAnimationDuration: 0 // animation duration after a resize
        },
        responsive: true,
        pan: {
            enabled: true,
            mode: 'x',
        },
        zoom: {
            enabled: true,
            drag: true,
            mode: 'xy',
            speed: 0.1,
        }

    };

    // console.log(plotDataSets);

    const ctx = $('#speedChart');
    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            datasets: plotDataSets
        },
        options: plotOptions
    });

    $('#resetZoomButton')
        .click( function () {
            chart.resetZoom();
        });

}

// report detail
function reportDetail(id) {

    logger.log('info', "Generating detail report for id '%d'", id);

    const vehicle = vehicles[id];

    // console.log(vehicle);

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
            detailVehicleId = -1;

            return;

        }

        // otherwise, this is another element, go ahead

    } else {

        // not visible, set it up and display

        logger.log('info', "detail is not visible, current id is '%s'", currentId);

    }

    // setup detail
    logger.log('info', "setting up");

    // set detailVehicle
    detailVehicleId = vehicle['id'];

    // set new detail title
    idElement.text(vehicle['identifier']);

    // render detail
    renderDetail(vehicle, xAxesMode);

    logger.log('info', "showing...");
    detailElement.collapse('show');

}

// report summary
function reportSummary() {

    logger.log('info', 'Generating summary report');

    // add vehicles to table
    let noActivities = true;
    for (const vehicle of Object.values(vehicles)) {

        // get history
        const data = vehicle['data'];

        // nothing to do?
        if (Object.entries(data).length === 0) {
            continue;
        }

        // set no activities to false
        noActivities = false;

        // retrieve segments
        const segments = data['segments'];

        // calculate statistics
        let [totalDistance, totalTime, totalMovingDistance, totalMovingTime, maxSpeed, distance, speed, time]
            = calculateMotionStatistics(movingSpeedThreshold, movingDistanceThreshold, ...segments);
        let avgSpeed = totalTime > 0 ? totalDistance / totalTime : 0.0;
        let avgMovingSpeed = totalMovingTime > 0 ? totalMovingDistance / totalMovingTime : 0.0;

        // store distance and speed
        vehicle['data']['distance'] = distance;
        vehicle['data']['speed'] = speed;
        vehicle['data']['time'] = time;

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

function processVehicleHistory(vehicle, history) {

    logger.log('debug', "Got '%s' updates for vehicle '%s' from API", history.length, vehicle['identifier']);

    if (history.length) {

        // get id
        const id = vehicle['id'];

        // segment and store
        const [segments, durations, status, user] = segmentHistory(history);
        vehicles[id]['data'] = {
            'history': history,
            'segments': segments,
            'durations': durations,
            'status': status,
            'user': user
        };

        // add to map
        addAmbulanceRoute(map, history, ambulance_status, false);

    }

}

function retrieveVehicleHistory(data, range, index, page_size=1000, page=1, history=[]) {

    // get current vehicle
    const vehicle = data[index];

    logger.log('debug', 'Retrieving vehicle %s page %d...', vehicle['identifier'], page);

    const url = `ambulance/${vehicle['id']}/updates/?page=${page}&page_size=${page_size}&filter=${range}`;
    return apiClient.httpClient.get(url)
        .then( response => {

            // retrieve updates and add to history
            const pageData = response.data;
            history = history.concat(pageData.results);
            const totalPages = Math.ceil(pageData.count / page_size);

            logger.log('debug', 'Processing vehicle %s data, page %d of %d...',
                vehicle['identifier'], page, totalPages);

            // update message
            $('#pleaseWaitVehicle').text(`${vehicle['identifier']}, page ${page} of ${totalPages}`);

            logger.log('debug', 'page %d: vehicle %s history has %d records, next=%s',
                page, vehicle['identifier'], history.length, pageData.next);

            // has next page?
            if (pageData.next !== null)

                // retrieve next page
                retrieveVehicleHistory(data, range, index, page_size, page+1, history);

            else {

                try {

                    // process vehicle history
                    processVehicleHistory(vehicle, history);

                } catch(error) {
                    console.log(error);
                }

                // retrieve next vehicle
                retrieveVehicles(data, range, index + 1);

            }

        })
        .catch((error) => {
            logger.log('error', "'Failed to retrieve vehicle %s, page %d, error: %s",
                vehicle['identifier'], page, error);

            // retrieve next vehicle
            retrieveVehicles(data, range, index + 1);
        });

}

function retrieveVehicles(data, range, index = 0) {

    if (index === data.length) {

        // no more vehicles, produce report
        logger.log('debug', 'Generating report...');

        // Update please wait message
        const pleaseWait = $('#pleaseWait');
        pleaseWait.text("Generating report...");

        // report summary
        reportSummary();

        // enable generate report button
        $('#submitButton')
            .prop('disabled', false);

        // hide please wait sign
        pleaseWait.hide();

        // and return
        return

    }

    // get current vehicle
    const vehicle = data[index];

    logger.log('debug', 'Adding vehicle %s', vehicle['identifier']);

    // save vehicle in global variable vehicles
    vehicles[vehicle['id']] = vehicle;
    vehicles[vehicle['id']]['data'] = {};

    $('#pleaseWaitVehicle').text(vehicle['identifier']);

    // retrieve updates
    return retrieveVehicleHistory(data, range, index);

}

function retrieveData(range) {

    // Retrieve vehicles
    return apiClient.httpClient.get('ambulance/')
        .then(response => {

            // retrieve vehicles
            logger.log('debug', "Got vehicle data from API");

            // loop through vehicle records
            retrieveVehicles(response.data, range);

        })

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
    logger.log('debug', '> beginDate = %s, endDate = %s, minDate = %s', beginDate, endDate, minDate);

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

    // mode
    xAxesMode = $('input[name="x-axis"]:checked').val();
    logger.log('debug', 'x-axis= %s', xAxesMode);

    // set radio input
    $('input[type="radio"][name="x-axis"]')
        .change( function() {

            // return if no change
            if (this.value === xAxesMode)
                return;

            // render
            xAxesMode = this.value;

            // segment history
            renderDetail(vehicles[detailVehicleId], xAxesMode);

        });

    // retrieve data
    retrieveData(range)
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
