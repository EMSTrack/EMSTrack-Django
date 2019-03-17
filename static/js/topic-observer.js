import { MqttDict } from "./mqtt-dict";

/**
 * Topic observer pattern base class
 */
export class TopicObserver {

    static ALL = '__all__';

    constructor() {
        this.observers = new MqttDict();
        this.observers.create(TopicObserver.ALL);
    }

    observe(fn, topic) {

        // default is all
        topic = topic || TopicObserver.ALL;

        // push topic
        this.observers.push(topic, fn);
    }

    remove(fn, topic) {

        // default is all
        topic = topic || TopicObserver.ALL;

        this.observers.remove(topic, fn);
    }

     broadcast(data, topic) {

        // default is all
        topic = topic || TopicObserver.ALL;

        // is that a particular topic?
        if (topic !== TopicObserver.ALL) {

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
         this.observers.get(TopicObserver.ALL)[0].forEach((subscriber) => subscriber(data));
    }

}