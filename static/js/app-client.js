import { logger } from "./logger";

import { TopicObserver } from "./topic-observer";

export class AppClient extends TopicObserver {
    
    /**
     *
     * @param {MqttClient} mqttClient
     * @param httpClient
     */
    constructor(mqttClient, httpClient) {

        // call super
        super();

        // mqtt client
        this.mqttClient = mqttClient;
        this.event_observer = null;

        // register observer
        this.event_observer = (event) => this._eventHandler(event);
        this.mqttClient.observe(this.event_observer);

        // http client
        this.httpClient = httpClient;

        // initialize
        this.ambulances = undefined;
        this.hospitals = undefined;
        this.locations = undefined;
        this.calls = undefined;

        // observer methods
        this.updateAmbulance = (message) => { this._updateAmbulance(message) };
        this.updateHospital = (message) => { this._updateHospital(message) };
        this.updateCall = (message) => { this._updateCall(message) };
        this.updateAmbulanceCallStatus = (message) => { this._updateAmbulanceCallStatus(message) };

    }

    disconnect() {

        // return if not connected
        if (!this.mqttClient.isConnected)
            return;

        // remove observer
        this.mqttClient.remove(this.event_observer);
        this.event_observer = null;

        // connect to client
        this.mqttClient.disconnect();

    }

    publish(topic, payload, qos, retained) {
        this.mqttClient.publish(topic, payload, qos, retained);
    }

    retrieveCallRadioCode() {

        // initialized if needed
        const radio_code = {};

        // retrieve radio code
        return this.httpClient.get('radio/')
            .then( (response) => {

                // Update radio code
                response.data.forEach( (code) => {

                    // update radio_code
                    radio_code[code.id] = code;

                });

                // return radio_code
                return radio_code;

            })

    }

    retrieveCallPriorityCode() {

        // initialized if needed
        const priority_code = {};

        // retrieve priority code
        return this.httpClient.get('priority/')
            .then( (response) => {

                // Update priority code
                response.data.forEach( (code) => {

                    // update priority_code
                    priority_code[code.id] = code;

                });

                // return priority_code
                return priority_code;

            })

    }

    retrieveCallPriorityClassification() {

        // initialized if needed
        const priority_classification = {};

        // retrieve priority classification
        return this.httpClient.get('priority/classification/')
            .then( (response) => {

                // Update priority classification
                response.data.forEach( (classification) => {

                    // update priority_classification
                    priority_classification[classification.id] = classification.label;

                });

                // return priority_classification
                return priority_classification;

            })

    }

    retrieveAmbulances() {

        // initialize if needed
        if (typeof this.ambulances === 'undefined')
            this.ambulances = {};

        // retrieve ambulances
        return this.httpClient.get('ambulance/')
            .then( (response) => {

                // Update ambulances
                response.data.forEach( (ambulance) => {
                    
                    // update ambulance
                    this.ambulances[ambulance.id] = ambulance;
                    
                    // subscribe
                    // TODO: check if already subscribed
                    this._subscribe('ambulance/' + ambulance.id + '/data',
                        this.updateAmbulance);
                    this._subscribe('ambulance/' + ambulance.id + '/call/+/status',
                        this.updateAmbulanceCallStatus);
                    
                });

                // return ambulances
                return this.ambulances;

            })

    }
    
    retrieveHospitals() {
        
        // initialize if needed
        if (typeof this.hospitals === 'undefined')
            this.hospitals = {};

        // retrieve hospitals
        return this.httpClient.get('hospital/')
            .then( (response) => {
                
                // Update hospitals
                response.data.forEach( (hospital) => {
                    
                    // update hospital
                    this.hospitals[hospital.id] = hospital;
                    
                    // subscribe
                    // TODO: check if already subscribed
                    this._subscribe('hospital/' + hospital.id + '/data',
                        this.updateHospital);
                    
                });

                // return hospitals
                return this.hospitals;

            })

    }

