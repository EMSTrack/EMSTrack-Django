/* Dispatch area - Should be eliminate after dispatching */

var markersGroup = new L.LayerGroup();
console.log("\n\n\n\n");
console.log("printining markersGroup");
console.log(markersGroup); 
var isDispatching = false;
var isFilterOpen = false;
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
var currentPatients;
var newPatientIndex;

var submitDispatching = function () {

    // submit form
    $('#dispatch-form-collapse').submit();

};

var beginDispatching = function () {

    isDispatching = true;
    var filtersDiv = $('#filtersDiv');
    isFilterOpen = filtersDiv.hasClass('show');
    console.log('Begin dispatching.');

    $('#dispatchBeginButton').hide();
    $('#dispatchSubmitButton').show();
    $('#dispatchCancelButton').show();

    // open filter and available ambulances
    filtersDiv.addClass('show');
    $('#ambulance_status').addClass('show');
    $('#ambulance_AV').addClass('show');

    // Update current location
    updateCurrentLocation(mymap.getCenter());

    // Update current address
    updateCurrentAddress(currentLocation);

    // Clear current currentPatients
    currentPatients = {};
    newPatientIndex = 0;

    // Initialize patient form
    $('#patients').empty();

    // add new patient form entry
    addPatientForm(newPatientIndex);

    // resize size
    resizeMap();

    // center map
    mymap.setView(currentLocation, mymap.getZoom());

}

var endDispatching = function () {

    isDispatching = false;
    dispatchingAmbulances = {};
    console.log('End dispatching.');

    markersGroup.clearLayers();

    $('#dispatchBeginButton').show();
    $('#dispatchSubmitButton').hide();
    $('#dispatchCancelButton').hide();

    // close dispatch panel
    $('#dispatchDiv').removeClass('show');

    if (!isFilterOpen) {
        // close filter panel
        $('#filtersDiv').removeClass('show');
    }

    // invalidate map size
    mymap.invalidateSize();

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
        bsalert('Can only dispatch available ambulances!');
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
        + ' type="button" class="btn btn-sm '+ ambulance_buttons['AV'] + '"'
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
    $('#curr-lat').html(currentLocation.lat.toFixed(6));
    $('#curr-lng').html(currentLocation.lng.toFixed(6));

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
            bsalert("Could not geocode:\nError " + status + ", " + results['error']);
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
                bsalert("Could not geocode:\nError " + status + ", " + results['error']);
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

function dispatchCall() {

    var form = {};

    // call information
    var street_address = $('#street').val().trim();
    form['details'] = $('#comment').val().trim();
    form['priority'] = $('input:radio[name=priority]:checked').val();

    // checks
    if (form["priority"] === undefined) {
        bsalert("Please select the priority level.");
        return;
    }
    if (numberOfDispatchingAmbulances == 0) {
        bsalert("Please dispatch at least one ambulance.");
        return;
    }

    // address information
    form['neighborhood'] = currentAddress['neighborhood'];
    form['city'] = currentAddress['city'];
    form['state'] = currentAddress['state'];
    form['country'] = currentAddress['country'];
    form['zipcode'] = currentAddress['zipcode'];
    form['location'] = currentAddress['location'];

    // Has the user modified the street address?
    if (street_address != currentAddress['street_address']) {

        // parse street address
        var address = geocoder.parse_street_address(street_address, form['country']);

        form['number'] = address['number'];
        form['street'] = address['street'];
        form['unit'] = address['unit'];

    } else {

        form['number'] = currentAddress['number'];
        form['street'] = currentAddress['street'];
        form['unit'] = currentAddress['unit'];

    }

    // Make sure blanks are undefined
    if (form['number'] == "") {
        form['number'] = undefined;
    }

    // ambulances
    var ambulances = [];
    for (var id in dispatchingAmbulances) {
        if (dispatchingAmbulances.hasOwnProperty(id))
            ambulances.push({ 'ambulance_id': id });
		}
    form['ambulancecall_set'] = ambulances;

    // patients
    var patients = [];
    for (var index in currentPatients)
        if (currentPatients.hasOwnProperty(index)) {
            var patient = currentPatients[index];
            var obj = { 'name': patient[0] };
            if (patient[1])
                // add age
                obj['age'] = parseInt(patient[1]);
            patients.push(obj);
        }
    form['patient_set'] = patients;

    // make json call
    var postJsonUrl = APIBaseUrl + 'call/';
    console.log("Form:");
    console.log(form);
    console.log("Will post:");
    console.log(JSON.stringify(form));

    var CSRFToken = Cookies.get('csrftoken');
    console.log('csrftoken = ' + CSRFToken);

    // retrieve csrf token
    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!CSRFSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", CSRFToken);
            }
        }
    });

    // make ajax call
    $.ajax({
        url: postJsonUrl,
        type: 'POST',
        dataType: 'json',
        contentType: 'application/json',
        data: JSON.stringify(form),
        success: function (data) {

            // Log success
            console.log("Succesfully posted new call.");

            // End dispatching
            endDispatching();

        },
        error: function (jqXHR, textStatus, errorThrown) {

            // Log failure
            console.log("Failed to post new call.");
            console.log(jqXHR.responseText);

            // Show modal
            bsalert(jqXHR.responseText, 'alert-danger', 'Failure');

            // End dispatching
            endDispatching();

        }
    });
}


