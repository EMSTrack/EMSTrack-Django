/* Dispatch area - Should be eliminate after dispatching */

var markersGroup = new L.LayerGroup();
var isDispatching = false;
var placeIcon = L.icon({
    iconUrl: '/static/icons/place_marker.png',
    iconSize: [50, 50], // size of the icon
});
var dispatchingAmbulances = {};

var beginDispatching = function () {
   
    isDispatching = true;
    console.log('Begin dispatching.');
    
    document.getElementById('dispatch_work').innerHTML 
        = '<button type="button" class="btn btn-link" onclick="endDispatching()">'
        + '<span class="glyphicon glyphicon-chevron-left"></span>'
        + 'Go back'
        + '</button>';
    $('#dispatchForm').collapse('show');
    $('#collapse1').collapse('hide');
    $('#collapse2').collapse('hide');

    mymap.on('click', function (e) {

        markersGroup.clearLayers();
        document.getElementById('curr-lat').innerHTML = e.latlng.lat;
        document.getElementById('curr-lng').innerHTML = e.latlng.lng;
        if (isDispatching) {
            L.marker([e.latlng.lat, e.latlng.lng], {icon: placeIcon}).addTo(markersGroup);
            markersGroup.addTo(mymap);
        }
        
    });

}

var endDispatching = function () {
    
    isDispatching = false;
    dispatchingAmbulances = {};
    console.log('End dispatching.');
    
    markersGroup.clearLayers();
    document.getElementById('dispatch_work').innerHTML 
        = '<button class="btn btn-primary" style="display: block; width: 100%;"' 
        + 'data-toggle="collapse" href="#dispatchForm" onclick="beginDispatching()">'
        + 'Dispatch'
        + '</button>';
    $('#dispatchForm').collapse('hide');
    $('#collapse1').collapse('show');
    $('#collapse2').collapse('show');
    
}

var handleDispatchDrop = function(e) {

    // button was dropped
    console.log('Dropped!');

}

var addToDispatchingList = function(ambulance) {

    if (isDispatching && !(ambulance.id in dispatchingAmbulances)) {

        // Available
        if (ambulance.status != STATUS_AVAILABLE) {
            alert('Can only dispatch available ambulances!');
            return;
        }

        // add ambulance to list of dispatching ambulances
        dispatchingAmbulances[ambulance.id] = true;

        // add button to grid
        $('#ambulance-selection').append(
            '<button id="dispatch-button-' + ambulance.id + '" ' +
            'type="button" class="btn btn-sm btn-success" draggable="true">'
            + ambulance.identifier
            + '</button>'
        );
        $('#dispatch-button-' + ambulance.id)
            .on('dragstart', function(e) {
                console.log('dragstart');
                this.style.opacity = '0.4';
                e.originalEvent.dataTransfer.setData("ambulance_id", ambulance.id);
            })
            .on('dragend', function(e) {
                console.log('dragend');
                // Remove if not dropped
                if(e.originalEvent.dataTransfer.dropEffect !== 'none'){
                    $(this).remove();
                } else {
                    this.style.opacity = '1.0';
                }
            });
    }
}

$("#street").change(function (data) {

    var addressInput = document.getElementById('street').value;
    console.log('Received address: ' + addressInput);

    var geocoder = new google.maps.Geocoder();

    geocoder.geocode({address: addressInput}, function (results, status) {
        if (status == google.maps.GeocoderStatus.OK) {
            var coordinate = results[0].geometry.location;

            document.getElementById('curr-lat').innerHTML = coordinate.lat();
            document.getElementById('curr-lng').innerHTML = coordinate.lng();

            L.marker([coordinate.lat(), coordinate.lng()], {icon: placeIcon}).addTo(markersGroup);
            markersGroup.addTo(mymap);
            mymap.setView(new L.LatLng(coordinate.lat(), coordinate.lng()), 17);
        }
        else {
            alert("There is error from Google map server");
        }
    });

});

/*
 * postDispatchCall makes an ajax post request to post dispatched ambulance.
 * @param void.
 * @return void.
 */
function postDispatchCall() {
    var formData = {};
    var assigned_ambulances = [];

    // Extract form value to JSON
    formData["stmain_number"] = $('#street').val();
    formData["residential_unit"] = $('#address').val();
    formData["latitude"] = document.getElementById('curr-lat').innerHTML;
    formData["longitude"] = document.getElementById('curr-lng').innerHTML;
    formData["active"] = true
    formData["name"] = "Make Dynamic for Future"
    console.log(formData["active"])

    console.log(formData["latitude"]);
    formData["description"] = $('#comment').val();
    formData["priority"] = $('input:radio[name=priority]:checked').val();
    $('input:checkbox[name="ambulance_assignment"]:checked').each(function (i) {
        assigned_ambulances[i] = $(this).val();
    });

    if (formData["priority"] == undefined) {
        alert("Please click one of priorities");
        return;
    }

    if (assigned_ambulances.length == 0) {
        alert("Please dispatch at least one ambulance");
        return;
    }

    formData["ambulance"] = assigned_ambulances.toString();

    let postJsonUrl = 'api/calls/';
    alert(JSON.stringify(formData) + '\n' + postJsonUrl);

    var csrftoken = getCookie('csrftoken');

    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    })

    $.ajax({
        url: postJsonUrl,
        type: 'POST',
        dataType: 'json',
        data: formData,
        success: function (data) {
            // alert(JSON.stringify(data));
            var successMsg = '<strong>Success</strong><br/>' +
                +'Ambulance: ' + data['ambulance']
                + ' dispatched to <br/>' + data['residential_unit']
                + ', ' + data['stmain_number'] + ', ' + data['latitude'] + ', ' + data['longitude'];
            $('.modal-body').html(successMsg).addClass('alert-success');
            $('.modal-title').append('Successfully Dispached');
            $("#dispatchModal").modal('show');
            endDispatching();
        },
        error: function (jqXHR, textStatus, errorThrown) {
            alert(JSON.stringify(jqXHR) + ' ' + textStatus);
            $('.modal-title').append('Dispatch failed');
            $("#dispatchModal").modal('show');
            endDispatching();
        }
    });
}

function csrfSafeMethod(method) {
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

/* Functions to fill autocomplete AND to click specific locations */
function initAutocomplete() {
    // Create the autocomplete object, restricting the search to geographical
    autocomplete = new google.maps.places.Autocomplete((document.getElementById('street')),
        {types: ['geocode']});
    //autocomplete.addListener('place_changed', fillInAddress);
}