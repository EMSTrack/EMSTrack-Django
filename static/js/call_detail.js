function addCallToMap(call, map) {

    console.log('Adding call to map');
    // console.log(call);

    // waypoint markers
    var icon = icon || L.icon({
        iconUrl: '/static/icons/maki/marker-15.svg',
        iconSize: [15, 30],
    });

    // loop through ambulancecall records
    call['ambulancecall_set'].forEach(function (ambulancecall) {

        console.log('Adding ambulancecall');
        // console.log(ambulancecall);

        // loop through waypoints
        ambulancecall['waypoint_set'].forEach(function (waypoint) {

            console.log('Adding waypoint');
            // console.log(waypoint);

            // waypoint label
            var label = location_type[waypoint['location']['type']];
            if (waypoint['location']['name'])
                label += ": " + waypoint['location']['name'];

            // add waypoint markers
            createMarker(waypoint['location'], icon)
                .addTo(map.map)
                .bindPopup("<strong>" + label + "</strong>")
                .on('mouseover',
                    function (e) {
                        // open popup bubble
                        this.openPopup().on('mouseout',
                            function (e) {
                                this.closePopup();
                            });
                    });
        });

        // add ambulance updates
        retrieveAmbulanceUpdates(ambulancecall['ambulance_id'], call['id'], map);

    });

}

function retrieveCall(call_id, map) {

    console.log("Retrieving call '" + call_id + "'from API");

    // Build url
    var url = APIBaseUrl + 'call/' + call_id + '/';

    $.ajax({
        type: 'GET',
        datatype: "json",
        url: url,

        fail: function (msg) {

            alert('Could not retrieve call from API:' + msg);

        },

        success: function (data) {

            console.log("Got call '" + call_id + "'from API");
            addCallToMap(data, map);

        }

    })
        .done(function (data) {
            if (console && console.log) {
                console.log("Done retrieving call '" + call_id + "' from API");
            }
        });

}


function retrieveAmbulanceUpdates(ambulance_id, call_id, map) {

    console.log("Retrieving ambulance '" + ambulance_id + "' from API");

    // Build url
    var url = APIBaseUrl + 'ambulance/' + ambulance_id + '/updates/?call_id=' + call_id;

    $.ajax({
        type: 'GET',
        datatype: "json",
        url: url,

        fail: function (msg) {

            alert('Could not retrieve ambulance updates from API:' + msg);

        },

        success: function (data) {

            console.log("Got '" + data.length + "' ambulance '" + ambulance_id + "' updates from API");
            addAmbulanceRoute(map, data, true);

        }

    })
        .done(function (data) {
            if (console && console.log) {
                console.log("Done retrieving ambulance '" + ambulance_id + "' updates from API");
            }
        });

}

$(function () {

    // Set up map widget
    options = {
        map_id: "map",
        zoom: 12
    }
    var map = new LeafletPolylineWidget(options);

    // Retrieve call
    retrieveCall(call_id, map);

});

