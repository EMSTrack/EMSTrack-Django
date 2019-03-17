import { MqttDict } from "./mqtt-dict";

/**
 * Topic observer pattern base class
 */
ALL = '__all__';

export class TopicObserver {

    constructor() {
        this.observers = new MqttDict();
        this.observers.create(ALL);
    }

    observe(fn, topic) {

        // default is all
        topic = topic || ALL;

        // push topic
        this.observers.push(topic, fn);
    }

    remove(fn, topic) {

        // default is all
        topic = topic || ALL;

        this.observers.remove(topic, fn);
    }

     broadcast(data, topic) {

        // default is all
        topic = topic || ALL;

        // is that a particular topic?
        if (topic !== ALL) {

            // match topics and broadcast
            const objects = this.observers.get(topic);
            if (objects.length > 0)
                objects.forEach(
                    (array) => array.forEach((subscriber) => subscriber(data))
                );
            else
                console.warn('No topics matched!');

        }

        // broadcast for all
         this.observers.get(ALL)[0].forEach((subscriber) => subscriber(data));
    }

}