var map;

$(function () {

    // Set up map widget
    options = {
        map_id: "map",
        zoom: 12
    }
    map = new LeafletPolylineWidget(options);

    // patient marker
    var icon = icon || L.icon({
        iconUrl: '/static/icons/maki/marker-15.svg',
        iconSize: [15, 30],
    });

    // add patient marker
    createMarker(call, icon)
        .addTo(map.map)
        .bindPopup('<strong>hi</strong>')
        .on('mouseover',
            function (e) {
                // open popup bubble
                this.openPopup().on('mouseout',
                    function (e) {
                        this.closePopup();
                    });
            });

    // add segments
    if (call.status == "Started" || call.status == "Ended") {
        
        // Gotta separate these. Started => live updates
        ambulances.forEach(id => { retrieveAmbulances(id); });

    } else
        console.error("Call status " + call.status + " not handled");

});

function retrieveAmbulances(ambulance_id) {

    // Build url
    var url = APIBaseUrl + 'ambulance/' + ambulance_id + '/updates/?call_id=' +_call.id;

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
