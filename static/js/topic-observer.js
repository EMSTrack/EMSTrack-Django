/**
 * Topic observer pattern base class
 */
export class TopicObserver {

    constructor() {
        this.observers = { __all__: [] };
    }

    static topicToRegex(topic) {

        // Parse topic
        let regex = topic;
        if (regex.indexOf('+') >= 0) {
            regex = regex.replace(/\+/g, "[^/]+");
        }
        if (regex.indexOf('#') === regex.length - 1) {
            regex = regex.replace("#", "[a-zA-Z0-9_/ ]+");
        }
        // Invalid topic
        if (regex.indexOf('#') >= 0) {
            throw new Error("Invalid topic '" + topic + "'");
        }

        // compile regex?
        if (topic !== regex)
            return new RegExp(regex);
        else
            return topic;
    }

    observe(fn, topic) {

        // default is all
        topic = topic || '__all__';

        // compile topic as regex if needed
        if (topic !== '__all__') {
            topic = TopicObserver.topicToRegex(topic);
        }

        // create topic if needed
        if (!this.observers.hasOwnProperty(topic))
            this.observers[topic] = [];

        this.observers[topic].push(fn);
    }

    remove(fn, topic) {

        // default is all
        topic = topic || '__all__';

        // compile topic as regex if needed
        if (topic !== '__all__') {
            topic = TopicObserver.topicToRegex(topic);
        }

        this.observers[topic] = this.observers[topic].filter((subscriber) => subscriber !== fn);
    }

    hasTopic(topic) {
        return this.observers.hasOwnProperty(topic);
    }

    getTopics(pattern) {
        const keys = this.observers.keys();
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