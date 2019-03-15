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

    matchAllTopics(topic) {
        const topics = [];
        const array = Object.keys(this.observers);
        for(let i = 0; i < array.length; i++) {
            const regex = array[i];
            let match = false;
            if (regex instanceof RegExp) {
                match = regex.exec(topic)
            } else {
                match = regex === topic;
            }
            if (match)
                topics.add(regex);
        }
        return topics;
    }

    matchTopic(topic) {
        const array = Object.keys(this.observers);
        for(let i = 0; i < array.length; i++) {
            const regex = array[i];
            let match = false;
            if (regex instanceof RegExp) {
                match = regex.exec(topic)
            } else {
                match = regex === topic;
            }
            if (match)
                return regex;
        }
        return null;
    }

    hasTopic(topic) {
        return this.matchTopic(TopicObserver.topicToRegex(topic)) !== null;
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