import { logger } from './logger';

const axios = require('axios');

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
            // logger.log('debug', matches);
            const street_components = config['street_components'];
            // matches[0] is the entire matched string
            for (let i = 1; i < matches.length; i++) {
                if (matches[i] !== undefined)
                    address[street_components[i - 1]] = matches[i].trim();
            }
        }

        return address;
    }

    reverse(location, options) {
        throw new Error("Not implemented!");
    }

    geocode(location, options) {
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
        if (features.length === 0)
            throw new Error("Empty results");

        // parse first feature
        const feature = features[0];
        if ('address' in feature['place_type']) {

            let address = {
                formatted_address: "",
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
            const formatted_address = feature['place_name'];
            address['formatted_address'] = formatted_address;

            // parse street address
            return this.parse_street_address(formatted_address,
                address['country'],
                address);

        }

        // log error
        throw new Error("Does not know how to parse feature of type '" + feature['place_type'] + "'");

    }

    reverse(location, options) {

        options = options || {};

        let property;
        let url = "https://api.mapbox.com/geocoding/v5/mapbox.places/";

        const parameters = {};

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

        // logger.log('debug', "geocode url = '" + url + "'");
        
        // query mapbox
        return axios.get(url)
            .then( (response) => {
                
                // parse results
                return this.parse_response(response.data);
                
            });
        
    }

    geocode(query, options) {

        options = options || { autocomplete: 'true' };

        let property;
        let url = "https://api.mapbox.com/geocoding/v5/mapbox.places/";

        const parameters = {};

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

        // logger.log('debug', "geocode url = '" + url + "'");

        // query mapbox
        return axios.get(url)
            .then( (response) =>  {
                
                // parse results
                return this.parse_response(response.data);
                
            });

    }

}

export class GeocoderGoogle extends BaseGeocoder {

    constructor(options) {

        // call super
        super(options);

    }

    parse_feature(feature) {

        let address = {
            formatted_address: "",
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
        const location = feature['geometry']['location'];
        address['location'] = {
            'latitude': Number.parseFloat(location['lat']),
            'longitude': Number.parseFloat(location['lng'])
        };
        logger.log('debug', location);
        logger.log('debug', address);

        // set formated address
        address['formatted_address'] = feature['formatted_address'];
        logger.log('debug', address);

        // parse context
        const context = feature['address_components'];
        for (let i = 0; i < context.length; i++) {
            const item = context[i];
            const types = item['types'];
            if (types.includes('sublocality_level_1'))
                address['neighborhood'] = item['short_name'];
            else if (types.includes('street_number'))
                address['number'] = item['short_name'];
            else if (types.includes('route'))
                address['street'] = item['short_name'];
            else if (types.includes('locality'))
                address['city'] = item['long_name'];
            else if (types.includes('administrative_area_level_1'))
                address['state'] = item['short_name'].replace('.', '');
            else if (types.includes('postal_code'))
                address['zipcode'] = item['short_name'];
            else if (types.includes('country'))
                address['country'] = item['short_name'].toUpperCase();
        }
        logger.log('debug', address);

        return address;

    }

    parse_response(response, filter) {

        filter = filter || [];

        // retrieve features
        const results = response['results'];
        if (results.length === 0)
            throw new Error("Empty results");

        // parse first feature
        for (let i = 0; i <  results.length; i++) {

            const feature = results[i];
            // logger.log('debug', feature);

            // filter types
            if (filter.length > 0) {

                const types = feature['types'];
                let j = 0;
                for (; j < types.length; j++) {
                    if ( filter.includes(types[j]) )
                        break;
                }

                if (j === types.length)
                    // could not find
                    continue;
            }

            let address = {
                formatted_address: "",
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
            const location = feature['geometry']['location'];
            address['location'] = {
                'latitude': location['lat'],
                'longitude': location['lng']
            };

            // set formated address
            address['formatted_address'] = feature['formatted_address'];

            // parse context
            const context = feature['address_components'];
            for (let i = 0; i < context.length; i++) {
                const item = context[i];
                const types = item['types'];
                if (types.includes('sublocality_level_1'))
                    address['neighborhood'] = item['short_name'];
                else if (types.includes('street_number'))
                    address['number'] = item['short_name'];
                else if (types.includes('route'))
                    address['street'] = item['short_name'];
                else if (types.includes('locality'))
                    address['city'] = item['long_name'];
                else if (types.includes('administrative_area_level_1'))
                    address['state'] = item['short_name'].replace('.', '');
                else if (types.includes('postal_code'))
                    address['zipcode'] = item['short_name'];
                else if (types.includes('country'))
                    address['country'] = item['short_name'].toUpperCase();
            }

            return address;

        }

        // throw error
        throw new Error("Does not know how to parse address");
    }

    reverse(location, options) {

        options = options || {};

        let property;
        let url = "https://maps.googleapis.com/maps/api/geocode/json";

        const parameters = {};

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
        parameters['latlng'] = location.lat + ',' + location.lng;

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

        // query google
        return axios.get(url)
            .then( (response) => {
                
                // parse results
                return this.parse_response(response.data, ['street_address', 'route', 'political']);
                
            });
        
    }

    geocode(query, options) {

        options = options || { autocomplete: 'true' };

        let property;
        let url = "https://maps.googleapis.com/maps/api/geocode/json";

        const parameters = {};

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

        // normalize query
        const combining = /[\u0300-\u036F]/g;
        query = query.normalize('NFKD').replace(combining, '');

        // logger.log('debug', "query = '" + query + "'");

        // construct query
        parameters['address'] = encodeURIComponent(query);

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

        // query google
        return axios.get(url)
            .then( (response) =>  {
                
                // parse results
                return this.parse_response(response.data);
                
            });
        
    }
    
}

/**
 *
 * @param map_provider
 * @param options
 * @returns {*}
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
        // add access token
        options['key'] = map_provider['access_token'];
        return new GeocoderGoogle(options);
    } else
        return null;

}
