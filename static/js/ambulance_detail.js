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

// Interact with widget to add an ambulance route
function addAmbulanceRoute(data) {

	// Store data in an array
	var latlngs = [];
	var lastStatus = '';
	data.results.forEach(function(update, i, array) {

		// get location
		var loc = update.location;
		latlngs.push([loc.latitude, loc.longitude]);

		// get status
		var status = update.status;
		if ((status != lastStatus) || (i == (array.length - 1))) {

			// add marker
			// TODO: color depending on status

			var marker = map.addPoint(loc.latitude, loc.longitude, update.id, null)
				.bindPopup(status)
				.on('mouseover',
					function(e){
						// open popup bubble
						this.openPopup().on('mouseout',
							function(e){
								this.closePopup();
							});
					});

			// update status
			lastStatus = status;
			console.log('Adding marker, status = ' + status);
		}
	});

	// Add line to map
	console.log('Adding line');
	map.addLine(latlngs, 1, "red", null);

	// Zoom to bounds
	console.log('Fitting bounds');
	map.fitBounds();

}