// LeafletWidget

var LeafletWidget = function (options) {

    this.options = {
        url: 'https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token=pk.eyJ1IjoibWNkZW9saXZlaXJhIiwiYSI6ImNpcWR0NncxdjAyeGRmcm0xdzJ4cGlxMHgifQ.ZkRNtM3-u0mXthxqCVwjtQ',
        options: {
            attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="http://mapbox.com">Mapbox</a>',
            maxZoom: 18,
            id: 'mapbox.streets'
        },

        lat: 32.53530431898372,
        lng: -116.9165934003241,
        zoom: 15,
        location_icon_url: '/static/icons/pin/blue.svg',
        location_icon_size: [32, 32],
        add_marker_control: false,
    };

    // Altering using user-provided options
    for (var property in options) {
        if (options.hasOwnProperty(property)) {
            this.options[property] = options[property];
        }
    }

    // create map
    this.map = L.map(this.options.map_id).setView(L.latLng(this.options.lat,
        this.options.lng),
        this.options.zoom);
    // add reference to parent object
    this.map.parent = this;

    // create title layer
    L.tileLayer(this.options.url,
        this.options.options).addTo(this.map);

    // add location controls
    var locateControl = L.Control.extend({

        options: {
            position: 'left'
        },

        onAdd: function (map) {

            var container = L.DomUtil.create('div',
                'leaflet-bar leaflet-control leaflet-control-custom');

            /* container.style.cursor = 'pointer'; */
            container.style.backgroundColor = 'white';
            container.style.backgroundImage = "url('/static/icons/mouse-pointer.svg')";
            container.style.backgroundSize = '13px 13px';
            container.style.width = '26px';
            container.style.height = '26px';
            container.style.backgroundPosition = 'center';
            /* container.style.backgroundRepeat = 'no-repeat'; */

            container.onclick = function() {
                console.log('buttonClicked');
                map.locate({setView: true, maxZoom: 14});
            }

            /*
            var tooltip = L.DomUtil.create('span',
                'leaflet-tooltiptext',
                container);
            tooltip.textContent = 'Show your location';

            L.DomEvent
                .addListener(container, 'click', L.DomEvent.stopPropagation)
                .addListener(container, 'click', L.DomEvent.preventDefault)
                .addListener(container, 'click', function () {
                    map.locate({setView: true, maxZoom: 14});
                });

            */

            return container;
        },

    });

    this.map.addControl(new locateControl());

    this.map.on('locationerror', function (e) {
        alert('Could not find location <br/> ' + e.message);
    });

    // location marker
    var location_icon = L.icon({
        iconUrl: this.options.location_icon_url,
        iconSize: this.options.location_icon_size,
    });

    // locate
    this.map.on('locationfound', function (e) {
        var parent = e.target.parent
        if (typeof parent.current_location == 'undefined') {
            // create marker
            parent.current_location =
                L.marker(parent.map.getCenter(),
                    {icon: location_icon}).addTo(parent.map);
        } else {
            // move marker
            parent.current_location.setLatLng(e.latlng);
        }
    });
}

LeafletWidget.prototype.fitBounds = function (bounds = null) {

    // Get bounds if not given
    if (bounds == null) bounds = this.map.getBounds();
    console.log('bounds = ' + bounds);

    // Fit map to bounds
    this.map.fitBounds(bounds);
}

// LeafletMultiPointWidget

