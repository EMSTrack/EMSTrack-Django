import moment from 'moment';

import noUiSlider from 'nouislider';
import 'nouislider/distribute/nouislider.css';

import {logger} from './logger';

import {ReadPages} from './components/pagination';

import {
    getOrCreateElement,
    millisToSplitTime,
    millisToTime,
    splitTimeToMillis,
    validateDateRange
} from "./util";

import {segmentHistory} from "./map-tools";

let apiClient, mode, slider, detailVehicleId = -1;
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
    const totalTime = endDate.valueOf() - beginDate.valueOf();
    for (let i = 0; i < n; i++) {

        const segment = segments[i];
        const currentOffset = (moment(segment[0].timestamp).valueOf() - beginDate.valueOf());
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

    logger.log('debug', 'done progress for vehicle');

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
                count: 1,
                duration: currentDuration
            };
        }

    }

    logger.log('debug', 'will render summary');

    let summaryHtml = `
<table class="table table-striped table-sm">
  <thead>
    <tr>
      <th></th>
      <th>Segments</th>
      <th>Duration (hours)</th>
      <th>Active Percentage (%)</th>
      <th>Percentage (%)</th>
      <th>Color</th>
    </tr>
  </thead>
  <tbody>`;

    for (let [key, value] of Object.entries(typesOfValues)) {
        summaryHtml += `
    <tr>
      <td>${mode === 'status' ? ambulance_status[key] : key}</td>
      <td>${value['count']}</td>
      <td>${(value['duration'] / 1000 / 60 / 60).toFixed(2)}</td>
      <td>${(100 * value['duration'] / totalDuration).toFixed(1)}%</td>
      <td>${(100 * value['duration'] / totalTime).toFixed(1)}%</td>
      <td class="bg-${mode === 'status' ? ambulance_css[key]['class'] : 'primary'}"></td>
    </tr>`;
    };

    if (Object.entries(typesOfValues).length === 0) {

        // no activity message
        summaryHtml += `
    <tr>
      <td colspan="6">No activity recorded in this period</td>
    </tr>`;

    } else {

        // total footer
        summaryHtml += `
    <tfoot>
      <th>Totals</th>
      <td>${numberOfSegments}</td>
      <td>${(totalDuration / 1000 / 60 / 60).toFixed(2)}</td>
      <td>100.0%</td>
      <td>${(100 * totalDuration / totalTime).toFixed(1)}%</td>
      <td></td>
    </tfoot>`;

    }

    summaryHtml += `    
  </tbody>
</table>`;

    console.log(summaryHtml);

    $('#detail_summary')
        .html(summaryHtml);

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

function createElement(elementId, id, beginDate = moment(), label = "", style = "", extraColClasses = "") {
    logger.log('debug', "creating element with id = %s, label = '%s'", elementId, label);

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
        logger.log('info', "vehicle '%s' has no activity", vehicle['id']);
        return false;
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

    return true;
}

