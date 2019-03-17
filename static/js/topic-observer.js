import { MqttDict } from "./mqtt-dict";

/**
 * Topic observer pattern base class
 */
export class TopicObserver {

    constructor() {
        this.observers = new MqttDict();
    }

    observe(topic, fn) {
        this.observers.push(topic, fn);
    }

    remove(topic, fn) {
        this.observers.remove(topic, fn);
    }

    broadcast(topic, data) {

         // match topics and broadcast
         const objects = this.observers.get(topic);
         if (objects.length > 0)
             Object.values(objects).forEach(
                 (value) => value.forEach((subscriber) => subscriber(data))
             );
         else
             console.warn('No topics matched!');

    }

}