var LeafletMultiPointWidget = function (options) {

    // Call parent
    LeafletWidget.call(this, options);

    // store all marker id's
    this.markerIdMap = {};
    this.pointIdMap = {};

    // create layer 
    this.markers = L.layerGroup();

    this.options.add_marker_control = true;
    if (this.options.add_marker_control) {

        this.clickToAddPoint = false;
        // add add marker control
        var addMarkerControl = L.Control.extend({

            options: {
                position: 'topleft'
            },

            onAdd: function (map) {
                var container = L.DomUtil.create('div',
                    'leaflet-bar leaflet-control leaflet-control-custom leaflet-add-marker leaflet-tooltip');

                var tooltip = L.DomUtil.create('span',
                    'leaflet-tooltiptext',
                    container);
                tooltip.textContent = 'Add AED';

                map.parent.addControlCheckbox =
                    L.DomUtil.create('input',
                        'leaflet-add-marker-input',
                        container);
                map.parent.addControlCheckbox.type = 'checkbox';
                map.parent.addControlCheckbox.id = 'leaflet-add-marker-id';
                map.parent.addControlCheckbox.map = this;

                var label = L.DomUtil.create('label',
                    '',
                    container);
                label.htmlFor = 'leaflet-add-marker-id';

                L.DomEvent
                    .addListener(map.parent.addControlCheckbox,
                        'click', L.DomEvent.stopPropagation)
                    .addListener(map.parent.addControlCheckbox,
                        'click',
                        function (e) {
                            if (e.target.checked) {
                                // enable click to add point
                                e.target.map._map.parent.clickToAddPoint = true;
                            } else {
                                // disable click to add point
                                e.target.map._map.parent.clickToAddPoint = false;
                            }
                        });

                return container;
            },

        });

        this.map.addControl(new addMarkerControl());

        // listen to click
        this.map.on('click', function (e) {
            var map = e.target.parent;
            if (map.clickToAddPoint) {
                // add marker?
                map.addPoint(e.latlng.lat, e.latlng.lng,
                    -1, map.options.newPointFunction);
                // disable add marker mode
                map.addControlCheckbox.click();
            }

        });
    }
}

LeafletMultiPointWidget.prototype = Object.create(LeafletWidget.prototype);
LeafletMultiPointWidget.prototype.constructor = LeafletMultiPointWidget;

// MEMBER FUNCTIONS

// add point
LeafletMultiPointWidget.prototype.addPoint = function (lat, lng, id, fun) {

    // add marker
    var marker = L.marker([lat, lng])
        .addTo(this.map);

    if (fun) {
        marker.on('click', fun);
    }

    L.stamp(marker);
    this.markers.addLayer(marker);

    if (id >= 0) {
        this.markerIdMap[marker._leaflet_id] = id;
        this.pointIdMap[id] = marker._leaflet_id;
    }

    // TODO: Disable add marker mode

    return marker;
}


// LeafletPointWidget

var LeafletPointWidget = function (options) {

    // Call parent
    LeafletWidget.call(this, options);

    if (!this.options.point) {
        this.options.point = [options.lat, options.lng];
    }

    // add marker
    this.point = L.marker(L.latLng(this.options.point[0], this.options.point[1]),
        {draggable: true});
    this.point.addTo(this.map);

    // add reference to parent object
    this.point.parent = this;

    // call set point to update fields
    this.setPoint(L.latLng(this.options.point[0], this.options.point[1]));

    // set coordinates when dragged
    this.point.on('dragend', function (e) {
        e.target.parent.setPoint(e.target.getLatLng());
    });

    // set coordinates when map is click
    this.map.on('click',
        function (e) {
            e.target.parent.setPoint(e.latlng);
        });

}
LeafletPointWidget.prototype = Object.create(LeafletWidget.prototype);
LeafletPointWidget.prototype.constructor = LeafletPointWidget;

// MEMBER FUNCTIONS

// update point
LeafletPointWidget.prototype.setPoint = function (p) {

    // set point coordinates
    this.point.setLatLng(p);

    // update fields
    if (this.options.id) {
        document.getElementById(this.options.id).value =
            'POINT(' + p.lng + ' ' + p.lat + ')';
    }
    if (this.options.id_lat) {
        document.getElementById(this.options.id_lat).value = p.lat;
    }
    if (this.options.id_lng) {
        document.getElementById(this.options.id_lng).value = p.lng;
    }
}

// Polyline Widget

var LeafletPolylineWidget = function (options) {

    // Call parent
    LeafletWidget.call(this, options);

    // Initialize id map
    this.polylineIdMap = {}

    // create layer 
    this.lines = L.layerGroup();

}

LeafletPolylineWidget.prototype = Object.create(LeafletWidget.prototype);
LeafletPolylineWidget.prototype.constructor = LeafletPolylineWidget;

LeafletPolylineWidget.prototype.addLine = function (points, id, color, fun) {

	// Create polyline
    var polyline = L.polyline(points, {color: color}).addTo(this.map);
    L.stamp(polyline);
    this.lines.addLayer(polyline);

    // Add click callback
    if (fun) {
        polyline.on('click', fun);
    }

    // Set id
    if (id >= 0) {
        this.polylineIdMap[polyline._leaflet_id] = id;
    }

}