function renderRuler(beginDate, endDate, offsetMillis = 0) {

    // get element
    const element = getOrCreateElement('ruler', (elementId) => {
        createElement(elementId, -1, beginDate, "", "", "pb-2");
    });

    // add time scale to table
    let progress = '<div class="progress" style="height: 20px;">\n';
    const totalTime = endDate.valueOf() - beginDate.valueOf();

    // const [hours, minutes, seconds, milliseconds] = millisToSplitTime(offsetMillis);
    const nextHourMillis = splitTimeToMillis(Math.ceil(offsetMillis / 1000 / 60 / 60), 0, 0, 0);
    const [offsetHour, minutes, seconds, milliseconds] = millisToSplitTime(nextHourMillis);

    logger.log('debug', 'totalTime = %s, offsetHour = %s:%s:%s.%s, nextHourMillis = %s',
        totalTime, offsetHour, minutes, seconds, milliseconds, nextHourMillis);

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

class ReadVehiclePages extends ReadPages {

    constructor(vehicle, callback, apiClient, url, page_size = 1000) {
        // call super
        super(apiClient, url, page_size);

        this.vehicle = vehicle;
        this.callback = callback;
    }

    afterPage(result) {

        // update message
        $('#pleaseWaitVehicle').text(`${this.vehicle['identifier']}, page ${this.page} of ${this.totalPages}`);

    }

    afterAllPages() {

        logger.log('debug', "Got '%s' updates for vehicle '%s' from API",
            this.results.length, this.vehicle['identifier']);

        if (this.results.length) {

            // get id
            const id = this.vehicle['id'];

            // store history
            vehicles[id]['data'] = {
                'history': this.results
            };

        }

        if (this.callback)
            this.callback();

    }

}

function retrieveVehicles(data, range, beginDate, endDate, index=0) {

    if (index === data.length) {

        // no more vehicles, produce report
        logger.log('debug', 'Generating report...');

        // Update please wait message
        $('#pleaseWaitMessage')
            .text("Generating report...");

        // segment history
        segmentHistoryByMode(mode);

        // render
        render(mode, beginDate, endDate);

        // enable generate report button
        $('#submitButton')
            .prop('disabled', false);

        // hide please wait sign
        $('#pleaseWait')
            .hide();

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
    const url = `ambulance/${vehicle['id']}/updates/?filter=${range}`;
    new ReadVehiclePages(vehicle, function() {
            retrieveVehicles(data, range, beginDate, endDate, index+1)
        },
        apiClient, url)
        .getPages();

}

function retrieveData(range, beginDate, endDate) {

    // disable generate report button
    $('#submitButton')
        .prop('disabled', true);

    // show retrieving data message
    $('#pleaseWaitMessage')
        .text('Retrieving data...');

    // show please wait sign
    $('#pleaseWait')
        .show();

    // clear vehicles table
    $('#vehiclesTable')
        .empty();

    // Retrieve vehicles
    return apiClient.httpClient.get('ambulance/')
        .then( response => {

            // retrieve vehicles
            logger.log('debug', "Got vehicle data from API");

            // loop through vehicle records
            retrieveVehicles(response.data, range, beginDate, endDate);

        });

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

    logger.log('debug', 'mode = %s, beginDate = %s, endDate = %s, offesetMillis = %d',
        mode, beginDate, endDate, offsetMillis);

    // render ruler
    renderRuler(beginDate, endDate, offsetMillis);

    // add vehicles to page
    let someVehicle = false;
    for (const vehicle of Object.values(vehicles)) {
        logger.log('debug', 'will render vehicle %s', vehicle['identifier']);
        someVehicle = renderVehicle(vehicle, beginDate, endDate, mode) || someVehicle;
    }

    if (!someVehicle) {
        // no activity message
        const element = getOrCreateElement('no_activity', (elementId) => {
            createElement(elementId, -1);
        });
        element.html('<p>No activity recorded in this period</p>');
    }

    // has detail?
    if (detailVehicleId >=0) {
        renderDetailReport(vehicles[detailVehicleId], beginDate, offsetMillis);
    }

}

function getTimes(slider, beginDate, offsetMillis = 0) {

    logger.log('debug', 'beginDate = %s, offsetMillis = %s', beginDate, offsetMillis);

    const [begin, end] = slider.noUiSlider.get();
    logger.log('info', 'begin = %s, end = %s', begin, end);

    // offset beginDate
    const offsetBeginDate = moment(beginDate);
    const beginMillis = Number.parseFloat(begin) * 60 * 60 * 1000 - offsetMillis;
    offsetBeginDate.add(beginMillis, 'milliseconds');

    const offsetEndDate = moment(beginDate);
    const endMillis = Number.parseFloat(end) * 60 * 60 * 1000 - offsetMillis;
    offsetEndDate.add(endMillis, 'milliseconds');

    logger.log('debug', 'offsetBeginDate = %s, offsetEndDate = %s', offsetBeginDate, offsetEndDate);

    return [offsetBeginDate, offsetEndDate, beginMillis, endMillis];

}


// initialization function
function init (client) {

    logger.log('info', '> report-vehicle-activity.js');

    // set apiClient
    apiClient = client;

    // get parameters
    const urlParams = new URLSearchParams(window.location.search);

    // set beginDate
    const [beginDate, endDate] = validateDateRange(urlParams.get('beginDate'));
    logger.log('debug', 'beginDate = %s, endDate = %s', beginDate, endDate);

    const beginTime = beginDate.format('HH:mm:ss');
    const endTime = endDate.format('HH:mm:ss');
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

        const beginDateElement = $('#beginDate');
        const beginDate = moment(beginDateElement.val(), 'YYYY-MM-DD');
        logger.log('debug', 'beginDate = %s', beginDate);

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

    $('#submitButton')
        .click(() => {

            const beginDateElement = $('#beginDate');
            const beginDate = moment(beginDateElement.val(), 'YYYY-MM-DD');
            logger.log('debug', 'beginDate = %s', beginDate);

            const [_beginDate, _endDate] = validateDateRange(beginDate);
            logger.log('debug', 'beginDate = %s, endDate = %s', _beginDate, _endDate);

            // set range
            const range = _beginDate.toISOString() + "," + _endDate.toISOString();
            logger.log('debug', 'range = %j', range);

            // retrieve data
            retrieveData(range, _beginDate, _endDate)
                .catch((error) => {
                    logger.log('error', "'Failed to retrieve vehicles: %s ", error);
                })

        });

}

$(function () {

});
