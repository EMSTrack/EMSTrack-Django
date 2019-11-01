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

let apiClient, mode, slider, detailVehicleId;
const vehicles = {};

// add initialization hook
add_init_function(init);

function trimDataToRange(data, beginDate, endDate) {

    // clone durations
    const segments = data['segments'];
    const durations = [...data['durations']];

    // calculate offsets
    const n = durations.length;
    const offsets = new Array(n);
    let beforeRange = true;
    const totalTime = endDate.getTime() - beginDate.getTime();
    for (let i = 0; i < n; i++) {

        const segment = segments[i];
        const currentOffset = (new Date(segment[0].timestamp)).getTime() - beginDate.getTime();
        offsets[i] = currentOffset;

        if (beforeRange && currentOffset >= 0) {
            // this is the first segment in range
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

    return [durations, offsets, totalTime];
}

function renderProgress(data, beginDate, endDate, mode) {

    console.log(data);

    let values;
    if (mode === 'status')
        values = data['status'];
    else if (mode === 'user')
        values = data['user'];
    else
        throw "Unknown mode '" + mode + "'";

    const [durations, offsets, totalTime] = trimDataToRange(data, beginDate, endDate);

    // build progress bar
    let cursor = 0;
    let progress = '<div class="progress" style="height: 20px;">\n';
    const n = durations.length;
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

// render detail
function renderDetailReport(vehicle, beginDate, offsetMillis = 0) {

    const data = vehicle['data'];

    // get times
    const [offsetBeginDate, offsetEndDate] = getTimes(slider, beginDate, offsetMillis);

    logger.log('debug', 'got times data');

    // trim to range
    const [durations, offsets, totalTime] = trimDataToRange(data, offsetBeginDate, offsetEndDate);

    logger.log('debug', 'got trimmed data');

    // get values
    let values;
    if (mode === 'status')
        values = data['status'];
    else if (mode === 'user')
        values = data['user'];
    else
        throw "Unknown mode '" + mode + "'";

    // summarize
    const n = durations.length;
    let numberOfSegments = 0;
    let totalDuration = 0;
    const typesOfValues = {};
    for (let i = 0; i < n; i++) {

        const currentOffset = offsets[i];

        // not in range yet
        if (currentOffset < 0)
            continue;

        // out of range, break
        if (currentOffset > totalTime)
            break;

        const currentValue = values[i];
        const currentDuration= durations[i];

        numberOfSegments++;
        totalDuration += currentDuration;

        if (currentValue in typesOfValues) {
            typesOfValues[currentValue]['count']++;
            typesOfValues[currentValue]['duration'] += currentDuration;
        } else {
            typesOfValues[currentValue] = {
                count: 0,
                duration: 0
            };
        }

    }

    logger.log('debug', 'will render summary');

    let reportByActivity = `
<table class="table table-striped table-sm>
  <thead>
    <tr>
      <th></th>
      <th>Segments</th>
      <th>Duration (hours)</th>
      <th>Percentage (%)</th>
    </tr>
  </thead>
  <tbody>
`;

    for (let [key, value] of Object.entries(typesOfValues)) {
        reportByActivity += `
    <tr>
      <td>${key}</td>
      <td>${value['count']}</td>
      <td>${(value['duration'] / 1000 / 60 / 60).toFixed(2)}</td>
      <td>${(100*value['duration']/totalTime).toFixed(1)}%</td>
    </tr>>`;
    };

    reportByActivity = `    
  </tbody>
</table>`;

    console.log(reportByActivity);

    $('#detail_summary')
        .html(`
<h2>Summary</h2>
<div class="row">
  <div class="col col-2 text-right">
     Number of Segments:
  </div>
  <div class="col col">
     ${numberOfSegments}
  </div>
</div>
<div class="row">
  <div class="col col-2 text-right">
     Time interval:
  </div>
  <div class="col col">
     ${(totalTime / 1000 / 60 / 60).toFixed(2)} hours
  </div>
</div>
<div class="row">
  <div class="col col-2 text-right">
     Total active time:
  </div>
  <div class="col col">
     ${(totalDuration / 1000 / 60 / 60).toFixed(2)} hours (${(100*totalDuration/totalTime).toFixed(1)}%)
  </div>
</div>
<h2>By ${mode === 'status' ? 'Status' : 'User' }</h2>
${reportByActivity}
`);

}

// report detail
function reportDetail(id, beginDate) {

    logger.log('info', "Generating detail report for id '%s'", id);

    const vehicle = vehicles[id];

    // get detail element information
    const detailElement = $('#detail');
    const isDetailVisible = detailElement.is( ":visible" );

    const idElement = $('#detail_id');
    const currentId = idElement.text();

    if (isDetailVisible) {

        logger.log('debug', "detail is visible, current id is '%s'", currentId);

        if (currentId === vehicle['identifier']) {

            logger.log('debug', "hiding detail");

            // same vehicle, collapse and return
            detailElement.collapse('hide');
            detailVehicleId = -1;

            return;

        }

        // otherwise, this is another element, go ahead

    } else {

        // not visible, set it up and display

        logger.log('debug', "detail is not visible, current id is '%s'", currentId);

    }

    // setup detail
    logger.log('debug', "setting up detail");

    // set detailVehicle
    detailVehicleId = vehicle['id'];

    // set new detail title
    idElement.text(vehicle['identifier']);

    // render detail report
    renderDetailReport(vehicle, beginDate);

    logger.log('debug', "showing...");
    detailElement.collapse('show');

}

function createElement(elementId, id, beginDate, label, style = "", extraColClasses = "") {

    logger.log('debug', 'creating element with id = %d, label = %s', elementId, label);

    $('#vehiclesTable').append(
`<div class="row">
  <div class="col-2">
    <a href="#" id="detail_${elementId}">${label}</a>
  </div>
  <div class="col-10 ${extraColClasses}" id="${elementId}" style="${style}">
  </div>
</div>`);

    if (id >= 0) {
        // attach detail handler
        $(`#detail_${elementId}`).click(function () {
            reportDetail(id, beginDate);
            return false;
        });
    }

}

function renderVehicle(vehicle, beginDate, endDate, mode) {

    // get history
    const data = vehicle['data'];

    // nothing to do?
    if (Object.entries(data).length === 0) {
        return;
    }

    // get element
    const id = vehicle['id'];
    const element = getOrCreateElement(
        `vehicle_${id}`,
        (elementId) => {
            createElement(elementId, id, beginDate, vehicle['identifier'], "background-color: #F9F9F9");
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
    const element = getOrCreateElement('ruler', (elementId) => {
        createElement(elementId, -1, beginDate, "", "", "pb-2");
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

    // has detail?
    if (detailVehicleId >=0) {
        renderDetailReport(vehicles[detailVehicleId], beginDate, offsetMillis);
    }

}

function getTimes(slider, beginDate, offsetMillis = 0) {

    const [begin, end] = slider.noUiSlider.get();
    logger.log('info', 'begin = %s, end = %s', begin, end);

    // offset beginDate
    const offsetBeginDate = new Date(beginDate);
    const beginMillis = Number.parseFloat(begin) * 60 * 60 * 1000 - offsetMillis;
    offsetBeginDate.setTime(offsetBeginDate.getTime() + beginMillis);

    const offsetEndDate = new Date(beginDate);
    const endMillis = Number.parseFloat(end) * 60 * 60 * 1000 - offsetMillis;
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
    slider = document.getElementById('slider-range');
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

            // Update please wait message
            const pleaseWait = $('#pleaseWait');
            pleaseWait.text("Generating report...");

            // segment history
            segmentHistoryByMode(mode);

            // render
            render(mode, beginDate, endDate);

            // enable generate report button
            $('#submitButton')
                .prop('disabled', false);

            // hide please wait sign
            pleaseWait.hide();

        })
        .catch( (error) => {
            logger.log('error', "'Failed to retrieve vehicles: %s ", error);
        });

}

$(function () {

});
