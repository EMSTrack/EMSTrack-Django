import { MqttClient } from "./mqtt-client";

import { AppClient } from "./app-client";

const axios = require('axios');

let apiClient;

// Ready function
$(function () {

    // make current page active
    var pathname = window.location.pathname;
    console.log("pathname = '" + pathname + "'");

    // exclude home page
    if (!pathname.match(/\/[^\/]*\//)) {
        // Make current page active
        $('.nav-item a[href^="' + pathname + '"]').addClass('nav-item active');

        if ((pathname === "{% url 'login:list-user' %}") ||
            (pathname === "{% url 'login:list-group' %}") ||
            (pathname === "{% url 'equipment:list' %}") ||
            (pathname === "{% url 'equipment:list-set' %}") ||
            (pathname === "{% url 'ambulance:location_list' %}") ||
            (pathname === "{% url 'login:list-client' %}") ||
            (pathname === "{% url 'login:restart' %}")) {

            // Make admin menu active
            $('#navitemDropdown').addClass('nav-item active');

        }

    }

    // quick return if logged off
    if (username === '')
        return;

    // initialize ApiClient
    let mqttClient;
    const httpClient = axios.create({
        baseURL: ApiBaseUrl
    });

    // retrieve temporary password for mqttClient and connect to broker
    console.log('ApiBaseUrl: ' + ApiBaseUrl);
    console.log('Retrieving MQTT password');
    httpClient.get('user/' + username + '/password/')
        .then( (response) => {

            // got password
            const password = response.data;
            mqttClient = new MqttClient(MqttBroker.host, MqttBroker.port, clientId);

            console.log('Connecting to MQTT broker');
            return mqttClient.connect({
                userName: username,
                password: password
            });

        })
        .then( () => {

            // instantiate client
            apiClient = new AppClient(mqttClient, httpClient);

            // retrieve ambulances
            console.log('Retrieving ambulances');
            return apiClient.retrieveAmbulances();

        })
        .then( (ambulances) => {
            console.log(Object.keys(ambulances).length + ' ambulances retrieved');
            console.log('Done initializing ApiClient');
        })
        .catch( (error ) => {
            console.log('Failed to initialize ApiClient');
            console.log(error);
        });

});
