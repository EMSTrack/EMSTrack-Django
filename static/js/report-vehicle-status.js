import {logger} from './logger';

import noUiSlider from 'nouislider';
import 'nouislider/distribute/nouislider.css';

import {validateDateRange, millisToTime, millisToSplitTime, splitTimeToMillis} from "./util";

import {calculateDistanceHaversine} from "./map-tools";

let apiClient;
const vehicles = {};

// add initialization hook
add_init_function(init);

function segmentHistory(history, byStatus, byUser, separationRadius, timeInterval) {

	separationRadius = separationRadius || [10, 1000];              // 10m, 1km
	timeInterval = timeInterval || [2 * 60 * 1000, 60 * 60 * 1000]; // 2 minutes, 1 hour

    byStatus = byStatus || true; // split by status
    byUser = byUser || false;     // split by user

    const segments = [];
    const durations = [];
    const status = [];
    const user = [];

    let currentSegment = [];
    let lastPosition = null;
    const n = history.length;
    for (let i = n - 1; i >= 0; i--) {

		// current position
        const currentPosition = history[i];

        // distance?
		if (lastPosition != null) {

            const distance = calculateDistanceHaversine(lastPosition.location, currentPosition.location);                 // meters
            const interval = Math.abs(Date.parse(lastPosition.timestamp) - Date.parse(currentPosition.timestamp)) / 1000; // milliseconds

            // new segment?
            const newSegment =
                distance > separationRadius[1] ||
                interval > timeInterval[1] ||
                (interval > timeInterval[0] && distance > separationRadius[0]);

            // new user?
            const newUser = byUser && lastPosition.updated_by_username !== currentPosition.updated_by_username;

            // new status?
            const newStatus = byStatus && lastPosition.status !== currentPosition.status;

            if ((newUser || newStatus) && !newSegment) {
                // will break in the middle of segment, duplicate current position first
                const newCurrentPosition = Object.assign({}, currentPosition);
                newCurrentPosition.status = lastPosition.status;
                currentSegment.push(newCurrentPosition);
            }

			if (newSegment || newUser || newStatus) {
                // terminate current segment
                durations.push(
                    new Date(currentSegment[currentSegment.length-1].timestamp) -
                    new Date(currentSegment[0].timestamp)
                );  // in milliseconds
                segments.push(currentSegment);
                status.push(lastPosition.status);
                user.push(lastPosition.updated_by_username);
                currentSegment = [];
            }
		}

		// add position to segment
		currentSegment.push(currentPosition);

		// update lastPosition
		lastPosition = currentPosition;

	}

	// anything left?
	if (currentSegment.length > 0) {
        // terminate last segment
        durations.push(
            new Date(currentSegment[currentSegment.length-1].timestamp) -
            new Date(currentSegment[0].timestamp)
        );  // in miliseconds
        segments.push(currentSegment);
        status.push(lastPosition.status);
        user.push(lastPosition.updated_by_username);
    }

	return [segments, durations, status, user];

}

