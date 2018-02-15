$(document).ready(function() {
	// Set map view
    mymap = L.map('live-map').setView([32.5149, -117.0382], 12);

    // Add layer to map.
    L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token=pk.eyJ1IjoieWFuZ2Y5NiIsImEiOiJjaXltYTNmbTcwMDJzMzNwZnpzM3Z6ZW9kIn0.gjEwLiCIbYhVFUGud9B56w', {
	attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="http://mapbox.com">Mapbox</a>',
	maxZoom: 22,
	id: 'mapbox.streets',
	accessToken: 'pk.eyJ1IjoieWFuZ2Y5NiIsImEiOiJjaXltYTNmbTcwMDJzMzNwZnpzM3Z6ZW9kIn0.gjEwLiCIbYhVFUGud9B56w'
    }).addTo(mymap);

    console.log(ambulance_id);
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
	    
	    showAmbulanceRoute(data)
	}
    })
	.done(function( data ) {
	    if ( console && console.log ) {
			console.log( "Done retrieving ambulance data from API" );
	    }
	});
}

function showAmbulanceRoute(data) {
	console.log(data)
}