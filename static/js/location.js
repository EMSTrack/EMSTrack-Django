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
    }

    static toText(location) {

        // format address
        let address = [location.number, location.street, location.unit].join(' ').trim();

        if (address !== "") {
            if (location.neighborhood !== "")
                address = [address, location.neighborhood].join(', ').trim();
        } else
            address += location.neighborhood.trim()

        if (address !== "")
            address = [address, location.city, location.state].join(', ').trim();
        else
            address = [location.city, location.state].join(', ').trim();

        address = [address, location.zipcode].join(' ').trim();
        address = [address, location.country].join(', ').trim();

        return address;
    }

    renderTypeForm(label, classes = "") {

        // language=HTML
        const top = `<div class="dropdown ${classes}"
    id="location-${label}-type-menu">
    <button class="btn btn-outline-dark btn-sm dropdown-toggle" type="button" 
            id="location-${label}-type-menu-button" 
            data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
        <span id="location-${label}-type-menu-button-label">${location_type[this.type]}</span>
    </button>
    <div class="dropdown-menu" aria-labelledby="location-${label}-type-menu-button">`;

        let middle = '';
        location_type_order.forEach( (type) => {
            middle += `        <a class="dropdown-item small"
        id="location-${label}-type-${type}-menu-item" 
        href="#">${location_type[type]}</a>`;
        });

        // language=HTML
        const bottom = `    </div>
</div>`;

        return top + middle + bottom;
    }

    renderAddress(label, classes = "") {

        // language=HTML
        return (
            `<div class="my-0 py-0 ${classes}" id="location-${label}-address-div">
    <p>
        <em>${translation_table['Address']}:</em>
    </p>
    <p>
        ${Location.toText(this)}
    </p>
</div>`
        );

    }

    render(label, classes = "", options = ['address-div']) {

        if (options.includes('type-dropdown'))
            return this.renderTypeForm(label, classes);
        else // if (options.include('address-div'))
            return this.renderAddress(label, classes);;
    }

    postRender(label, options = ['address-div']) {

        if (options.includes('type-dropdown')) {
            $(`#location-${label}-type-menu a`)
                .click(function () {

                    // copy to label
                    $(`#location-${label}-type-menu-button-label`)
                        .text($(this).text());

                });
        }

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

