/* Dispatch area - Should be eliminate after dispatching */

var markersGroup = new L.LayerGroup();
var isDispatching = false;
var placeIcon = L.icon({
	iconUrl: '/static/icons/place_marker.png',
	iconSize: [40, 40],
	iconAnchor: [20, 40],
	popupAnchor: [0,-40]
});

var dispatchingAmbulances = {};
var numberOfDispatchingAmbulances = 0;

var currentAddress;
var currentLocation;

var beginDispatching = function () {

    isDispatching = true;
    console.log('Begin dispatching.');

    $('#dispatch_work').html(
        '<button type="button" class="btn btn-link" onclick="endDispatching()">'
        + '<span class="glyphicon glyphicon-chevron-left"></span>'
        + 'Abort'
        + '</button>'
    );
    $('#dispatchForm').collapse('show');
    $('#ambulance_info_collapse').collapse('hide');

    // Update current location
    updateCurrentLocation(mymap.getCenter());

    // Update current address
    updateCurrentAddress(currentLocation);

}

var endDispatching = function () {

    isDispatching = false;
    dispatchingAmbulances = {};
    console.log('End dispatching.');

    markersGroup.clearLayers();
    $('#dispatch_work').html(
        '<button class="btn btn-primary" style="display: block; width: 100%;"'
        + 'data-toggle="collapse" href="#dispatchForm" onclick="beginDispatching()">'
        + 'Dispatch'
        + '</button>'
    );
    $('#dispatchForm').collapse('hide');
    $('#ambulance_info_collapse').collapse('show');

}

var removeFromDispatchingList = function(ambulance) {

    // delete from dispatching list
    delete dispatchingAmbulances[ambulance.id];
    numberOfDispatchingAmbulances--;

    // show message if last button
    if (numberOfDispatchingAmbulances == 0)
        $('#ambulance-selection-message').show();

}

var addToDispatchingList = function(ambulance) {

    // quick return if null or not dispatching
    if (ambulance == null || !isDispatching)
        return;

    // add ambulance to dispatching list
    console.log('Adding ambulance ' + ambulance.identifier + ' to dispatching list');

    // already in?
    if (ambulance.id in dispatchingAmbulances) {
        console.log('Already in dispatching list, skip');
        return;
    }

    // not available?
    if (ambulance.status != STATUS_AVAILABLE) {
        console.log('Ambulance is not available');
        alert('Can only dispatch available ambulances!');
        return;
    }

    // hide message if first button
    if (numberOfDispatchingAmbulances == 0)
        $('#ambulance-selection-message').hide();

    // add ambulance to list of dispatching ambulances
    dispatchingAmbulances[ambulance.id] = ambulance;
    numberOfDispatchingAmbulances++;

    // add button to ambulance dispatch grid
    $('#ambulance-selection').append(
        '<button id="dispatch-button-' + ambulance.id + '"'
        + ' value="' + ambulance.id + '"'
        + ' type="button" class="btn btn-sm btn-success"'
        + ' style="margin: 2px 2px;"'
        + ' draggable="true">'
        + ambulance.identifier
        + '</button>'
    );
    $('#dispatch-button-' + ambulance.id)
        .on('dragstart', function (e) {
            // on start of drag, copy information and fade button
            console.log('dragstart');
            this.style.opacity = '0.4';
            e.originalEvent.dataTransfer.setData("text/plain", ambulance.id);
        })
        .on('dragend', function (e) {
            console.log('dragend');
            if (e.originalEvent.dataTransfer.dropEffect == 'none') {
                // Remove button if not dropped back
                removeFromDispatchingList(ambulance);
                // Remove button
                $(this).remove();
            } else {
                // Restore opacity if dropped back in
                this.style.opacity = '1.0';
            }
        });
}

var updateCurrentLocation = function(location) {

    console.log('Setting current location to: ' + location.lat + ', ' + location.lng);

    // set currentLocation
    currentLocation = location;

    // update coordinates on form
    $('#curr-lat').html(currentLocation.lat);
    $('#curr-lng').html(currentLocation.lng);

    // remove existing marker
    markersGroup.clearLayers();

    // laydown marker
    var marker = L.marker(location,
        {
            icon: placeIcon,
            draggable: true
        })
        .addTo(markersGroup);
    markersGroup.addTo(mymap);

    // pan to location
    mymap.panTo(location);

    // events
    marker.on('dragend', function(e) {

        // update current location
        updateCurrentLocation(marker.getLatLng());

        // update address?
        if ($('#update-address').prop('checked'))
            updateCurrentAddress(currentLocation);

    })

}

