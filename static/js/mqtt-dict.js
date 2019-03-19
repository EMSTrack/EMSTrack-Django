
export class MqttDict {

    constructor() {

        this.dict = {};
        this.keys = [];

    }

    static matchStringOrRegExp(regex, topic) {
        if (regex instanceof RegExp) {
            return regex.test(topic);
        } else {
            return topic === regex;
        }
    }

    static topicToRegex(topic) {

        // deep copy
        let regex = (' ' + topic).slice(1);

        // Parse topic
        regex = regex.replace(/\+/g, "[^/]+");
        regex = regex.replace(/#$/, "[a-zA-Z0-9_/ ]+");

        // Invalid topic
        if (regex.indexOf('#') >= 0) {
            throw new Error("Invalid topic '" + topic + "'");
        }

        // compile regex?
        if (topic !== regex)
            return new RegExp('^' + regex + '$');
        else
            return topic;

    }

    // key functions

    create(topic) {

        const regexp = MqttDict.topicToRegex(topic);
        const key = regexp.toString();

        // create topic
        if (!this.dict.hasOwnProperty(key)) {
            this.dict[key] = {regexp: regexp, array: []};
            this.keys = Object.keys(this.dict);
        } else
            throw new Error("Topic '" + topic + "' already exists");

    }

    push(topic, obj) {

        const regexp = MqttDict.topicToRegex(topic);
        const key = regexp.toString();

        // create topic if needed
        if (!this.dict.hasOwnProperty(key)) {
            this.dict[key] = {regexp: regexp, array: []};
            this.keys = Object.keys(this.dict);
        }

        this.dict[key].array.push(obj);

    }

    remove(topic, obj) {

        const regexp = MqttDict.topicToRegex(topic);
        const key = regexp.toString();

        if (!this.dict.hasOwnProperty(key))
            throw new Error("Unknown topic '" + topic + "'");

        this.dict[key].array = this.dict[key].array.filter((subscriber) => subscriber !== obj);

    }

    contains(topic) {

        const regexp = MqttDict.topicToRegex(topic);
        const key = regexp.toString();

        if (this.dict.hasOwnProperty(key))
            return true;
        else
            return false;

    }

    // match functions

    matchAll(topic) {

        const topics = [];
        for (let i = 0; i < this.keys.length; i++) {
            const key = this.keys[i];
            const regexp = this.dict[key].regexp;
            if (MqttDict.matchStringOrRegExp(regexp, topic))
                topics.push(key);
        }

        return topics;

    }

    matchFirst(topic) {

        for (let i = 0; i < this.keys.length; i++) {
            const key = this.keys[i];
            const regexp = this.dict[key].regexp;
            if (MqttDict.matchStringOrRegExp(regexp, topic))
                return key;
        }

        return null;

    }

    matches(topic) {

        return this.matchFirst(topic) !== null;

    }

    get(topic) {

        const objects = {};
        const keys = this.matchAll(topic);
        if (keys.length > 0)
            keys.forEach(
                (key) => { objects[key] = this.dict[key].array; }
            );
        else
            throw new Error("Unknown topic '" + topic + "'");

        return objects;

    }

}
