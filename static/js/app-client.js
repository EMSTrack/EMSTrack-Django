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
        this.event_observer = (event) => this.eventHandler(event);
        this.mqttClient.observe(this.event_observer);

        // http client
        this.httpClient = httpClient;

        // initialize
        this.ambulances = undefined;
        this.hospitals = undefined;
        this.bases = undefined;
        this.calls = undefined;

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

    /**
     *
     * @param {MqttEvent} event
     */
    eventHandler(event) {

        console.log(event);

        if (event.event === 'messageReceived') {

            const topic = event.object.destinationName;
            const payload = JSON.parse(event.object.payloadString);

            console.log(topic);
            console.log(payload);

            // broadcast
            this.broadcast(topic, {topic: topic, payload: payload});

        }

    }

    subscribe(filter, fn, options) {
        options = options || {};
        this.mqttClient.subscribe(filter, options);
        this.observe(filter, fn)
    }

    unsubscribe(filter, fn, options) {
        options = options || {};
        this.mqttClient.unsubscribe(filter, options);
        this.remove(filter, fn)
    }

    publish(topic, payload, qos, retained) {
        this.mqttClient.publish(topic, payload, qos, retained);
    }

    updateAmbulance(message) {
        const ambulance = message.payload;
        this.ambulances[ambulance.id] = ambulance;
    }

    updateHospital(message) {
        const hospital = message.payload;
        this.hospitals[hospital.id] = hospital;
    }

    updateCall(message) {
        const call = message.payload;
        this.call[call.id] = call;
    }

    updateAmbulanceCallStatus(message) {

        const status = message.payload;

        // get ambulance and call ids
        const topic = message.topic.split('/');
        // const ambulance_id = topic[1];
        const call_id = topic[3];

        if ( !this.calls.hasOwnProperty(call_id) && status !== 'C' ) {

            // retrieve call from api
            this.httpClient.get('call/' + call_id + '/')
                .then( (call) => {

                    // update call
                    this.calls[call.id] = call;

                    // subscribe
                    this.subscribe('call/' + call.id + '/data', this.updateCall);

            });

        }

    }

    retrieveAmbulances() {

        // initialized if needed
        if (typeof this.ambulances === 'undefined')
            this.ambulances = {};

        // retrieve ambulances
        this.httpClient.get('ambulance/')
            .then( (response) => {

                // console.log(response.data);

                // Update ambulances
                response.data.forEach( (ambulance) => {
                    
                    // update ambulance
                    this.ambulances[ambulance.id] = ambulance;
                    
                    // subscribe
                    // TODO: check if already subscribed
                    this.subscribe('ambulance/' + ambulance.id + '/data',
                        this.updateAmbulance);
                    this.subscribe('ambulance/' + ambulance.id + '/call/+/status',
                        this.updateAmbulanceCallStatus);
                    
                });
                
            })
            .catch( (error) => {
                console.log('retrieveAmbulance: ' + error);
            });

    }
    
    retrieveHospitals() {
        
        // initialized if needed
        if (typeof this.hospitals === 'undefined')
            this.hospitals = {};

        // retrieve ambulances
        this.httpClient.get('hospital/')
            .then( (response) => {
                
                // Update hospitals
                response.data.forEach( (hospital) => {
                    
                    // update hospital
                    this.hospitals[hospital.id] = hospital;
                    
                    // subscribe
                    // TODO: check if already subscribed
                    this.subscribe('hospital/' + hospital.id + '/data', this.updateHospital);
                    
                });
                
            })
            .catch( (error) => {
                console.log('retrieveHospital: ' + error);
            });

    }

    retrieveCalls() {
        
        // initialized if needed
        if (typeof this.calls === 'undefined')
            this.calls = {};

        // retrieve ambulances
        this.httpClient.get('call/')
            .then( (response) => {
                
                // Update calls
                response.data.forEach( (call) => {
                    
                    // update call
                    this.calls[call.id] = call;
                    
                    // subscribe
                    // TODO: check if already subscribed
                    this.subscribe('call/' + call.id + '/data', this.updateCall);
                    
                });
                
            })
            .catch( (error) => {
                console.log('retrievecall: ' + error);
            });

    }

    retrieveBases() {

        // initialized if needed
        if (typeof this.bases === 'undefined')
            this.bases = {};

        // retrieve ambulances
        this.httpClient.get('location/Base/')
            .then( (response) => {

                // Update bases
                response.data.forEach( (base) => {

                    // update base
                    this.bases[base.id] = base;

                });

            })
            .catch( (error) => {
                console.log('retrieveBase: ' + error);
            });

    }

}
