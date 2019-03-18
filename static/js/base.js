import { MqttClient } from "./mqtt-client";

import { AppClient } from "./app-client";

const axios = require('axios');

let apiClient;

// Ready function
$(function () {

    let mqttClient;
    const httpClient = axios.create({
        baseURL: ApiBaseUrl
    });

    // retrieve temporary password for mqttClient and connect to broker
    console.log('Retrieving MQTT password from ' + ApiBaseUrl);
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
            console.log(Object.keys(ambulances).length + ' ambulances retrieved.');
            console.log('Done initializing ApiClient');
        })
        .catch( (error ) => {
            console.log('Failed to initialize ApiClient');
            console.log(error);
        });

});
