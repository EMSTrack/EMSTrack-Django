
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
            return new RegExp('^' + regex + '$');
        else
            return topic;

    }

    push(topic, obj) {

        const key = MqttDict.topicToRegex(topic);

        // create topic if needed
        if (!this.dict.hasOwnProperty(topic)) {
            this.dict[key] = {key: key, array: []};
            this.keys = Object.keys(this.dict);
        }

        this.dict[key].array.push(obj);

    }

    remove(topic, obj) {

        const key = MqttDict.topicToRegex(topic);

        this.dict[key].array = this.dict[key].array.filter((subscriber) => subscriber !== obj);

    }

    matchAll(topic) {

        const topics = [];
        for (let i = 0; i < this.keys.length; i++) {
            const key = this.keys[i];
            const regexp = this.dict[key].key;
            if (MqttDict.matchStringOrRegExp(regexp, topic))
                topics.push(key);
        }

        return topics;

    }

    matchFirst(topic) {

        for (let i = 0; i < this.keys.length; i++) {
            const key = this.keys[i];
            const regexp = this.dict[key].key;
            if (MqttDict.matchStringOrRegExp(regexp, topic))
                return key;
        }

        return null;

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
