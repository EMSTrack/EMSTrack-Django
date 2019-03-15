/**
 * Topic observer pattern base class
 */
export class TopicObserver {

    constructor() {
        this.observers = { __all__: [] };
    }

    observe(fn, topic) {

        // default is all
        topic = topic || '__all__';

        // create topic if needed
        if (!this.observers.hasOwnProperty(topic))
            this.observers[topic] = [];

        this.observers[topic].push(fn);
    }

    remove(fn, topic) {

        // default is all
        topic = topic || '__all__';

        this.observers = this.observers[topic].filter((subscriber) => subscriber !== fn);
    }

    broadcast(data, topic) {

        // default is all
        topic = topic || '__all__';

        // is that a particular topic?
        if (topic !== '__all__')
            this.observers[topic].forEach((subscriber) => subscriber(data));

        // broadcast for all
        this.observers['__all__'].forEach((subscriber) => subscriber(data));
    }

}