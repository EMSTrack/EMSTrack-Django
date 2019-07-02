import {logger} from "../logger";

import {LeafletSimplePointWidget} from "../leaflet/LeafletWidget";

import {Dropdown} from "./dropdown";

import { Settings } from "../settings";

/**
 * Location base class
 */

const settings = new Settings();

export class Point {

    constructor(parameters) {
        const properties = Object.assign({...Point.default}, parameters);

        this.latitude = properties.latitude;
        this.longitude = properties.longitude;
        this.srid = properties.srid;
    }

}

Point.default = {
    latitude: 32.5149,
    longitude: -117.0382,
    srid: 4326
};

class MapAddress {

    constructor(parameters) {

        const properties = Object.assign({...MapAddress.default}, parameters);

        this.type = properties.type;
        this.location = properties.location;
        this.onChange = properties.onChange;

        this.map = null;
    }

    onUpdateCoordinates(label, lat, lng) {

        logger.log('debug', 'Coordinates updated to %f, %f', lat, lng);

        // geocode coordinates
        settings.geocoder
            .reverse({lat: lat, lng: lng})
            .then( (address) => {

                logger.log('debug', "address = '%j'", address);

                // parse features into current address
                Object.assign(this.location, address);

                // refresh
                this.refresh(label);

                this.onChange(this.location);

            })
            .catch( (error) => {
                logger.log('warn', "Could not forward geocode. Error: '%s'", error);

                this.onChange(this.location);

            });

    }

    onUpdateAddress(label, address) {

        logger.log('debug', 'Address updated to %s', address);

        // geocode address
        settings.geocoder
            .geocode(address)
            .then( (address) => {

                logger.log('debug', "address = '%j'", address);

                // parse features into current address
                Object.assign(this.location, address);

                // refresh
                this.refresh(label);

                this.onChange(this.location);

        })
        .catch( (error) => {
            logger.log('warn', "Could not forward geocode. Error: '%s'", error);

            this.onChange(this.location);

        });

    }

    refresh(label) {

        // setting address
        $(`#address-${label}-address`)
            .val(this.location.toText());

        // set point on the map
        this.map.setPoint(this.location.location.latitude, this.location.location.longitude);

    }

    render(label, classes = "") {

        // language=HTML
        let html = `<div class="my-0 py-0 ${classes}" id="${label}-address-div">
    <div>
        <p>
            <em>${settings.translation_table['Address']}:</em>
        </p>
        <p>
            <input class="form-control form-control-sm"
                   id="address-${label}-address" type="text"
                   name="street"
                   placeholder="${settings.translation_table['Address']}">
            
        </p>
    </div>`;

        html += `    <div>
        <p>
            <input type="hidden" id="address-${label}-lat" name="lat">
            <input type="hidden" id="address-${label}-lng" name="lng">
            <input type="hidden" id="address-${label}-pnt" name="point">
            <div id="address-${label}-map" style="height: 250px"></div>
        </p>
    </div>
</div>`;

        return html;
    }

    postRender(label) {

        // Set up map widget
        const options = {
            map_id: `address-${label}-map`,
            id: `address-${label}-pnt`,
            id_lat: `address-${label}-lat`,
            id_lng: `address-${label}-lng`,
            zoom: 12,
            map_provider: mapProvider,
            layer_names: [settings.translation_table['Roads'], settings.translation_table['Satellite'], settings.translation_table['Hybrid']],
            clickable: true,
            draggable: true,
            onChange: (lat, lng) => { this.onUpdateCoordinates(label, lat, lng); }
        };

        this.map = new LeafletSimplePointWidget(options);
        this.map.map.on('load', () => {
            console.log('on load');
            this.refresh(label);
        } );

        // bind on change
        const self = this;
        $(`#address-${label}-address`)
            .on('change', function () {
                self.onUpdateAddress(label, $(this).val());
            });

    }

}

MapAddress.default = {
    type: '',
    location: undefined,
    onChange: (location) => { logger.log('debug', 'location = %s', location); },
};

class ChoiceAddress {

    constructor(parameters) {

        const properties = Object.assign({...ChoiceAddress.default}, parameters);

        this.type = properties.type;
        this.location = properties.location;
        this.onChange= properties.onChange;

        this.dropdown = null;
        this.map = null;
    }

    onClick(label, id) {

        if (this.location !== undefined && this.location.id === id)
            // no changes, quick return
            return;

        // setting location
        this.location = new Location(settings.locations[this.type][id]);

        // refresh
        this.refresh(label);

        // call onSelect
        this.onChange(this.location);
    }

    refresh(label) {

        // setting address
        $(`#address-${label}-address`)
            .empty()
            .append(this.location.toText());

        // set point on the map
        this.map.setPoint(this.location.location.latitude, this.location.location.longitude);

    }

