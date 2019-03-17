import { MqttDict } from "./mqtt-dict";

/**
 * Topic observer pattern base class
 */
export class TopicObserver {

    constructor() {
        this.observers = new MqttDict();
        this.observers.create('__ALL__');
    }

    observe(fn, topic) {

        // default is '__ALL__'
        topic = topic || '__ALL__';

        // push topic
        this.observers.push(topic, fn);
    }

    remove(fn, topic) {

        // default is '__ALL__'
        topic = topic || '__ALL__';

        this.observers.remove(topic, fn);
    }

     broadcast(data, topic) {

        // default is '__ALL__'
        topic = topic || '__ALL__';

        // is that a particular topic?
        if (topic !== '__ALL__') {

            // match topics and broadcast
            const objects = this.observers.get(topic);
            if (objects.length > 0)
                objects.forEach(
                    (array) => array.forEach((subscriber) => subscriber(data))
                );
            else
                console.warn('No topics matched!');

        }

        // broadcast for '__ALL__'
         this.observers.get('__ALL__')[0].forEach((subscriber) => subscriber(data));
    }

}