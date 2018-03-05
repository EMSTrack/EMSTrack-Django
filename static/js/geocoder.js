var Geocoder = function(options) {

    this.options = {
        autocomplete: 'true'
    };

     // Altering using user-provided options
    for (var property in options) {
        if (options.hasOwnProperty(property)) {
            this.options[property] = options[property];
        }
    }

}

Geocoder.prototype.parse_feature = function(feature) {

    // parse feature
    if (feature['place_type'] == 'address') {

        var address = {
            number: "",
            street: "",
            unit: null,
            neighborhood: null,
            city: "",
            state: "",
            zipcode: "",
            country: "",
            location: null
        };
        address['location'] = {
            'latitude': feature['center'][0],
            'longitude': feature['center'][1]
        }

        // Parse address
        var address = feature['place_name'].split(',');
        address['street'] = address[0];

        // Parse context
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
                address['state'] = item['short-code'].toUpperCase().substr(3);
            else if (id.startsWith('country'))
                address['country'] = item['short-code'].toUpperCase();
        }

        return address;
    }

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