function addCallToMap(call, map) {

    console.log('Adding call to map');
    console.log(call);

    // waypoint markers
    var icon = icon || L.icon({
        iconUrl: '/static/icons/maki/marker-15.svg',
        iconSize: [15, 30],
    });

    // loop through ambulancecall records
    call['ambulancecall_set'].forEach(function(ambulancecall) {

        console.log(ambulancecall);

        // loop through waypoints
        ambulancecall['waypoint_set'].forEach(function(waypoint) {

            console.log(waypoint);

            // add waypoint markers
            createMarker(waypoint, icon)
                .addTo(map.map)
                .bindPopup("<strong>" + waypoint['type'] + "</strong>")
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

        if (call['status'] === "S" || call.status === "E") {

            // Gotta separate these. Started => live updates
            retrieveAmbulanceUpdates(ambulancecall['ambulance_id'], map);

        } else
            console.error("Call status " + call.status + " not handled");

    });

}

function retrieveCall(call_id, map) {

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

            console.log('Got call from API');
            addCallToMap(data, map);

        }

    })
        .done(function (data) {
            if (console && console.log) {
                console.log("Done retrieving call data from API");
            }
        });

}


function retrieveAmbulanceUpdates(ambulance_id, map) {

    // Build url
    var url = APIBaseUrl + 'ambulance/' + ambulance_id + '/updates/?call_id=' + call.id;

    $.ajax({
        type: 'GET',
        datatype: "json",
        url: url,

        fail: function (msg) {

            alert('Could not retrieve ambulance updates from API:' + msg);

        },

        success: function (data) {

            console.log('Got ambulance updates from API');

            addAmbulanceRoute(map, data, true);

        }

    })
        .done(function (data) {
            if (console && console.log) {
                console.log("Done retrieving ambulance updates from API");
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

