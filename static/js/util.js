import {logger} from "./logger";

export function swapElements(a, b) {
    a = $(a); b = $(b);
    var tmp = $('<span>').hide();
    a.before(tmp);
    b.before(a);
    tmp.replaceWith(b);
};

export function timeSplit(time, defaultTime = [0,0,0,0]) {
    if (time == null || typeof time === 'undefined' || time === "")
        return defaultTime;
    const terms = time.split(':');
    const hours = Number.parseInt(terms[0]);
    const minutes = terms.length > 1 ? Number.parseInt(terms[1]) : defaultTime[1];
    let seconds = defaultTime[2];
    let milliseconds = defaultTime[3];
    if (terms.length > 2) {
        const seconds_terms = time.split('.');
        seconds = Number.parseInt(seconds_terms[0]);
        if (seconds_terms.length > 1)
            milliseconds = Number.parseInt(seconds_terms[1]);
    }

    return [hours, minutes, seconds, milliseconds];
}

export function timeMerge(hours, minutes, seconds, milliseconds) {
    return String(hours).padStart(2, '0') + ':' + String(minutes).padStart(2, '0') + ':' +
        String(seconds).padStart(2, '0') + '.' + String(milliseconds).padStart(3, '0');
}

export function timeToMillis(time, defaultTime = [0,0,0,0]) {
    const [hours, minutes, seconds, milliseconds] = timeSplit(time, defaultTime);
    return 1000 * (60 * (60 * hours + minutes) + seconds) + milliseconds;
}

export function splitTimeToMillis(hours, minutes, seconds, milliseconds) {
    return 1000 * (60 * (60 * hours + minutes) + seconds) + milliseconds;
}

export function millisToSplitTime(millis) {
    const milliseconds = millis % 1000;
    millis = (millis - milliseconds) / 1000;
    const seconds = millis % 60;
    millis = (millis - seconds) / 60;
    const minutes = millis % 60;
    const hours = (millis - minutes) / 60;
    return [hours, minutes, seconds, milliseconds];
}

export function millisToTime(millis) {
    const [hours, minutes, seconds, milliseconds] = millisToSplitTime(millis);
    if (milliseconds > 0)
        return String(hours).padStart(2, '0') + ':' + String(minutes).padStart(2, '0') + ':' +
            String(seconds).padStart(2, '0') + '.' + String(milliseconds).padStart(3, '0');
    else if (seconds > 0)
        return String(hours).padStart(2, '0') + ':' + String(minutes).padStart(2, '0') + ':' +
            String(seconds).padStart(2, '0');
    else
        return String(hours).padStart(2, '0') + ':' + String(minutes).padStart(2, '0');
}

export function validateDateRange(beginDate, endDate) {

    logger.log('debug', 'beginDate = %s, endDate = %s', beginDate, endDate);

    // beginDate
    if (beginDate === null || typeof beginDate === 'undefined') {
        beginDate = new Date();
    } else
        beginDate = new Date(beginDate);
    beginDate.setHours(0, 0, 0, 0);

    // minDate
    let minDate = new Date();
    minDate.setTime(beginDate.getTime() + 24 * 60 * 60 * 1000);

    logger.log('debug', 'beginDate = %s, endDate = %s, minDate = %s', beginDate, endDate, minDate);

    // endDate
    if (endDate === null || typeof endDate === 'undefined') {
        logger.log('debug', 'no enddate');
        endDate = new Date(minDate);
    } else {
        logger.log('debug', 'got enddate');
        endDate = new Date(endDate);
        endDate.setHours(0, 0, 0, 0);
    }

    logger.log('debug', 'beginDate = %s, endDate = %s, minDate = %s', beginDate, endDate, minDate);

    // make sure endDate > beginDate
    if (endDate <= beginDate) {
        endDate = new Date(minDate);
        endDate.setHours(0, 0, 0, 0);
    }

    logger.log('debug', 'beginDate = %s, endDate = %s, minDate = %s', beginDate, endDate, minDate);

    return [beginDate, endDate, minDate];
}

export function getOrCreateElement(elementId, create) {

    // get element
    const selector = `#${elementId}`;
    let element = $(selector);
    if (element.length === 0) {

        try {
            // create element first
            create(elementId);

        } catch(error) {
            throw "Could not create element! Error: " + error;
        }

        // assign created element
        element = $(selector);

        if (element.length === 0) {
            throw "Could not retrieve created element!";
        }
    }

    return element;
}