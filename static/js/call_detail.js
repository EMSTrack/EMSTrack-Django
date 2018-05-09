var map;
var page;
$(function() {

 	// Set up map widget
 	options = {
 		map_id: "map",
 		zoom: 12
 	}
 	map = new LeafletPolylineWidget(options);

 	// get page and page_size parameters
	var searchParams = new URLSearchParams(window.location.search)
	if (searchParams.has('page'))
        page = searchParams.get('page');
	if (searchParams.has('page_size'))
        page_size = searchParams.get('page_size');

 	// Retrieve ambulances via AJAX
 	// retrieveAmbulances(ambulance_id)

});

function retrieveAmbulances(ambulance_id) {

	// Build url
	var url = APIBaseUrl + 'ambulance/' + ambulance_id + '/updates';
	if (page != null) {
        url += "?page=" + page;
        if (page_size != null)
            url += "&page_size=" + page_size;
    } else if (page_size != null)
            url += "?page_size=" + page_size;

    $.ajax({
        type: 'GET',
        datatype: "json",
        url: url,

        fail: function (msg) {

            alert('Could not retrieve data from API:' + msg)

        },

        success: function (data) {

            console.log('Got data from API')

            addAmbulanceRoute(data)

        }

    })
        .done(function (data) {
            if (console && console.log) {
                console.log("Done retrieving ambulance data from API");
            }
        });

}

function addMarker(map, update, layer) {

	// add marker
	map.addPoint(update.location.latitude, update.location.longitude, update.id, null, layer)
		.bindPopup('<strong>' + ambulance_status[update.status] + '</strong><br/>@'
            + (new Date(Date.parse(update.timestamp))).toLocaleString())
		.on('mouseover',
			function(e){
				// open popup bubble
				this.openPopup().on('mouseout',
					function(e){
						this.closePopup();
					});
			});

}

function calculateDistanceHaversine(location1, location2, radius) {

	radius = radius || 6371e3;

	// convert latitude and longitude to radians first
    var lat1 = Math.PI * location1.latitude / 180;
    var lat2 = Math.PI * location2.latitude / 180;
    var d_phi = lat2 - lat1;
    var d_lambda = Math.PI * (location2.longitude - location1.longitude) / 180;

    var a = Math.sin(d_phi / 2) * Math.sin(d_phi / 2) + Math.cos(lat1) * Math.cos(lat2) * Math.sin(d_lambda / 2) * Math.sin(d_lambda / 2);
    var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

    // console.log('|| {} - {} ||= {}'.format(location2, location1, earth_radius * c))

    return radius * c;
}

function breakSegments(data, separationRadius, timeInterval) {

	separationRadius = separationRadius || [100, 10000]; // 10m, 10km
	timeInterval = timeInterval || [2 * 60 * 1000, 60 * 60 * 1000]; // 2 minutes, 1 hour

	var segments = [];

	var currentSegment = [];
	var lastPosition = null;
	var n = data.length;
	for (var i = 0; i < n; i++) {

		// current position
		var currentPosition = data[i];

		// distance?
		if (lastPosition != null) {
			var distance = calculateDistanceHaversine(lastPosition.location, currentPosition.location);
			var interval = Math.abs(Date.parse(lastPosition.timestamp) - Date.parse(currentPosition.timestamp));
			if (distance > separationRadius[1] || interval > timeInterval[1] ||
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

function addSegment(updates, layer) {

	// Add status markers
	// TODO: color depending on status

    // Create layer
    map.createLayer(layer);

	// First entry
	var lastStatus;
	if (updates.length >= 2) {

		// Retrieve last entry (first position)
		entry = updates[updates.length - 1];

		// add marker
		addMarker(map, entry, layer);

		// entry status
		lastStatus = entry.status;

	}

	// Mid updates
	for (var i = updates.length - 2; i > 0; i--) {

		// Retrieve next entry
		entry = updates[i];

		if (entry.status != lastStatus) {

            // add marker
            addMarker(map, entry, layer);

        }

		// entry status
		lastStatus = entry.status;

	}

	// Last entry
	if (updates.length > 0) {

		// Retrieve last entry (first position)
		entry = updates[0];

		// add marker
		addMarker(map, entry, layer);

	}

	// Store data in an array
	var latlngs = [];
	updates.forEach(function(update) {

		// push location
		var loc = update.location;
		latlngs.push([loc.latitude, loc.longitude]);

    });

	// Add line to map
	console.log('Adding segment');
	map.addLine(latlngs, 1, "red", null, layer);

}

// Interact with widget to add an ambulance route
function addAmbulanceRoute(data) {

    // short return
    if (data.results.length == 0)
        return;

    // break segments
    var segments = breakSegments(data.results);

    // loop on segments
    segments.forEach( function(segment, index) {

        // add segment to map
        addSegment(segment, 'layer_' + index);

    });

    // create route filter
    createRouteFilter(segments);

    console.log('Centering map');
    map.center(data.results[0].location);

}

function createRouteFilter(segments) {

    // Add the checkbox on the top right corner for filtering.
    var container = L.DomUtil.create('div', 'filter-options bg-light');

    //Generate HTML code for checkboxes for each of the statuses.
    var filterHtml = "";

    filterHtml += '<div class="border border-dark rounded px-1 pt-1 pb-0">';
    segments.forEach(function (segment, index) {

        var date = new Date(Date.parse(segment[0].timestamp));
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
    var customControl = L.Control.extend({

        options: {
            position: 'topright'
        },

        onAdd: function (map) {
            return container;
        }

    });
    map.map.addControl(new customControl());

    // Add listener to remove status layer when filter checkbox is clicked
    $('.chk').change(function () {

        // Which layer?
        var layer = map.getLayerPane(this.getAttribute('data-status'));

        if (this.checked) {
            layer.style.display = 'block';
        } else {
            layer.style.display = 'none';
        }

    });

};