    render(label, classes = "") {

        // dropdown
        let options = {};
        if (settings.locations.hasOwnProperty(this.type)) {
            for (const [id, location] of Object.entries(settings.locations[this.type]))
                options[id] = location.name;
        }

        this.dropdown = new Dropdown({
            options: options,
            prefix: `address-${label}`,
            onClick: (value) => {
                this.onClick(label, value);
            }
        });

        // language=HTML
        let html = `<div class="my-0 py-0 ${classes}" id="${label}-address-div">
    <div>
        <em>${settings.translation_table['Address']}:</em>`;

        html += this.dropdown.render("float-right");

        html += `    </div>
    <div>
        <p id="address-${label}-address">
            ${settings.translation_table['Please select']} ${settings.location_type[this.type].toLowerCase()}  
        </p>
        <p>
            <input type="hidden" id="address-${label}-lat" name="lat">
            <input type="hidden" id="address-${label}-lng" name="lng">
            <input type="hidden" id="address-${label}-pnt" name="point">
            <div id="address-${label}-map" style="height: 250px"></div>
        </p>
    </div>
</div>`;

        return html;
    }

    postRender(label) {

        if (this.dropdown !== null)
            this.dropdown.postRender();

        // Set up map widget
        const options = {
            map_id: `address-${label}-map`,
            id: `address-${label}-pnt`,
            id_lat: `address-${label}-lat`,
            id_lng: `address-${label}-lng`,
            zoom: 12,
            map_provider: mapProvider,
            layer_names: [settings.translation_table['Roads'], settings.translation_table['Satellite'], settings.translation_table['Hybrid']],
            clickable: false,
            draggable: false
        };

        this.map = new LeafletSimplePointWidget(options);

        // initial select type
        this.map.map.on('load', () => {
            console.log('on load');
            this.refresh(label);
        } );

    }

}

ChoiceAddress.default = {
    type: '',
    location: undefined,
    onChange: (location) => { logger.log('debug', 'location = %s', location); }
};

export class Location {

    constructor(parameters) {

        const properties = Object.assign({...Location.default}, parameters);

        this.id = properties.id;
        this.name = properties.name;
        this.type = properties.type;
        this.number = properties.number;
        this.street = properties.street;
        this.unit = properties.unit;
        this.neighborhood = properties.neighborhood;
        this.city = properties.city;
        this.state = properties.state;
        this.zipcode = properties.zipcode;
        this.country = properties.country;
        this.location = new Point(properties.location);

        this.typeDropdown = null;
        this.addressComponent = null;

    }

    static append(address, items, separator=' ') {

        for (const item of items)
            if (item)
                address = [address, item.trim()].join(separator).trim();

        return address;
    }

    toText() {

        // format address
        let address = Location.append('', [this.number, this.street, this.unit]);
        address = Location.append(address, [this.neighborhood, this.city, this.state], ', ');
        address = Location.append(address, [this.zipcode]);
        address = Location.append(address, [this.country], ', ');

        return address;
    }

    selectType(label, type, force = false) {

        if (!force && this.type === type)
            // no changes, quick return
            return;

        // setting type
        this.type = type;

        // reinitialize address component
        if (type === 'b' || type === 'o' || type === 'h' || type === 'a')
            this.addressComponent = new ChoiceAddress({
                type: type,
                location: this,
                onClick: (location) => {
                    logger.log('debug', 'Setting location to %d:%s', location.id, location.name);
                    Object.assign(this, location);
                }
            });
        else if (type === 'w' || type === 'i')
            this.addressComponent = new MapAddress({
                type: type,
                location: this,
                onClick: (location) => {
                    logger.log('debug', 'Setting location to %d:%s', location.id, location.name);
                    Object.assign(this, location);
                }
            });

        $(`#location-${label}-item-address`)
            .empty()
            .append(
                this.addressComponent.render(`location-${label}`)
            );

        this.addressComponent.postRender(`location-${label}`);

    }

    render(label, classes = "") {

        let html = '';

        // type
        this.typeDropdown = new Dropdown({
            options: location_type,
            value: this.type,
            prefix: `location-${label}`,
            onClick: (value) => {
                this.selectType(label, value);
            }
        });

        html += `<li id="location-${label}-item-type" class="${classes}">
    <em>${settings.translation_table['Type']}:</em>`;

        html += this.typeDropdown.render("float-right");

        html += '</li>';

        // address
        html += `<li id="location-${label}-item-address" class="${classes}">`;

        html += '</li>';

        return html;
    }

    postRender(label) {

        if (this.typeDropdown !== null)
            this.typeDropdown.postRender();

        // initial select type
        this.selectType(label, this.type, true);


    }

    disable() {

        this.addressComponent.map.disable();

    }

    enable() {

        this.addressComponent.map.enable();

    }

    refresh(label) {

        this.addressComponent.refresh(`location-${label}`);

    }

}

Location.default = {
    id: null,
    name: '',
    type: 'w',
    number: '',
    street: '',
    unit: '',
    neighborhood: '',
    city: settings.defaults.city,
    state: settings.defaults.state,
    zipcode: '',
    country: settings.defaults.country,
    location: {...settings.defaults.location}
};

