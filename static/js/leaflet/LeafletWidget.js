import L from 'leaflet'
import 'leaflet-rotatedmarker'
import "leaflet/dist/leaflet.css";
import 'leaflet.gridlayer.googlemutant'

// https://github.com/Leaflet/Leaflet/issues/4968
import iconUrl from 'leaflet/dist/images/marker-icon.png';
import icon2xUrl from 'leaflet/dist/images/marker-icon-2x.png';
import iconShadowUrl from 'leaflet/dist/images/marker-shadow.png';

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: icon2xUrl,
  iconUrl: iconUrl,
  shadowUrl: iconShadowUrl,
});

// LeafletWidget

export class LeafletWidget {

    constructor(options) {

        // enabled flag
        this.enabled = true;

        // Retrieve map provider
        this.map_provider = options['map_provider'];
        delete options['map_provider'];

        let url;
        let provider_options;
        if (this.map_provider['provider'] === 'mapbox') {

            url = 'https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token=';
            provider_options = {
                attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="http://mapbox.com">Mapbox</a>',
                maxZoom: 18,
                id: 'mapbox.streets'
            };

        } else if (this.map_provider['provider'] === 'google') {

            url = '';
            provider_options = {
                maxZoom: 18,
                type: 'roadmap'
            };

        }

        this.options = {
            url: url,
            options: provider_options,

            layer_names: ['Roads', 'Satellite', 'Hybrid'],

            lat: 32.53530431898372,
            lng: -116.9165934003241,
            zoom: 15,
            location_icon_url: '/static/icons/pin/blue.svg',
            location_icon_size: [32, 32],
            add_location_control: false,
            add_marker_control: false,
        };

        // Altering using user-provided options
        for (const property in options) {
            if (options.hasOwnProperty(property)) {
                this.options[property] = options[property];
            }
        }

        // create map
        this.map = L.map(this.options.map_id)
            .setView(L.latLng(this.options.lat,
                this.options.lng),
                this.options.zoom);
        // add reference to parent object
        this.map.parent = this;

        if (this.map_provider['provider'] === 'mapbox') {

            // create mapbox title layer
            L.tileLayer(this.options.url + this.map_provider['access_token'],
                this.options.options)
                .addTo(this.map);

        } else if (this.map_provider['provider'] === 'google') {

            // create google map title layer
            const roadMutant = L.gridLayer.googleMutant(this.options.options)
                .addTo(this.map);

            // Create satelite and hybrid layers
            const satMutant = L.gridLayer.googleMutant({
                maxZoom: 24,
                type:'satellite'
            });

            const hybridMutant = L.gridLayer.googleMutant({
                maxZoom: 24,
                type:'hybrid'
            });

            const layers = {};
            layers[this.options.layer_names[0]] = roadMutant;
            layers[this.options.layer_names[1]] = satMutant;
            layers[this.options.layer_names[2]] = hybridMutant;
            L.control.layers(
                layers,
                {},
                { collapsed: false }
            ).addTo(this.map);

        }

        if (this.add_location_control) {

            // add location controls
            const locateControl = L.Control.extend({

                options: {
                    position: 'topleft'
                },

                onAdd: function (map) {

                    const container = L.DomUtil.create('div',
                        'leaflet-bar leaflet-control leaflet-control-custom');

                    container.style.width = '32px';
                    container.style.height = '32px';
                    container.style.backgroundImage = "url('/static/icons/mouse-pointer.svg')";
                    container.style.backgroundPosition = 'center';
                    container.style.backgroundSize = '20px 20px';
                    container.style.backgroundColor = 'white';
                    container.style.backgroundRepeat = 'no-repeat';

                    /* tooltip */
                    container.title = 'Go to your location';

                    L.DomEvent
                        .addListener(container, 'click', L.DomEvent.stopPropagation)
                        .addListener(container, 'click', L.DomEvent.preventDefault)
                        .addListener(container, 'click', function () {
                            map.locate({setView: true, maxZoom: 14});
                        });

                    return container;
                },

            });

            this.map.addControl(new locateControl());

            this.map.on('locationerror', function (e) {
                alert('Could not find location <br/> ' + e.message);
            });

            // location marker
            const location_icon = L.icon({
                iconUrl: this.options.location_icon_url,
                iconSize: this.options.location_icon_size,
            });

            // locate
            this.map.on('locationfound', function (e) {
                const parent = e.target.parent;
                if (typeof parent.current_location === 'undefined') {
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

    }

    fitBounds(bounds) {

        // Get bounds if not given
        bounds = bounds || this.map.getBounds();

        // Fit map to bounds
        this.map.fitBounds(bounds);

    }

    center(position, zoom) {

        // Get zoom from map if not given
        zoom = zoom || this.map.getZoom();

        // center map
        this.map.setView([position.latitude, position.longitude], zoom);

    }

    disable() {
        this.map.boxZoom.disable();
        this.map.doubleClickZoom.disable();
        this.map.dragging.disable();
        this.map.keyboard.disable();
        this.map.scrollWheelZoom.disable();
        // TODO: Check for updates, gives error on console
        // this.map.tap.disable();
        this.map.touchZoom.disable();
        this.enabled = false;
    }

    enable() {
        this.map.boxZoom.enable();
        this.map.doubleClickZoom.enable();
        this.map.dragging.enable();
        this.map.keyboard.enable();
        this.map.scrollWheelZoom.enable();
        // TODO: Check for updates, gives error on console
        // this.map.tap.enable();
        this.map.touchZoom.enable();
        this.enabled = true;
    }

}

// LeafletMultiPointWidget

export class LeafletMultiPointWidget extends LeafletWidget {

    constructor(options) {

        // Call parent
        super(options);

        // store all marker id's
        this.markerIdMap = {};
        this.pointIdMap = {};

        // create layer
        this.markers = L.layerGroup();

        this.options.add_marker_control = true;
        if (this.options.add_marker_control) {

            this.clickToAddPoint = false;

            // add add marker control
            const addMarkerControl = L.Control.extend({

                options: {
                    position: 'topleft'
                },

                onAdd: function (map) {
                    const container = L.DomUtil.create('div',
                        'leaflet-bar leaflet-control leaflet-control-custom leaflet-add-marker leaflet-tooltip');

                    const tooltip = L.DomUtil.create('span',
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

                    const label = L.DomUtil.create('label',
                        '',
                        container);
                    label.htmlFor = 'leaflet-add-marker-id';

                    L.DomEvent
                        .addListener(map.parent.addControlCheckbox,
                            'click', L.DomEvent.stopPropagation)
                        .addListener(map.parent.addControlCheckbox,
                            'click',
                            function (e) {
                                e.target.map._map.parent.clickToAddPoint = !!e.target.checked;
                            });

                    return container;
                },

            });

            this.map.addControl(new addMarkerControl());

            // listen to click
            this.map.on('click', function (e) {
                const map = e.target.parent;
                if (map.clickToAddPoint) {
                    // add marker?
                    map.addPoint(e.latlng.lat, e.latlng.lng, -1, map.options.newPointFunction);
                    // disable add marker mode
                    map.addControlCheckbox.click();
                }

            });
        }
    }

    // MEMBER FUNCTIONS

    // add point
    addPoint(lat, lng, id, fun) {

        // add marker
        const marker = L.marker([lat, lng])
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

}

// LeafletPointWidget

export class LeafletPointWidget extends LeafletWidget {

    constructor(options) {

        // Call parent
        super(options);

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

    // MEMBER FUNCTIONS

    // update point
    setPoint(p) {

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

}

// LeafletSimplePointWidget

export class LeafletSimplePointWidget extends LeafletWidget {

    constructor(options) {

        // Call parent
        super(options);

        // has point?
        let coordinates = null;
        if (options.hasOwnProperty('lat') && options.hasOwnProperty('lng'))
             coordinates = [options.lat, options.lng];

        // draggable
        if (!this.options.hasOwnProperty('draggable'))
            this.options['draggable'] = true;

        // clickable
        if (!this.options.hasOwnProperty('clickable'))
            this.options['clickable'] = true;

        // onChange
        if (!this.options.hasOwnProperty('onChange'))
            this.options['onChange'] = null;

        // initialize point
        this.point = null;
        if (coordinates !== null)
            this.setPoint(coordinates[0], coordinates[1]);

        // set coordinates when map is clicked
        if (this.options.clickable)
            this.map.on('click',
                (e) => {
                    if (this.enabled) {
                        const latlng = e.latlng;
                        e.target.parent.setPoint(latlng.lat, latlng.lng);
                        if (this.options.onChange != null)
                            this.options.onChange(latlng.lat, latlng.lng);
                    }
                });

    }

    // MEMBER FUNCTIONS

    // update point
    setPoint(lat, lng) {

        // Does point exist?
        if (this.point === null) {

            // create first

            // add marker
            this.point = L.marker(L.latLng([lat, lng]), { draggable: this.options['draggable']} );
            this.point.addTo(this.map);

            // add reference to parent object
            this.point.parent = this;

            // set coordinates when dragged
            if (this.options.draggable)
                this.point.on('dragend', (e) => {
                    if (this.enabled) {
                        const latlng = e.target.getLatLng();
                        e.target.parent.setPoint(latlng.lat, latlng.lng);
                        if (this.options.onChange != null)
                            this.options.onChange(latlng.lat, latlng.lng);
                    }
                });

        } else {

            // just update coordinates
            this.point.setLatLng(L.latLng([lat, lng]));

        }

        // center map
        this.center({ latitude: lat, longitude: lng });

        // update fields
        if (this.options.id) {
            document.getElementById(this.options.id).value = 'POINT(' + lng + ' ' + lat + ')';
        }
        if (this.options.id_lat) {
            document.getElementById(this.options.id_lat).value = lat;
        }
        if (this.options.id_lng) {
            document.getElementById(this.options.id_lng).value = lng;
        }

    }

    disable() {
        super.disable();
        this.point.dragging.disable();
    }

    enable() {
        super.enable();
        this.point.dragging.enable();
    }

}

// Polyline Widget

export class LeafletPolylineWidget extends LeafletWidget {

    constructor(options) {

        // Call parent
        super(options);

        // store all markers and lines id's
        this.polylineIdMap = {};
        this.markerIdMap = {};
        this.pointIdMap = {};

        // create layers
        this.layers = {};

        // create default layer
        this.createLayer('default');

    }

    createLayer(layer) {

        const layerName = layer + 'LeafletPolylineWidgetPane';
        this.map.createPane(layerName);
        this.layers[layer] = {
            'markers': L.layerGroup({'pane': layerName}),
            'lines': L.layerGroup({'pane': layerName})
        };

    }

    getLayerPane(layer) {

        const layerName = layer + 'LeafletPolylineWidgetPane';
        return this.map.getPane(layerName);

    }

    addLine(points, id, color, fun, layer) {

        fun = fun || null;
        layer = layer || 'default';

        // Create polyline
        const layerName = layer + 'LeafletPolylineWidgetPane';
        const polyline = L.polyline(points, {color: color, pane: layerName})
            .addTo(this.map);

        // Add click callback
        if (fun) {
            polyline.on('click', fun);
        }

        // Add marker
        L.stamp(polyline);
        this.layers[layer]['lines'].addLayer(polyline);

        // Track ids
        if (id >= 0) {
            this.polylineIdMap[polyline._leaflet_id] = id;
        }

        return polyline;
    }

    // add point
    addPoint(lat, lng, id, fun, layer) {

        fun = fun || null;
        layer = layer || 'default';

        // Create marker without a shaddow
        const icon = new L.Icon.Default();
        icon.options.shadowSize = [0, 0];
        const layerName = layer + 'LeafletPolylineWidgetPane';
        const marker = L.marker([lat, lng], {icon: icon, pane: layerName})
            .addTo(this.map);

        // Add click callback
        if (fun) {
            marker.on('click', fun);
        }

        // Add marker
        L.stamp(marker);
        this.layers[layer]['markers'].addLayer(marker);

        // Track ids
        if (id >= 0) {
            this.markerIdMap[marker._leaflet_id] = id;
            this.pointIdMap[id] = marker._leaflet_id;
        }

        return marker;
    }

}
