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

export function validateDateRange(beginDate, endDate) {

    // beginDate
    if (beginDate === null) {
        beginDate = new Date();
        beginDate.setHours(0, 0, 0, 0);
    } else
        beginDate = new Date(beginDate);

    // minDate
    let minDate = new Date();
    minDate.setDate(beginDate.getDate() + 1);
    minDate.setHours(0, 0, 0, 0);

    // endDate
    if (endDate === null) {
        endDate = minDate;
    } else {
        endDate = new Date(endDate);
    }

    // make sure endDate > beginDate
    if (endDate <= beginDate) {
        endDate = new Date(minDate);
    }

    logger.log('debug', 'beginDate = %s, endDate = %s, minDate = %s', beginDate, endDate, minDate);

    return [beginDate, endDate, minDate];
}