    retrieveCalls() {
        
        // initialize if needed
        if (typeof this.calls === 'undefined')
            this.calls = {};

        // retrieve calls
        return this.httpClient.get('call/')
            .then( (response) => {
                
                // Update calls
                response.data.forEach( (call) => {
                    
                    // update call
                    this.calls[call.id] = call;
                    
                    // subscribe
                    // TODO: check if already subscribed
                    this._subscribe('call/' + call.id + '/data',
                        this.updateCall);
                    
                });

                // return calls
                return this.calls;

            })

    }

    retrieveLocations(type) {

        // initialize if needed
        if (typeof this.locations === 'undefined')
            this.locations = {};

        if (typeof this.locations[type] === 'undefined')
            this.locations[type] = {};

        // retrieve bases
        return this.httpClient.get('location/' + type + '/')
            .then( (response) => {

                // Update bases
                const locations = this.locations[type];
                response.data.forEach( (location) => {

                    // update base
                    locations[location.id] = location;

                });

                // return bases
                return this.locations[type];

            })

    }


    // private methods

    // subscribe methods

    _subscribe(filter, fn, options = {qos:2}) {
        logger.log('debug', "subscribing to '%s'", filter);
        this.mqttClient.subscribe(filter, options);
        this.observe(filter, fn)
    }

    _unsubscribe(filter, fn, options = {}) {
        logger.log('debug', "unsubscribing from '%s'", filter);
        this.mqttClient.unsubscribe(filter, options);
        this.remove(filter, fn)
    }


    // observer methods

    _updateAmbulance(message) {
        const ambulance = message.payload;
        this.ambulances[ambulance.id] = ambulance;
    }

    _updateHospital(message) {
        const hospital = message.payload;
        this.hospitals[hospital.id] = hospital;
    }

    _updateCall(message) {
        const call = message.payload;

        if (call.status === 'E')
        // call ended? remove
            this._removeCall(call);
        else
        // update
            this.calls[call.id] = call;
    }

    _updateAmbulanceCallStatus(message) {
        const status = message.payload;

        // get ambulance and call ids
        const topic = message.topic.split('/');
        const ambulance_id = topic[1];
        const call_id = topic[3];

        // is this a new call?
        logger.log('debug', "Received ambulance '%d' call '%d' status '%s'", ambulance_id, call_id, status);
        if ( !this.calls.hasOwnProperty(call_id) && status !== 'C' ) {

            // retrieve call from api
            this.httpClient.get('call/' + call_id + '/')
                .then( (response) => {

                    // add call
                    this._addCall(response.data);

                })
                .catch( (error) => {
                    logger.log('error', "Could not retrieve call with id '%d': '%s'", call_id, error);
                });

        }

    }

    _addCall(call) {

        // update call
        this.calls[call.id] = call;

        // subscribe
        const topic = 'call/' + call.id + '/data';
        this._subscribe(topic, this.updateCall);

        // broadcast new call update
        // this is necessary in case mqtt publication of new call is too fast
        this.broadcast(topic, {topic: topic, payload: call});

    }

    _removeCall(call) {

        // unsubscribe call
        this._unsubscribe('call/' + call.id + '/data', this.updateCall);

        // delete call
        delete this.calls[call.id];

    }

    // mqtt event handler

    /**
     *
     * @param {MqttEvent} event
     */
    _eventHandler(event) {

        logger.log('debug', "event: '%j'", event);

        if (event.event === 'messageArrived') {

            const topic = event.object.destinationName;
            let payload;
            try {
                payload = JSON.parse(event.object.payloadString);
            } catch(e) {
                logger.warn('Could not parse incoming message.');
                payload = event.object.payloadString;
            }

            // broadcast
            logger.log('debug', "message: '%j'", {topic: topic, payload: payload});
            this.broadcast(topic, {topic: topic, payload: payload});

        } else if (event.event === 'messageSent') {
            /* ignore */
        } else if (event.event === 'connect') {
            /* ignore */
        } else if (event.event === 'lostConnection') {
            /* ignore */
        } else
            logger.log('warn', "Unknown event type '%s'", event.event);

    }

}
