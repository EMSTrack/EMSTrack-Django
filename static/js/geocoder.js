var Geocoder = function(options) {

    this.options = {};

    // Altering using user-provided options
    for (var property in options) {
        if (options.hasOwnProperty(property)) {
            this.options[property] = options[property];
        }
    }

    // initialize parser configurations
    this.parser_configurations = {

        'US': {
            regex: /^(\d+)(\D+)((suite|ste|#)?\s*\d+)?$/i,
            street_components: ['number', 'street', 'complement']
        },

        'MX': {
            regex: /^(\D+)(\d+|s\/n)?(\D+\d*)?$/i,
            street_components: ['street', 'number', 'complement']
        }

    }

}

Geocoder.prototype.parse_feature = function(feature) {

    // parse feature
    if (feature['place_type'] == 'address') {

        var address = {
            street_address: "",
            number: "",
            street: "",
            complement: "",
            unit: null,
            neighborhood: null,
            city: "",
            state: "",
            zipcode: "",
            country: "",
            location: null
        };

        // set location
        address['location'] = {
            'latitude': feature['center'][0],
            'longitude': feature['center'][1]
        }

        // parse context
        var context = feature['context'];
        for (var i = 0; i < context.length; i++) {
            var item = context[i];
            var id = item['id'];
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
        var street_address = feature['place_name'];
        address['street_address'] = street_address;

        // parse street address
        var street = street_address.split(',');

        // load configuration based on country
        var config = this.parser_configurations[address['country']];

        var matches = street[0].match(config['regex']);
        if (matches) {
            console.log(matches);
            var street_components = config['regex'];
            // matches[0] is the entire matched string
            for (var i = 1; i < matches.length; i++) {
                if (matches[i] !== undefined)
                    address[street_components[i-1]] = matches[i].trim();
            }
        }

        return address;
    }

    // log error
    console.log("Does not know how to parse feature of type'" + feature['place_type'] + "'");

}

Geocoder.prototype.reverse = function(location, options, callback) {

    var url = "https://api.mapbox.com/geocoding/v5/mapbox.places/";

    var parameters = this.options;

    // Start with class options
    for (var property in this.options) {
        if (this.options.hasOwnProperty(property)) {
            parameters[property] = this.options[property];
        }
    }

    // Altering using user-provided options
    for (var property in options) {
        if (options.hasOwnProperty(property)) {
            parameters[property] = options[property];
        }
    }

    // construct query
    url += location.lng + ',' + location.lat + ".json";

    // add parameters
    var prefix = '?';

    for (var option in parameters) {
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

        console.log('JSON response = ' + response);

        // callback
        if (callback)
            callback(response.features, "success");

    })
        .fail(function (jqxhr, textStatus, error) {

            if (callback)
                callback({error: error}, textStatus);
            else
                alert("Could not geocode:" +
                    textStatus + "," + error + "\n");

        });

}


Geocoder.prototype.geocode = function(query, options, callback) {

    var url = "https://api.mapbox.com/geocoding/v5/mapbox.places/";

    var parameters = this.options;

    // Start with class options
    for (var property in this.options) {
        if (this.options.hasOwnProperty(property)) {
            parameters[property] = this.options[property];
        }
    }

    // Altering using user-provided options
    for (var property in options) {
        if (options.hasOwnProperty(property)) {
            parameters[property] = options[property];
        }
    }

    // construct query
    url += encodeURIComponent(query) + ".json";

    // add parameters
    var prefix = '?';

    for (var option in parameters) {
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

        // callback
        if (callback)
            callback(response.features, "success");

    })
        .fail(function (jqxhr, textStatus, error) {

            if (callback)
                callback({error: error}, textStatus);
            else
                alert("Could not geocode:" +
                    textStatus + "," + error + "\n");

        });

}