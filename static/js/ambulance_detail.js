$(document).ready(function() {

 	// Set up map widget
 	options = {
 		map_id: "map",
 		zoom: 12
 	}
 	this.mapWidget = new LeafletPolylineWidget(options);

 	// Retrieve ambulances via AJAX
 	retrieveAmbulances(ambulance_id)
});

function retrieveAmbulances(ambulance_id) {
	$.ajax({
	type: 'GET',
	datatype: "json",
	url: APIBaseUrl + 'ambulance/' + ambulance_id + '/updates',
	
	error: function(msg) {
	    
	    alert('Could not retrieve data from API:' + msg)
	    
	},
	
	success: function(data) {
	    
	    console.log('Got data from API')
	  
	    addAmbulanceRoute(data)

	}
    })
	.done(function( data ) {
	    if ( console && console.log ) {
			console.log( "Done retrieving ambulance data from API" );
	    }
	});
}

// Interact with widget to add an ambulance route
function addAmbulanceRoute(data) {
	var latlngs = [];
	$.each(data, function(i, update) {
		loc = update.location;
		latlngs.push([loc.latitude, loc.longitude]);
	});	
	this.mapWidget.addLine(latlngs, 1, "red");
}