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
        this.bases = undefined;
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


    retrieveAmbulances() {

        // initialized if needed
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
        
        // initialized if needed
        if (typeof this.hospitals === 'undefined')
            this.hospitals = {};

        // retrieve ambulances
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
        
        // initialized if needed
        if (typeof this.calls === 'undefined')
            this.calls = {};

        // retrieve ambulances
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

    retrieveBases() {

        // initialized if needed
        if (typeof this.bases === 'undefined')
            this.bases = {};

        // retrieve ambulances
        return this.httpClient.get('location/Base/')
            .then( (response) => {

                // Update bases
                response.data.forEach( (base) => {

                    // update base
                    this.bases[base.id] = base;

                });

                // return bases
                return this.bases;

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
            this.call[call.id] = call;
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

            logger.log('debug', "Retrieving call '%d'", call_id);

            const pause = (duration) => new Promise(res => setTimeout(res, duration));
            const backoff = (retries, fn, delay = 500) =>
                fn().catch(err => retries > 1
                    ? pause(delay).then(() => backoff(retries - 1, fn, delay * 2))
                    : Promise.reject(err));

            // retrieve call from api
            backoff(3, () => this.httpClient.get('call/' + call_id + '/'), 500)
                .then( (response) => {

                    logger.log('debug', "Retrieved call '%j'", call);

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
        this._subscribe('call/' + call.id + '/data', this.updateCall);

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
