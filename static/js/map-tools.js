import L from "leaflet";
import "leaflet-rotatedmarker";
import "leaflet/dist/leaflet.css";

import {ambulanceStatusIcon, waypointIcon} from "./app-icons";

import { logger } from './logger';

export function calculateDistanceHaversine(location1, location2, radius) {

	radius = radius || 6371e3; // m

	// convert latitude and longitude to radians first
    const lat1 = Math.PI * location1.latitude / 180;
    const lat2 = Math.PI * location2.latitude / 180;
    const d_phi = lat2 - lat1;
    const d_lambda = Math.PI * (location2.longitude - location1.longitude) / 180;

    const a = Math.sin(d_phi / 2) * Math.sin(d_phi / 2) + Math.cos(lat1) * Math.cos(lat2) * Math.sin(d_lambda / 2) * Math.sin(d_lambda / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

    // logger.log('info', ('|| {} - {} ||= {}'.format(location2, location1, earth_radius * c))

    return radius * c;
}

export function calculateSegmentDistanceAndSpeed(segment, movingSpeedThreshold, movingDistanceThreshold) {

	movingSpeedThreshold = movingSpeedThreshold || (5/3.6);    // m/s
	movingDistanceThreshold = movingDistanceThreshold || 5;    // m
    const filterCoefficient = 0.95;

    const eps = 1e-4;

    let totalDistance = 0.0;
    let totalTime= 0.0;
    let totalMovingDistance = 0.0;
    let totalMovingTime= 0.0;
    let maxSpeed = 0.0;
    const distance = [];
    const speed = [];
    const time = [];
    if (segment.length) {

        distance[0] = .0;
        speed[0] = movingSpeedThreshold;
        time[0] = new Date(segment[0].timestamp);

        let lastSpeed = movingSpeedThreshold;
        let lastPosition = segment[0].location;
        let lastTimestamp = Date.parse(segment[0].timestamp);
        for (let i = 1; i < segment.length; i++) {

            const currentPosition = segment[i].location;
            const currentTimestamp = Date.parse(segment[i].timestamp);

            const _time = new Date(segment[i].timestamp);
            const _distance = calculateDistanceHaversine(lastPosition, currentPosition); // meters
            const _duration = Math.abs(currentTimestamp - lastTimestamp) / 1000;         // seconds

            if (_distance < movingDistanceThreshold)
                // not enough movement
                continue;

            totalDistance += _distance;
            totalTime += _duration;

            // regularized velocity to avoid singularities
            let _speed = (_distance * _duration) / (_duration * _duration + eps);      // m/s

            // logger.log('debug', '_speed = %s', _speed);

            // filter speed
            if (filterCoefficient > 0) {
                _speed = (1 - filterCoefficient) * lastSpeed + filterCoefficient * _speed;
            }

            maxSpeed = maxSpeed >= _speed ? maxSpeed : _speed;

            if (_speed > movingSpeedThreshold) {

                distance.push(_distance);
                speed.push(_speed);
                time.push(_time);

                totalMovingDistance += _distance;
                totalMovingTime += _duration;
            }

            lastSpeed = _speed;
            lastPosition = currentPosition;
            lastTimestamp = currentTimestamp;
        }
    }
    return [totalDistance, totalTime, totalMovingDistance, totalMovingTime, maxSpeed, distance, speed, time];
}

export function calculateMotionStatistics(movingSpeedThreshold, movingDistanceThreshold, ...segments) {

    let totalDistance = .0;
    let totalTime = .0;
    let totalMovingDistance = 0.0;
    let totalMovingTime= 0.0;
    let maxSpeed = 0.0;

    const distance = [];
    const speed = [];
    const time = [];

    for (let i = 0; i < segments.length; i++) {

        // calculate length, speed and total length
        const [_totalDistance, _totalTime, _totalMovingDistance, _totalMovingTime,
            _maxSpeed, _distance, _speed, _time] =
            calculateSegmentDistanceAndSpeed(segments[i], movingSpeedThreshold, movingDistanceThreshold);

        // concatenate speed and distance
        distance.push(_distance);
        speed.push(_speed);
        time.push(_time);

        // calculate max speed
        maxSpeed = maxSpeed >= _maxSpeed ? maxSpeed : _maxSpeed;

        logger.log('debug', 'maxSpeed = %s', maxSpeed);

        // accumulate
        totalDistance += _totalDistance;
        totalTime += _totalTime;

        totalMovingDistance += _totalMovingDistance;
        totalMovingTime += _totalMovingTime;

    }

    return [totalDistance, totalTime, totalMovingDistance, totalMovingTime, maxSpeed, distance, speed, time];
}

export function segmentHistory(history, _options = {}) {

    const options =
        Object.assign({
                'separationRadius' :[10, 1000],                  // 10m, 1km
                'timeInterval': [2 * 60 * 1000, 60 * 60 * 1000], // 2 minutes, 1 hour
                'byStatus': false,                               // split by status
                'byUser': false,                                 // split by user
                'reverse': true                                  // traverse in reverse order
            },
            _options);

    const segments = [];
    const durations = [];
    const status = [];
    const user = [];

    let currentSegment = [];
    let lastPosition = null;
    const n = history.length;
    for (let i = 0; i < n; i++) {

		// current position
        const currentPosition = history[options.reverse ? n - i - 1: i];

        // distance?
		if (lastPosition != null) {

            const distance = calculateDistanceHaversine(lastPosition.location, currentPosition.location);          // meters
            const interval = Math.abs(Date.parse(lastPosition.timestamp) - Date.parse(currentPosition.timestamp)); // milliseconds

            // new segment?
            const newSegment =
                distance > options.separationRadius[1] ||
                interval > options.timeInterval[1] ||
                (interval > options.timeInterval[0] && distance > options.separationRadius[0]);

            // new user?
            const newUser = options.byUser && lastPosition.updated_by_username !== currentPosition.updated_by_username;

            // new status?
            const newStatus = options.byStatus && lastPosition.status !== currentPosition.status;

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

export function breakSegments(data, byStatus, separationRadius, timeInterval) {

	separationRadius = separationRadius || [10, 1000]; // 10m, 1km
	timeInterval = timeInterval || [2 * 60, 60 * 60]; // 2 minutes, 1 hour
    byStatus = byStatus || false; // split by status as well?

    const segments = [];

    let currentSegment = [];
    let lastPosition = null;
    const n = data.length;
    for (let i = 0; i < n; i++) {

		// current position
        const currentPosition = data[i];

        // distance?
		if (lastPosition != null) {

            const distance = calculateDistanceHaversine(lastPosition.location, currentPosition.location);                 // meters
            const interval = Math.abs(Date.parse(lastPosition.timestamp) - Date.parse(currentPosition.timestamp)) / 1000; // seconds

            let newStatus = false;
            if (byStatus && lastPosition.status !== currentPosition.status) {
			    newStatus = true;
			    // will break segment, add current position first
                const newCurrentPosition = Object.assign({}, currentPosition);
                newCurrentPosition.status = lastPosition.status;
                currentSegment.push(newCurrentPosition);
            }

			if (newStatus ||
                distance > separationRadius[1] ||
                interval > timeInterval[1] ||
                (interval > timeInterval[0] && distance > separationRadius[0])) {
                // terminate current segment
                segments.push(currentSegment);
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
        segments.push(currentSegment);
    }

	return segments;

}

export function createMarker(call_or_update, icon) {

    // default marker
    icon = icon || new L.divIcon(ambulanceStatusIcon(call_or_update));

    const location = call_or_update.location;
    return L.marker(
        [location.latitude, location.longitude],
        {icon: icon});

}

export function createSegmentLine(map, updates) {

	// Store data in an array
    const latlngs = [];
    updates.forEach(function(update) {

		// push location
        const loc = update.location;
        latlngs.push([loc.latitude, loc.longitude]);

    });

	// Add line to map
	logger.log('debug', 'Adding line segment');
	return L.polyline(latlngs, {color: "red"});

}

// Add call waypoints
export function addCallWaypoints(map, waypoints) {

    // loop through waypoints
    waypoints.forEach( (waypoint) => {

        logger.log('debug', "Adding waypoint type '%s', status '%s'", waypoint.location.type, waypoint.status);

        // waypoint icon
        const icon = new L.divIcon(waypointIcon(waypoint));

        // waypoint label
        let label = location_type[waypoint['location']['type']];
        if (waypoint['location']['name'])
            label += ": " + waypoint['location']['name'];

        // add waypoint markers
        createMarker(waypoint['location'], icon)
            .addTo(map.map)
            .bindPopup("<strong>" + label + "</strong>")
            .on('mouseover',
                function () {
                    // open popup bubble
                    this.openPopup().on('mouseout',
                        function () {
                            this.closePopup();
                        });
                });
    });

}

// Interact with widget to add an ambulance route
export function addAmbulanceRoute(map, data, ambulance_status, byStatus) {

    byStatus = byStatus || false;

    // paginated?
    if ('results' in data) {
        data = data.results
    }

    // short return
    if (data.length === 0)
        return;

    // break segments
    //const segments = breakSegments(data, byStatus);
    const [segments, durations, status, user] = segmentHistory(data, {'byStatus': byStatus});

    // loop on segments
    const n = segments.length;
    let last_segment = null;
    for (let i = 0; i < n; i++) {

	    // grab segment
        const segment = segments[i];

        // initial point
        const initialPoint = segment[0];

        if (i === 0) {

            // add starting marker
            logger.log('debug', "Adding initial '%s' marker", initialPoint.status);
            createMarker(segment[0])
                .addTo(map.map)
                .bindPopup('<strong>' + ambulance_status[initialPoint.status] + '</strong>')
                .on('mouseover',
                    function () {
                        // open popup bubble
                        this.openPopup().on('mouseout',
                            function () {
                                this.closePopup();
                            });
                    });

        } else if (byStatus) { // && i > 0

            const status = initialPoint.status;
            const last_status = last_segment[last_segment.length - 1].status;
            logger.log('debug', "status = '%s', last_status = '%s'", status, last_status);
            if (last_status !== status) {
                // add status marker
                logger.log('debug', "Adding '%s' marker", status);
                createMarker(initialPoint)
                    .addTo(map.map)
                    .bindPopup('<strong>' + ambulance_status[status] + '</strong>')
                    .on('mouseover',
                        function () {
                            // open popup bubble
                            this.openPopup().on('mouseout',
                                function () {
                                    this.closePopup();
                                });
                        });
            }

        }

        // add segment to map
        createSegmentLine(map, segment)
            .addTo(map.map);

        // last segment?
        if (i === n - 1 && segment.length > 0) {
            // add ending marker
            const finalPoint = segment[segment.length - 1];
            logger.log('debug', "Adding final '%s' marker", finalPoint.status);
            createMarker(finalPoint)
                .addTo(map.map)
                .bindPopup('<strong>' + ambulance_status[finalPoint.status] + '</strong>')
                .on('mouseover',
                    function () {
                        // open popup bubble
                        this.openPopup().on('mouseout',
                            function () {
                                this.closePopup();
                            });
                    });
        }

        last_segment = segment;

    }

    // create route filter
    //createRouteFilter(segments);

    logger.log('debug', 'Centering map');
    map.center(data[0].location);

}

export function createRouteFilter(map, segments) {

    // Add the checkbox on the top right corner for filtering.
    const container = L.DomUtil.create('div', 'filter-options bg-light');

    //Generate HTML code for checkboxes for each of the statuses.
    let filterHtml = "";

    filterHtml += '<div class="border border-dark rounded px-1 pt-1 pb-0">';
    segments.forEach(function (segment, index) {

        const date = new Date(Date.parse(segment[0].timestamp));
        filterHtml += '<div class="checkbox">'
            + '<label><input class="chk" data-status="layer_' + index + '" type="checkbox" value="" checked >'
            + date.toLocaleString()
            + '</label>'
            + '</div>';

    });
    filterHtml += "</div>";

    // Append html code to container
    container.innerHTML = filterHtml;

    // Add the checkboxes.
    const customControl = L.Control.extend({

        options: {
            position: 'topright'
        },

        onAdd: function () {
            return container;
        }

    });
    map.map.addControl(new customControl());

    // Add listener to remove status layer when filter checkbox is clicked
    $('.chk').change(function () {

        // Which layer?
        const layer = map.getLayerPane(this.getAttribute('data-status'));

        if (this.checked) {
            layer.style.display = 'block';
        } else {
            layer.style.display = 'none';
        }

    });

};
