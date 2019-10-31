import {logger} from './logger';

import noUiSlider from 'nouislider';
import 'nouislider/distribute/nouislider.css';

import {
    getOrCreateElement,
    millisToSplitTime,
    millisToTime,
    splitTimeToMillis,
    validateDateRange
} from "./util";

import {segmentHistory} from "./map-tools";

let apiClient;
const vehicles = {};
let mode;

// add initialization hook
add_init_function(init);

function renderProgress(data, beginDate, endDate, mode) {

    console.log(data);

    // clone durations
    const segments = data['segments'];
    const durations = [...data['durations']];
    let values;
    if (mode === 'status')
        values = data['status'];
    else if (mode === 'user')
        values = data['user'];
    else
        throw "Unknown mode '" + mode + "'";

    // console.log(segments);
    // console.log(durations);
    // console.log(status);

    // calculate offsets
    const n = values.length;
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

        const currentOffset = offsets[i];
        const currentValue = values[i];

        // not in range yet
        if (currentOffset < 0)
            continue;

        // out of range, break
        if (currentOffset > totalTime)
            break;

        // in range, advance bar until start
        const start = 100 * (currentOffset / totalTime);
        logger.log('debug', 'start = %s', start);
        if (start > cursor) {
            const delta = (start - cursor);
            progress +=
                `<div class="progress-bar bg-light" role="progressbar" style="width: ${delta}%" 
aria-valuenow="${delta}" aria-valuemin="0" aria-valuemax="100"></div>`;
            cursor = start;
            logger.log('debug', 'delta = %s', delta);
        }

        // fill bar with duration fraction
        const fraction = (100 * (durations[i] / totalTime));

        let bgclass, label;
        if (mode === 'status') {
            bgclass = ambulance_css[currentValue]['class'];
            label = ambulance_status[currentValue];
        } else { // mode === 'user'
            bgclass = 'primary';
            label = currentValue;
        }
        progress += `<div class="progress-bar bg-${bgclass}" role="progressbar" style="width: ${fraction}%"
aria-valuenow="${fraction}" aria-valuemin="0" aria-valuemax="100"
data-toggle="tooltip" data-placement="top" title="${label}"></div>`;
        cursor += fraction;

        logger.log('debug', 'status = %s', currentValue);
        logger.log('debug', 'fraction = %s', fraction);
        logger.log('debug', 'cursor = %s', cursor);

    }

    progress += '</div>';
    // logger.log('debug', 'progress = %s', progress);

    return progress;

}

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

function createElement(id, label, style = "", extraColClasses = "") {

    $('#vehiclesTable').append(
`<div class="row">
  <div class="col-2">
    <a href="#" id="detail_${id}">${label}</a>
  </div>
  <div class="col-10 ${extraColClasses}" id="${id}" style="${style}">
  </div>
</div>`);

     // attach detail handler
    $(`#detail_${id}`).click(function(){ reportDetail(id); return false; });

}

function renderVehicle(vehicle, beginDate, endDate, mode) {

    // get history
    const data = vehicle['data'];

    // nothing to do?
    if (Object.entries(data).length === 0) {
        return;
    }

    // get element
    const element = getOrCreateElement(
        `vehicle_${vehicle['id']}`,
        (id) => {
            createElement(id, vehicle['identifier'], "background-color: #F9F9F9");
        });

    // render progress
    const progress = renderProgress(data, beginDate, endDate, mode);
    // logger.log('debug', 'progress = %s', progress);

    // replace element content
    element.html(progress);

    // activate tooltips
    $('[data-toggle="tooltip"]').tooltip();

}

