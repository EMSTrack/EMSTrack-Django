import {logger} from "./logger";

import {LeafletSimplePointWidget} from "./leaflet/LeafletWidget";

import {Dropdown} from "./dropdown";

/**
 * Location base class
 */

// settings are exported as default
const settings = {
    locations: {},
    location_type: {},
    translation_table: {},
    map_provider: undefined,
};
export default settings;

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

    updateCoordinates(label, lat, lng) {

        logger.log('debug', 'Coordinates updated to %f, %f', lat, lng);

        this.onChange(this.location);

    }

    updateAddress(label, address) {

        logger.log('debug', 'Address updated to %s', address);

        this.onChange(this.location);

    }

    refresh() {

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
            clickable: true,
            draggable: true,
            onChange: (lat, lng) => { this.updateCoordinates(label, lat, lng); }
        };

        this.map = new LeafletSimplePointWidget(options);
        this.refresh();

        // bind on change
        const self = this;
        $(`#address-${label}-address`).on('change', function () {
            self.updateAddress(label, $(this).val());
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

    select(label, key, force = false) {

        if (!force && this.location !== undefined && this.location.id === key)
            // no changes, quick return
            return;

        // setting location
        this.location = new Location(settings.locations[this.type][key]);

        // setting address
        $(`#address-${label}-address`)
            .empty()
            .append(this.location.toText());

        // set point on the map
        console.log(this.location);
        this.map.setPoint(this.location.location.latitude, this.location.location.longitude);

        // call onSelect
        this.onChange(this.location);
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
                this.select(label, value);
            }
        });

        // language=HTML
        let html = `<div class="my-0 py-0 ${classes}" id="${label}-address-div">
    <div>
        <p>
            <em>${settings.translation_table['Address']}:</em>`;

        html += this.dropdown.render("float-right");

        html += `        </p>
    </div>
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
            clickable: false,
            draggable: false
        };

        this.map = new LeafletSimplePointWidget(options);

        // initial select type
        if (this.location !== undefined && this.location.id !== null)
            this.select(label, this.location.id, true);

    }

}

ChoiceAddress.default = {
    type: '',
    location: undefined,
    onChange: (location) => { logger.log('debug', 'location = %s', location); }
};

class SimpleAddress {

    constructor(location) {
        this.location = location;
    }

    render(label, classes = "") {

        // language=HTML
        return `<div class="my-0 py-0 ${classes}" id="${label}-address-div">
    <p>
        <em>${settings.translation_table['Address']}:</em>
    </p>
    <p>
        ${this.location.toText()}
    </p>
</div>`;

    }

    postRender(label) {

    }

}

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

    toText() {

        // format address
        let address = [this.number, this.street, this.unit].join(' ').trim();

        if (address !== "") {
            if (this.neighborhood !== "")
                address = [address, this.neighborhood].join(', ').trim();
        } else
            address += this.neighborhood.trim()

        if (address !== "")
            address = [address, this.city, this.state].join(', ').trim();
        else
            address = [this.city, this.state].join(', ').trim();

        address = [address, this.zipcode].join(' ').trim();
        address = [address, this.country].join(', ').trim();

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

    render(label, classes = "", options = ['address-div']) {

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

    postRender(label, options = ['address-div']) {

        if (this.typeDropdown !== null)
            this.typeDropdown.postRender();

        // initial select type
        this.selectType(label, this.type, true);

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
    city: '',
    state: '',
    zipcode: '',
    country: '',
    location: new Point()
};

