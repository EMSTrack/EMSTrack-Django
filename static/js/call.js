import L from "leaflet";
import "leaflet-rotatedmarker";
import "leaflet/dist/leaflet.css";

import { LeafletPolylineWidget } from "./leaflet/LeafletWidget";

import { addAmbulanceRoute, createMarker } from "./map-tools";

let map;
let apiClient;

// add initialization hook
add_init_function(init);

// initialization function
function init (client) {

    console.log('> ambulance.js');

    // set apiClient
    apiClient = client;

    // Retrieve call
    retrieveCall(call_id, map);

}

$(function () {

    // Set up map widget
    const options = {
        map_id: "map",
        zoom: 12,
        map_provider: map_provider
    };

    map = new LeafletPolylineWidget(options);

});

function retrieveCall(call_id, map) {

    // Build url
    const url = 'call/' + call_id + '/?exclude=';

    apiClient.httpClient.get(url)
        .then( (response) => {

            console.log("Got call data from API");
            addCallToMap(response.data, map);

        })
        .catch( (error) => {
            console.log('Failed to retrieve call data');
            console.log(error);
        });

}

function retrieveAmbulanceUpdates(ambulance_id, call_id, map) {

    console.log("Retrieving ambulance '" + ambulance_id + "' updates from API");

    // Build url
    const url = 'ambulance/' + ambulance_id + '/updates/?call_id=' + call_id;

    apiClient.httpClient.get(url)
        .then( (response) => {

            console.log("Got '" + response.data.length + "' ambulance '" + ambulance_id + "' updates from API");
            addAmbulanceRoute(map, response.data, true);

        })
        .catch( (error) => {
            console.log("'Failed to retrieve ambulance '" + ambulance_id + "' updates");
            console.log(error);
        });

}

function addCallToMap(call, map, icon) {

    console.log('Adding call to map');
    // console.log(call);

    // waypoint markers
    icon = icon || L.icon({
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

        // add ambulance updates
        retrieveAmbulanceUpdates(ambulancecall['ambulance_id'], call['id'], map);

    });

}
