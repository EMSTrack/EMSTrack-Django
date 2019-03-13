import $ from 'jquery';

class BaseGeocoder {

    constructor(options) {

        // initialize options
        this.options = {};

        // Altering using user-provided options
        for (const property in options) {
            if (options.hasOwnProperty(property)) {
                this.options[property] = options[property];
            }
        }

        // initialize parser configurations
        this.parser_configurations = {

            'US': {
                regex: /^(\d+)?(\D+)((suite|ste|#)?\s*\d+)?$/i,
                street_components: ['number', 'street', 'unit']
            },

            'MX': {
                regex: /^(\D+)(\d+|s\/n)?(\D+\d*)?$/i,
                street_components: ['street', 'number', 'unit']
            }

        }

    }

    // parse street address
    parse_street_address(street_address, country, address) {

        // initialize address
        address = address || {};

        // parse street address
        const street = street_address.split(',');

        // load configuration based on country
        const config = this.parser_configurations[country];

        const matches = street[0].match(config['regex']);
        if (matches) {
            console.log(matches);
            const street_components = config['street_components'];
            // matches[0] is the entire matched string
            for (let i = 1; i < matches.length; i++) {
                if (matches[i] !== undefined)
                    address[street_components[i - 1]] = matches[i].trim();
            }
        }

        return address;
    }

    reverse(location, callback, options) {
        throw new Error("Not implemented!");
    }

    geocode(location, callback, options) {
        throw new Error("Not implemented!");
    }

}

export class GeocoderMapBox extends BaseGeocoder {

    constructor(options) {

        // add query default parameters
        options['types'] = 'address';
        options['limit'] = 1;

        // call super
        super(options);

    }

    parse_response(response) {

        // retrieve features
        const features = response.features;
        if (features.length == 0)
            return null;

        // parse first feature
        const feature = features[0];
        if (feature['place_type'] == 'address') {

            let address = {
                street_address: "",
                number: "",
                street: "",
                unit: undefined,
                neighborhood: undefined,
                city: "",
                state: "",
                zipcode: undefined,
                country: "",
                location: undefined
            };

            // set location
            address['location'] = {
                'latitude': feature['center'][1],
                'longitude': feature['center'][0]
            };

            // parse context
            const context = feature['context'];
            for (let i = 0; i < context.length; i++) {
                const item = context[i];
                const id = item['id'];
                if (id.startsWith('neighborhood'))
                    address['neighborhood'] = item['text'];
                else if (id.startsWith('postcode'))
                    address['zipcode'] = item['text'];
                else if (id.startsWith('place'))
                    address['city'] = item['text'];
                else if (id.startsWith('region'))
                    address['state'] = item['short_code'].toUpperCase().substr(3);
                else if (id.startsWith('country'))
                    address['country'] = item['short_code'].toUpperCase();
            }

            // set street_address
            const street_address = feature['place_name'];
            address['street_address'] = street_address;

            // parse street address
            return this.parse_street_address(street_address,
                address['country'],
                address);

        }

        // log error
        console.log("Does not know how to parse feature of type '" + feature['place_type'] + "'");

        return null;
    }

    reverse(location, callback, options) {

        options = options || {};

        let property;
        let url = "https://api.mapbox.com/geocoding/v5/mapbox.places/";

        const parameters = this.options;

        // Start with class options
        for (property in this.options) {
            if (this.options.hasOwnProperty(property)) {
                parameters[property] = this.options[property];
            }
        }

        // Altering using user-provided options
        for (property in options) {
            if (options.hasOwnProperty(property)) {
                parameters[property] = options[property];
            }
        }

        // construct query
        url += location.lng + ',' + location.lat + ".json";

        // add parameters
        let prefix = '?';
        for (const option in parameters) {
            if (parameters.hasOwnProperty(option)) {

                // add options
                url += prefix
                    + encodeURIComponent(option)
                    + "="
                    + encodeURIComponent(parameters[option]);
                prefix = '&';

            }
        }

        // query mapbox
        $.getJSON(url, function (response) {

            // parse results
            const address = this.parse_response(response);

            // callback
            if (callback)
                callback(address, response);

        }.bind(this))
            .fail(function (jqxhr, textStatus, error) {

                if (callback)
                    callback(null, {error: error});
                else
                    alert("Could not geocode:" +
                        textStatus + "," + error + "\n");

            });

    }

    geocode(query, callback, options) {

        options = options || { autocomplete: 'true' };

        let property;
        let url = "https://api.mapbox.com/geocoding/v5/mapbox.places/";

        const parameters = this.options;

        // Start with class options
        for (property in this.options) {
            if (this.options.hasOwnProperty(property)) {
                parameters[property] = this.options[property];
            }
        }

        // Altering using user-provided options
        for (property in options) {
            if (options.hasOwnProperty(property)) {
                parameters[property] = options[property];
            }
        }

        // construct query
        url += encodeURIComponent(query) + ".json";

        // add parameters
        let prefix = '?';
        for (const option in parameters) {
            if (parameters.hasOwnProperty(option)) {

                // add options
                url += prefix
                    + encodeURIComponent(option)
                    + "="
                    + encodeURIComponent(parameters[option]);
                prefix = '&';

            }
        }

        // query mapbox
        $.getJSON(url, function (response) {

            // parse results
            const address = this.parse_response(response);

            // callback
            if (callback)
                callback(address, response);

        }.bind(this))
            .fail(function (jqxhr, textStatus, error) {

                if (callback)
                    callback(null, {error: error});
                else
                    alert("Could not geocode:" +
                        textStatus + "," + error + "\n");

            });

    }

}

export class GeocoderGoogle extends BaseGeocoder {



}

/**
 * @return {null}
 */
export function GeocoderFactory(map_provider, options) {

    // default empty options
    options = options || {};

    // Retrieve MapBox access_token
    const provider = map_provider['provider'];
    if (provider === 'mapbox') {
        // add access token
        options['access_token'] = map_provider['access_token'];
        return new GeocoderMapBox(options);
    } else if (provider === 'google') {
        return new GeocoderGoogle(options);
    } else
        return null;

}