// patient functions

var addPatient = function(index) {

    console.log('Adding patient index ' + index);

    var name = $('#patient-' + index + '-name').val().trim();
    var age = $('#patient-' + index + '-age').val().trim();

    // is name empty?
    if (!name) {
        bsalert('Empty name');
        return;
    }

    // add name
    currentPatients[index] = [name, age];
    newPatientIndex++;

    // change button symbol
    var symbol = $('#patient-' + index + '-symbol');
    symbol.removeClass('fa-plus');
    symbol.addClass('fa-minus');

    // change button action from add to remove
    $('#patients').find('#patient-' + index + '-button')
        .off()
        .on('click', function(e) { removePatient(index); });

    // add new form
    addPatientForm(newPatientIndex);

}

var removePatient = function(index) {

    console.log('Removing patient index ' + index);

    // remove from storage
    delete currentPatients[index];

    // remove from form
    $('#patients')
        .find('#patient-' + index + '-form')
        .remove();

}

var addPatientForm = function(index) {

    // add new patient form entry
    $('#patients').append(newPatientForm(index, 'fa-plus'));

    // bind addPatient to click
    $('#patients')
        .on('click',
            '#patient-' + index + '-button',
            function(e) { addPatient(index); });

}

var newPatientForm = function(index, symbol) {

    var html =
        '<div class="form-row" id="patient-' + index + '-form">' +
            '<div class="col-md-7 pr-0">' +
                '<input id="patient-' + index + '-name" ' +
                       'type="text" ' +
                       'class="form-control" ' +
                       'placeholder="Name">' +
            '</div>' +
            '<div class="col-md-3 px-0">' +
                '<input id="patient-' + index + '-age" ' +
                       'type="number" min="0" ' +
                       'class="form-control" ' +
                       'placeholder="Age">' +
            '</div>' +
            '<div class="col-md-2 pl-0">' +
                '<button class="btn btn-default btn-block new-patient" ' +
                       ' type="button" ' +
                       ' id="patient-' + index + '-button">' +
                    '<span id="patient-' + index + '-symbol" class="fas ' + symbol + '"></span>' +
                '</button>' +
            '</div>' +
        '</div>';

    // console.log('html = "' + html + '"');

    return html;

}

// Ready function
$(function() {

    // connect actions to inputs

    $("#street").change(function () {

        // update coordinates?
        if ($('#update-coordinates').prop('checked'))
            updateCoordinates();

    });


    $('#update-coordinates').change(function () {

        // update coordinates?
        if ($('#update-coordinates').prop('checked'))
            updateCoordinates();

    });

    $('#update-address').change(function () {

        // update address?
        if ($('#update-address').prop('checked'))
            updateCurrentAddress(currentLocation);

    });

    $('#dispatch-form-collapse').submit(function (e) {

        // prevent normal form submission
        e.preventDefault();

        // dispatch call
        dispatchCall();

    });

});

// CSRF functions

function CSRFSafeMethod(method) {
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