function renderProgress(data, beginDate, endDate) {

    console.log(data);

     // clone durations
    const segments = data['segments'];
    const durations = [...data['durations']];
    const status = data['status'];

    console.log(segments);
    console.log(durations);
    console.log(status);

    // calculate offsets
    const n = status.length;
    const offsets = new Array(n);
    let beforeRange = true;
    const totalTime = endDate.getTime() - beginDate.getTime();
    for (let i = 0; i < n; i++) {

        const segment = segments[i];
        const currentOffset = (new Date(segment[0].timestamp)).getTime() - beginDate.getTime();
        offsets[i] = currentOffset;

        if (beforeRange && currentOffset >= 0) {
            // this is the first element in range
            beforeRange = false;
            if (i > 0 && currentOffset[i - 1] + durations[i - 1] >= 0) {
                // previous status extends in range, shift to zero to ensure continuity
                durations[i - 1] -= currentOffset[i - 1];
                currentOffset[i - 1] = 0;
            }
        }

        if (currentOffset > totalTime) {
            // simply break, out of range
            break;
        }

        if (currentOffset + durations[i] > totalTime) {
            // match end and break
            durations[i] -= (currentOffset + durations[i] - totalTime);
            break;
        }

    }

    // build progress bar
    let cursor = 0;
    let progress = '<div class="progress" style="height: 20px;">\n';
    for (let i = 0; i < n; i++) {

        // not in range yet
        if (offsets[i] < 0)
            continue;

        // out of range, break
        if (offsets[i] > totalTime)
            break;

        // in range, advance bar until start
        const start = 100 * (offsets[i] / totalTime);
        logger.log('debug', 'start = %s', start);
        if (start > cursor) {
            const delta = (start - cursor);
            progress += `<div class="progress-bar bg-light" role="progressbar" style="width: ${delta}%" aria-valuenow="${delta}" aria-valuemin="0" aria-valuemax="100"></div>\n`;
            cursor = start;
            logger.log('debug', 'delta = %s', delta);
        }

        // fill bar with duration fraction
        const fraction = (100 * (durations[i] / totalTime));
        const status_class = ambulance_css[status[i]]['class'];
        progress += `<div class="progress-bar bg-${status_class}" role="progressbar" style="width: ${fraction}%" aria-valuenow="${fraction}" aria-valuemin="0" aria-valuemax="100"></div>\n`;
        cursor += fraction;

        logger.log('debug', 'status = %s', status[i]);
        logger.log('debug', 'fraction = %s', fraction);
        logger.log('debug', 'cursor = %s', cursor);

    }

    progress += '</div>';
    // logger.log('debug', 'progress = %s', progress);

    return progress;

}

function getOrCreateElement(id, label, extraClasses = "", style = "background-color: #F9F9F9") {

    // get element
    const selector = `#${id}`;
    let element = $(selector);
    if (element.length === 0) {

        // create element first
        element = $(
`<div class="row">
  <div class="col-2">
    ${label}
  </div>
  <div class="col-10 ${extraClasses}" id="${id}" style="${style}">
  </div>
</div>`);
        $('#vehiclesTable').append(element);

        // assign created element
        element = $(selector);
    }

    return element;
}

function renderVehicle(vehicle, beginDate, endDate) {

    // get history
    const history = vehicle['history'];

    // get element
    const element = getOrCreateElement(`vehicle_${vehicle['id']}`, vehicle['identifier'], "mt-2");

    // nothing to do?
    if (Object.entries(history).length === 0) {
        return;
    }

    // render progress
    const progress = renderProgress(history, beginDate, endDate);
    // logger.log('debug', 'progress = %s', progress);

    // replace element content
    element.html(progress);

}

function renderRuler(beginDate, endDate, offsetMillis = 0) {

    // get element
    const element = getOrCreateElement('ruler', '<strong>Time</strong>');

    // add time scale to table
    let progress = '<div class="progress" style="height: 20px;">\n';
    const totalTime = endDate.getTime() - beginDate.getTime();

    // const [hours, minutes, seconds, milliseconds] = millisToSplitTime(offsetMillis);
    const nextHourMillis = splitTimeToMillis(Math.ceil(offsetMillis / 1000 / 60 / 60), 0, 0, 0);
    const [offsetHour, minutes, seconds, milliseconds] = millisToSplitTime(nextHourMillis);

    logger.log('debug', 'offsetHour = %s:%s:%s.%s, nextHourMillis = %s',
        offsetHour, minutes, seconds, milliseconds, nextHourMillis);

    const labels = ['secondary', 'light'];

    // left edge
    let offsetDelta = 100 * ((nextHourMillis - offsetMillis) / totalTime);
    progress += `<div class="progress-bar bg-${labels[(offsetHour - 1)% 2]}" role="progressbar" style="width: ${offsetDelta}%" aria-valuenow="${offsetDelta}" aria-valuemin="0" aria-valuemax="100"></div>\n`;

    logger.log('debug', 'offsetDelta = %s', offsetDelta);

    const numberOfHours = Math.floor(totalTime / 1000 / 60 / 60);
    const delta = 100 * (1000 * 60 * 60 / totalTime);
    for (let i = offsetHour; i < offsetHour + numberOfHours; i++) {
        progress += `<div class="progress-bar bg-${labels[i % 2]} text-${labels[(i + 1) % 2]}" role="progressbar" style="width: ${delta}%" aria-valuenow="${delta}" aria-valuemin="0" aria-valuemax="100">${i}</div>\n`;
    }

    // right edge
    offsetDelta = 100 - offsetDelta - numberOfHours * delta;
    progress += `<div class="progress-bar bg-${labels[(offsetHour + numberOfHours)% 2]}" role="progressbar" style="width: ${offsetDelta}%" aria-valuenow="${offsetDelta}" aria-valuemin="0" aria-valuemax="100"></div>\n`;

    logger.log('debug', 'offsetDelta = %s', offsetDelta);

    progress += '</div>';
    // logger.log('debug', 'progress = %s', progress);

    // replace element content
    element.html(progress);

}