var updateCurrentAddress = function(location) {

    var options = {
        types: 'address',
        limit: 1
    };
    geocoder.reverse(location, options,
        function (results, status) {

        if (status != "success") {
            alert("Could not geocode:\nError " + status + ", " + results['error']);
            return;
        }

        // quick return if found nothing
        if (results.length == 0) {
            console.log('Got nothing from geocode');
            return;
        }

        // parse features into current address
        currentAddress = geocoder.parse_feature(results[0]);

        console.log(
            'Setting currentAddress to:'
            + '\nnumber: ' + currentAddress['number']
            + '\nstreet: ' + currentAddress['street']
            + '\nunit: ' + currentAddress['unit']
            + '\nlocation: ' + currentAddress['location']['latitude']
            + ',' + currentAddress['location']['longitude']
            + '\nneighborhood: ' + currentAddress['neighborhood']
            + '\nzipcode: ' + currentAddress['zipcode']
            + '\ncity: ' + currentAddress['city']
            + '\nstate: ' + currentAddress['state']
            + '\ncountry: ' + currentAddress['country']
        );

        // set input text
        $('#street').val(currentAddress['street_address']);

    });

}

var updateCoordinates = function() {

    // when the user changes the street address
    var address =$('#street').val();

    // quick return if no address
    if (!address)
        return;

    // otherwise geocode and update
    var options = {
        types: 'address',
        limit: 1,
        autocomplete: 'true'
    };
    geocoder.geocode(address, options,
        function (results, status) {

            if (status != "success") {
                alert("Could not geocode:\nError " + status + ", " + results['error']);
                return;
            }

            // quick return if found nothing
            if (results.length == 0) {
                console.log('Got nothing from geocode');
                return;
            }

            // parse features into address
            var address = geocoder.parse_feature(results[0]);

            console.log(
                'Setting currentLocation to:'
                + '\nnumber: ' + address['number']
                + '\nstreet: ' + address['street']
                + '\nunit: ' + address['unit']
                + '\nlocation: ' + address['location']['latitude']
                + ',' + address['location']['longitude']
                + '\nneighborhood: ' + address['neighborhood']
                + '\nzipcode: ' + address['zipcode']
                + '\ncity: ' + address['city']
                + '\nstate: ' + address['state']
                + '\ncountry: ' + address['country']
            );

            // set current location
            updateCurrentLocation({
                lat: address['location']['latitude'],
                lng: address['location']['longitude']
            });

        });
}

// connect actions to inputs

$("#street").change(function () {

    // update coordinates?
    if ($('#update-coordinates').prop('checked'))
        updateCoordinates();

});


$('#update-coordinates').change(function() {

    // update coordinates?
    if ($('#update-coordinates').prop('checked'))
        updateCoordinates();

});

$('#update-address').change(function() {

    // update address?
    if ($('#update-address').prop('checked'))
        updateCurrentAddress(currentLocation);

});

$('#dispatchForm').submit(function (e) {

    // prevent normal form submission
    e.preventDefault();

    // dispatch call
    dispatchCall();

});



/*
 * dispatchCall makes an ajax post request to post dispatched ambulance.
 * @param void.
 * @return void.
 */
function dispatchCall() {

    var form = {};

    // call information
    form['details'] = $('#comment').val();
    form['priority'] = $('input:radio[name=priority]:checked').val();

    // checks
    if (form["priority"] === undefined) {
        alert("Please click one of priorities");
        return;
    }
    if (numberOfDispatchingAmbulances == 0) {
        alert("Please dispatch at least one ambulance");
        return;
    }

    // address information
    form['number'] = currentAddress['number'];
    form['street'] = currentAddress['street'];
    form['unit'] = currentAddress['unit'];
    form['neighborbood'] = currentAddress['neighborhood'];
    form['city'] = currentAddress['city'];
    form['state'] = currentAddress['state'];
    form['country'] = currentAddress['country'];
    form['zipcode'] = currentAddress['zipcode'];
    form['location'] = currentAddress['location'];

    // ambulances
    var ambulances = [];
    for (var id in dispatchingAmbulances)
        if (dispatchingAmbulances.hasOwnProperty(id))
            ambulances.push(id);
    form['ambulances'] = ambulances;

    // TODO: patients

    // make json call
    let postJsonUrl = 'api/call/';
    console.log("Will post '" + JSON.stringify(form) + "'");

    var CSRFToken = getCookie('csrftoken');

    // retrieve csrf token
    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!CSRFSafeMethod(settings.type)) {
                xhr.setRequestHeader("X-CSRFToken", CSRFToken);
            }
        }
    })

    // make ajax call
    $.ajax({
        url: postJsonUrl,
        type: 'POST',
        dataType: 'json',
        data: form,
        success: function (data) {

            // alert(JSON.stringify(data));
            var successMsg = '<strong>Success</strong><br/>' +
                +'Ambulance: ' + data['ambulance']
                + ' dispatched to <br/>' + data['residential_unit']
                + ', ' + data['stmain_number'] + ', ' + data['latitude'] + ', ' + data['longitude'];

            // Show modal
            $('.modal-title').append('Dispatch suceeded');
            $('.modal-body').html(successMsg).addClass('alert-success');
            $("#dispatchModal").modal('show');

            endDispatching();
        },
        error: function (jqXHR, textStatus, errorThrown) {

            // Show modal
            $('.modal-title').append('Dispatch failed');
            $('.modal-body').html(textStatus + ": " + errorThrown).addClass('alert-danger');
            $("#dispatchModal").modal('show');

            endDispatching();
        }
    });
}

function CSRFSafeMethod(method) {
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

/*
 * getCookie extracts the csrf token for form submit
 */
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = $.trim(cookies[i]);
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
