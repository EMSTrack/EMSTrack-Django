var map;
$(document).ready(function() {

 	// Set up map widget
 	options = {
 		map_id: "map",
 		zoom: 12
 	}
 	map = new LeafletPolylineWidget(options);

 	// Retrieve ambulances via AJAX
 	retrieveAmbulances(ambulance_id)

});

function retrieveAmbulances(ambulance_id) {

    $.ajax({
        type: 'GET',
        datatype: "json",
        url: APIBaseUrl + 'ambulance/' + ambulance_id + '/updates',

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

function addMarker(map, update) {

	// add marker
	map.addPoint(update.location.latitude, update.location.longitude, update.id, null)
		.bindPopup('<strong>' + ambulance_status[status] + '</strong><br/>@' + update.timestamp)
		.on('mouseover',
			function(e){
				// open popup bubble
				this.openPopup().on('mouseout',
					function(e){
						this.closePopup();
					});
			});
};

// Interact with widget to add an ambulance route
function addAmbulanceRoute(data) {

	// Add status markers
	// TODO: color depending on status

	// First update
	var lastStatus;
	if (data.length >= 2) {

		// Retrieve last update (first position)
		update = data[data.length - 1];

		// add marker
		addMarker(map, update);

		// update status
		lastStatus = update.status;

	}

	// Mid updates
	for (var i = data.length - 2; i > 0; i--) {

		// Retrieve next update
		update = data[i];

		if (update.status != lastStatus) {

            // add marker
            addMarker(map, update);

        }

		// update status
		lastStatus = update.status;

	}

	// Last update
	if (data.length > 0) {

		// Retrieve last update (first position)
		update = data[0];

		// add marker
		addMarker(map, update);

	}

	// Store data in an array
	var latlngs = [];
	data.results.forEach(function(update) {

		// push location
		var loc = update.location;
		latlngs.push([loc.latitude, loc.longitude]);

    });

	// Add line to map
	console.log('Adding line');
	map.addLine(latlngs, 1, "red", null);

	// Zoom to bounds
	console.log('Fitting bounds');
	map.fitBounds();

}