/*
 * Auxiliary functions
 */

/**
 * Convert topic to regex
 *
 * @param topic
 * @returns {*}
 */
export function topicToRegex(topic) {

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

/**
 * Matches topic to all possible entries in array of regexps.
 *
 * @param array the array of regexps
 * @param topic the topic to be matched
 * @returns {Array}
 */
export function matchAllTopics(array, topic) {

    const topics = [];
    for(let i = 0; i < array.length; i++) {
        const regex = array[i];
        let match = false;
        if (regex instanceof RegExp) {
            match = regex.exec(topic)
        } else {
            match = regex === topic;
        }
        if (match)
            topics.push(regex);
    }
    return topics;

}

/**
 * Matches topic to first possible entry in array of regexps.
 *
 * @param array the array of regexps
 * @param topic the topic to be matched
 * @returns {*}
 */
export function matchFirstTopic(array, topic) {

    console.log("topic = '" + topic + "'");
    for(let i = 0; i < array.length; i++) {
        const regex = array[i];
        let match = false;
        console.log("regex = '" + regex + "'");
        if (regex instanceof RegExp) {
            match = regex.exec(topic)
        } else {
            match = regex === topic;
        }
        console.log("match = '" + match + "'");
        if (match)
            return regex;
    }
    return null;

}

/**
 * Topic observer pattern base class
 */
export class TopicObserver {

    constructor() {
        this.observers = { __all__: [] };
        this.keys = Object.keys(this.observers);
    }

    matchesTopic(topic) {
        return matchFirstTopic(this.keys, topic) !== null;
    }

    hasTopic(topic) {
        return this.observers.hasOwnProperty(topicToRegex(topic));
    }

    observe(fn, topic) {

        // default is all
        topic = topic || '__all__';

        // compile topic as regex if needed
        if (topic !== '__all__') {
            topic = topicToRegex(topic);
        }

        // create topic if needed
        if (!this.observers.hasOwnProperty(topic)) {
            this.observers[topic] = [];
            this.keys = Object.keys(this.observers);
        }

        this.observers[topic].push(fn);
    }

    remove(fn, topic) {

        // default is all
        topic = topic || '__all__';

        // compile topic as regex if needed
        if (topic !== '__all__') {
            topic = topicToRegex(topic);
        }

        this.observers[topic] = this.observers[topic].filter((subscriber) => subscriber !== fn);
    }

     broadcast(data, topic) {

        // default is all
        topic = topic || '__all__';

        // is that a particular topic?
        if (topic !== '__all__') {

            // match topics and broadcast
            const topics = matchAllTopics(this.keys, topic);
            if (topics.length > 0)
                topics.forEach(
                    (topic) => this.observers[topic].forEach((subscriber) => subscriber(data))
                );
            else
                console.warn('No topics matched!');

        }

        // broadcast for all
        this.observers['__all__'].forEach((subscriber) => subscriber(data));
    }

}