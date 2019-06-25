import { MqttClient } from "./mqtt-client";

import { AppClient } from "./app-client";

import { logger } from './logger';

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
    if (pathname.split('/').length > 3) {

        // Make current page active
        $('.nav-item a[href^="' + pathname + '"]').addClass('nav-item active');

        if (typeof adminUrls === 'undefined' || adminUrls === null) {
             // variable is undefined or null
            logger.log('info', 'User is not admin');
        } else {
            // Make admin menu active
            if (adminUrls.includes(pathname))
                $('#navitemDropdown').addClass('nav-item active');
        }

    }

    // quick return if logged off
    if (username === '')
        return;

    // initialize ApiClient
    let mqttClient;
    let apiClient;
    const httpClient = axios.create({
        baseURL: apiBaseUrl,
        xsrfCookieName: Cookies.get('csrftoken'),
        xsrfHeaderName: 'X-CSRFToken'
    });

    // retrieve temporary password for mqttClient and connect to broker
    // logger.log('info', 'ApiBaseUrl: ' + apiBaseUrl);
    logger.log('info', 'Retrieving MQTT password');
    httpClient.get('user/' + username + '/password/')
        .then( (response) => {

            // got password
            const password = response.data;
            mqttClient = new MqttClient(mqttBroker.host, mqttBroker.port, clientId, 2);

            logger.log('info', 'Connecting to MQTT broker');
            return mqttClient.connect({
                userName: username,
                password: password
            });

        })
        .then( () => {

            // instantiate client
            logger.log('info', 'Instantiating ApiClient');
            apiClient = new AppClient(mqttClient, httpClient);

            // retrieve ambulances
            logger.log('info', 'Retrieving ambulances');
            return apiClient.retrieveAmbulances();

        })
        .then( (ambulances) => {
            logger.log('info', Object.keys(ambulances).length + ' ambulances retrieved');

            // retrieve calls
            logger.log('info', 'Retrieving calls');
            return apiClient.retrieveCalls();
        })
        .then( (calls) => {
            logger.log('info', Object.keys(calls).length + ' calls retrieved');

            // calling initialization function
            logger.log('info', 'Calling initialization functions');
            init_functions.forEach( (fn) => fn(apiClient) );
        })
        .catch( (error ) => {
            logger.log('error', 'Failed to initialize ApiClient');
            logger.log('error', error);
        });

});
