import { MqttClient } from "./mqtt-client";

import { AppClient } from "./app-client";

const axios = require('axios');

// initialization
let init_functions = [];
global.add_init_function = function add_init_function(fn) {
    init_functions.push(fn)
};

// Ready function
$(function () {

    // make current page active
    const pathname = window.location.pathname;

    // exclude home page
    if (!pathname.match(/\/[^\/]*\//)) {
        // Make current page active
        $('.nav-item a[href^="' + pathname + '"]').addClass('nav-item active');

        // Make admin menu active
        if (adminUrls.findIndex(pathname) !== -1)
            $('#navitemDropdown').addClass('nav-item active');

    }

    // quick return if logged off
    if (username === '')
        return;

    // initialize ApiClient
    let mqttClient;
    let apiClient;
    const httpClient = axios.create({
        baseURL: apiBaseUrl
    });

    // retrieve temporary password for mqttClient and connect to broker
    console.log('ApiBaseUrl: ' + apiBaseUrl);
    console.log('Retrieving MQTT password');
    httpClient.get('user/' + username + '/password/')
        .then( (response) => {

            // got password
            const password = response.data;
            mqttClient = new MqttClient(mqttBroker.host, mqttBroker.port, clientId);

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

            // retrieve calls
            console.log('Retrieving calls');
            return apiClient.retrieveCalls();
        })
        .then( (calls) => {
            console.log(Object.keys(calls).length + ' calls retrieved');

            // calling initialization function
            console.log('Calling initialization functions');
            init_functions.forEach( (fn) => fn(apiClient) );
        })
        .catch( (error ) => {
            console.log('Failed to initialize ApiClient');
            console.log(error);
        });

});
