import {Dropdown} from "./dropdown";

/**
 * Location base class
 */

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

class SimpleAddress {

    constructor(location) {
        this.location = location;
    }

    render(label, classes = "") {

        // language=HTML
        return `<div class="my-0 py-0 ${classes}" id="${label}-address-div">
    <p>
        <em>${translation_table['Address']}:</em>
    </p>
    <p>
        ${this.location.toText()}
    </p>
</div>`;

    }

    postRender() {

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
        this.addressCompoenent = null;

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

    selectType(label, type) {

        if (this.type === type)
            // no changes, quick return
            return

        // otherwise reinitialize address component
        this.addressCompoenent = new SimpleAddress(this.location);

        $(`#location-${label}-item-address`)
            .empty()
            .append(
                this.addressCompoenent.render(`location-${label}`)
            );

        this.addressCompoenent.postRender();

    }

    render(label, classes = "", options = ['address-div']) {

        let html = '';

        // type
        this.typeDropdown = new Dropdown({
            options: location_type,
            value: this.type,
            prefix: `location-${label}`,
            clickOnInitialValue: true,
            onClick: (key) => {
                this.selectType(label, key);
            }
        });

        html += `<li id="location-${label}-item-type" class="${classes}">
    <em>${translation_table['Type']}:</em>`;

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