function renderRuler(beginDate, endDate, offsetMillis = 0) {

    // get element
    const element = getOrCreateElement('ruler', (id) => {
        createElement(id, "", "", "pb-2");
    });

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

function retrieveData(range) {

    // Retrieve vehicles
    return apiClient.httpClient.get('ambulance/')
        .then( response => {

            // retrieve vehicles
            logger.log('debug', "Got vehicle data from API");

            // loop through vehicle records
            const requests = response.data.map( vehicle  => {

                logger.log('debug', 'Adding vehicle %s', vehicle['identifier']);

                // save vehicle
                vehicles[vehicle['id']] = vehicle;
                vehicles[vehicle['id']]['data'] = {};

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

                        // store history
                        vehicles[id]['data'] = {
                            'history': history
                        };

                    }

                }
        ))

}

function segmentHistoryByMode(mode) {

    logger.log('info', 'Segmenting history by %s', mode);

    // add vehicles to table
    for (const vehicle of Object.values(vehicles)) {

        logger.log('info', 'Segmenting history for vehicel %s', vehicle['identifier']);

        // get history
        const data = vehicle['data'];

        console.log(data);
        if (Object.entries(data).length) {

            logger.log('info', 'Got history');

            // segment and store
            const [segments, durations, status, user] = segmentHistory(
                data['history'],
                {
                    'byStatus': mode === 'status',
                    'byUser': mode === 'user'
                }
            );
            vehicle['data']['mode'] = mode;
            vehicle['data']['segments'] = segments;
            vehicle['data']['durations'] = durations;
            vehicle['data']['status'] = status;
            vehicle['data']['user'] = user;

        }

    }

}

function render(mode, beginDate, endDate, offsetMillis = 0) {

    // render ruler
    renderRuler(beginDate, endDate, offsetMillis);

    // add vehicles to page
    for (const vehicle of Object.values(vehicles)) {
        renderVehicle(vehicle, beginDate, endDate, mode);
    }

}

function getTimes(slider, beginDate) {

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

    return [offsetBeginDate, offsetEndDate, beginMillis, endMillis];

}


// initialization function
function init (client) {

    logger.log('info', '> report-vehicle-status.js');

    // set apiClient
    apiClient = client;

    // get parameters
    const urlParams = new URLSearchParams(window.location.search);

    // set beginDate
    const [beginDate, endDate] = validateDateRange(urlParams.get('beginDate'));
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
    }).on('change', function() {

        // get times
        const [offsetBeginDate, offsetEndDate, beginMillis, endMillis] = getTimes(slider, beginDate);

        // set time inputs
        const beginTime = millisToTime(beginMillis);
        let endTime = millisToTime(endMillis);
        if (endTime === "24:00") {
            endTime = "00:00";
        }
        logger.log('debug', 'beginTime = %s, endTime = %s', beginTime, endTime);

        $('#beginTime').val(beginTime);
        $('#endTime').val(endTime);

        // render
        render(mode, offsetBeginDate, offsetEndDate, beginMillis);

    });

    // set connect color
    slider.querySelectorAll('.noUi-connect')[0].classList.add('bg-primary');

    // set range
    const range = beginDate.toISOString() + "," + endDate.toISOString();
    logger.log('debug', 'range = %j', range);

    // mode
    mode = urlParams.get('mode') ? urlParams.get('mode') : $('input[name="mode"]:checked').val();
    logger.log('debug', 'mode = %s', mode);

    $('input[type="radio"][name="mode"]')
        .change( function() {

            // return if no change
            if (this.value === mode)
                return;

            // render
            mode = this.value;

            // get times
            const [offsetBeginDate, offsetEndDate, beginMillis] = getTimes(slider, beginDate);

            // segment history
            segmentHistoryByMode(mode);

            // render
            render(mode, offsetBeginDate, offsetEndDate, beginMillis);

        });

    // retrieve data
    retrieveData(range)
        .then( () => {

            // segment history
            segmentHistoryByMode(mode);

            // render
            render(mode, beginDate, endDate);

            // enable generate report button
            $('#submitButton')
                .prop('disabled', false);

        })
        .catch( (error) => {
            logger.log('error', "'Failed to retrieve vehicles: %s ", error);
        });

}

$(function () {

});