// initialization function
function init (client) {

    logger.log('info', '> report-vehicle-status.js');

    // set apiClient
    apiClient = client;

    // get parameters
    const urlParams = new URLSearchParams(window.location.search);

    // set beginDate
    const [beginDate, endDate, minTime] = validateDateRange(urlParams.get('beginDate'));
    logger.log('debug', 'beginDate = %s, endDate = %s', beginDate, endDate);

    const beginTime = beginDate.toTimeString().substr(0, 8);
    const endTime = endDate.toTimeString().substr(0, 8);
    logger.log('debug', 'beginTime = %s, endTime = %s', beginTime, endTime);

    // set datepickers
    $('#beginDate')
        .prop('value', beginDate.toISOString().substr(0, 10));

    // setup slider
    const slider = document.getElementById('slider-range');
    noUiSlider.create(slider, {
        start: [0, 24],
        connect: true,
        step: 1/4,
        margin: 1,
        range: {
            'min': [0],
            'max': [24]
        },
        pips: {
            mode: 'count',
            values: 25,
            density: 4*24/100,
        }
    }).on('change', function(e) {

        const [begin, end] = slider.noUiSlider.get();
        logger.log('info', 'begin = %s, end = %s', begin, end);

        // offset beginDate
        const offsetBeginDate = new Date(beginDate);
        const beginMillis = Number.parseFloat(begin) * 60 * 60 * 1000;
        offsetBeginDate.setTime(offsetBeginDate.getTime() + beginMillis);

        const offsetEndDate = new Date(beginDate);
        const endMillis = Number.parseFloat(end) * 60 * 60 * 1000;
        offsetEndDate.setTime(offsetEndDate.getTime() + endMillis);

        logger.log('debug', 'offsetBeginDate = %s, offsetEndDate = %s', offsetBeginDate, offsetEndDate);

        // set time inputs
        const beginTime = millisToTime(beginMillis);
        let endTime = millisToTime(endMillis);
        if (endTime === "24:00") {
            endTime = "00:00";
        }
        logger.log('debug', 'beginTime = %s, endTime = %s', beginTime, endTime);

        $('#beginTime').val(beginTime);
        $('#endTime').val(endTime);

        // modify ruler
        renderRuler(offsetBeginDate, offsetEndDate, beginMillis);

        // add vehicles to page
        for (const vehicle of Object.values(vehicles)) {
            renderVehicle(vehicle, offsetBeginDate, offsetEndDate);
        }

    });

    // set connect color
    slider.querySelectorAll('.noUi-connect')[0].classList.add('bg-primary');

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
                vehicles[vehicle['id']]['history'] = {};

                const url = 'ambulance/' + vehicle['id'] + '/updates/?filter=' + range;
                return apiClient.httpClient.get(url);

            });

            return Promise.all(requests);

        })
        .then( responses =>
            responses.forEach(
                response => {

                    // retrieve updates
                    const history = response.data;
                    if (history.length) {

                        // get id
                        const id = history[0]['ambulance_id'];

                        // segment by status and store
                        const [segments, durations, status, user] = segmentHistory(history, true, false);
                        vehicles[id]['history'] = {
                            'history': history,
                            'segments': segments,
                            'durations': durations,
                            'status': status,
                            'user': user
                        };

                    }

                }
        ))
        .then( () => {

            // render ruler
            renderRuler(beginDate, endDate);

            // add vehicles to page
            for (const vehicle of Object.values(vehicles)) {
                renderVehicle(vehicle, beginDate, endDate);
            }

            // enable generate report button
            $('#submitButton')
                .prop('disabled', false);

        })
        .catch( (error) => {
            logger.log('error', "'Failed to retrieve vehicles: %s ", error);
        });

}

$(function () {

    logger.log('info', 'beginning of ready function');

    logger.log('info', 'end of ready function');

});
