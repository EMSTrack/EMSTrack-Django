const expect = require('chai').expect;

import { MqttDict } from "../mqtt-dict";

describe('valid topics', () => {

    it('valid keys', function () {

        let pattern = 'topic/+/data';
        let regexp = new RegExp('^topic/[^/]+/data$');
        expect(MqttDict.topicToRegex(pattern)).to.eql(regexp);

        pattern = 'topic/+/data/+/status';
        regexp = new RegExp('^topic/[^/]+/data/[^/]+/status$');
        expect(MqttDict.topicToRegex(pattern)).to.eql(regexp);

        pattern = 'topic/+/data/#';
        regexp = new RegExp('^topic/[^/]+/data/[a-zA-Z0-9_/ ]+$');
        expect(MqttDict.topicToRegex(pattern)).to.eql(regexp);

    });

    it('invalid keys', function () {

        let pattern = 'topic/#/data/#';
        expect(() => MqttDict.topicToRegex(pattern)).to.throw();

        pattern = 'topic/+/data/#/';
        expect(() => MqttDict.topicToRegex(pattern)).to.throw();

    });

});

describe('mqtt-dict strings', () => {

    it('push and remove', function () {

        const dict = new MqttDict();

        const obj1 = "object1";
        const key1 = 'string1';
        dict.push(key1, obj1);
        expect(Object.keys(dict.dict).length).to.equal(1);
        expect(dict.dict[key1].regexp).to.equal(key1);
        expect(Object.keys(dict.dict[key1].array).length).to.equal(1);

        const obj2 = "object2";
        dict.push(key1, obj2);
        expect(Object.keys(dict.dict).length).to.equal(1);
        expect(Object.keys(dict.dict[key1].array).length).to.equal(2);

        const key2 = 'string2';
        dict.push(key2, obj1);
        expect(Object.keys(dict.dict).length).to.equal(2);
        expect(dict.dict[key2].regexp).to.equal(key2);
        expect(Object.keys(dict.dict[key1].array).length).to.equal(2);
        expect(Object.keys(dict.dict[key2].array).length).to.equal(1);

        dict.remove(key1, obj2);
        expect(Object.keys(dict.dict).length).to.equal(2);
        expect(Object.keys(dict.dict[key1].array).length).to.equal(1);
        expect(Object.keys(dict.dict[key2].array).length).to.equal(1);

        dict.remove(key2, obj1);
        expect(Object.keys(dict.dict).length).to.equal(2);
        expect(Object.keys(dict.dict[key1].array).length).to.equal(1);
        expect(Object.keys(dict.dict[key2].array).length).to.equal(0);

        let objects = dict.get(key1);
        expect(Object.keys(objects).length).to.equal(1);
        expect(objects[key1].length).to.equal(1);
        expect(objects[key1]).to.eql([obj1]);

        objects = dict.get(key2);
        expect(Object.keys(objects).length).to.equal(1);
        expect(objects[key2].length).to.equal(0);
        expect(objects[key2]).to.eql([]);

        const key3 = 'new_key';
        dict.create(key3);
        expect(Object.keys(dict.dict).length).to.equal(3);
        expect(Object.keys(dict.dict[key1].array).length).to.equal(1);
        expect(Object.keys(dict.dict[key2].array).length).to.equal(0);
        expect(Object.keys(dict.dict[key3].array).length).to.equal(0);

    });

});

describe('mqtt-dict topics', () => {

    it('push and remove simple', function () {

        const dict = new MqttDict();

        const obj1 = "object1";
        const key1 = 'topic/1/data';
        dict.push(key1, obj1);
        expect(Object.keys(dict.dict).length).to.equal(1);
        expect(dict.dict[key1].regexp).to.equal(key1);
        expect(Object.keys(dict.dict[key1].array).length).to.equal(1);

        const obj2 = "object2";
        dict.push(key1, obj2);
        expect(Object.keys(dict.dict).length).to.equal(1);
        expect(Object.keys(dict.dict[key1].array).length).to.equal(2);

        const key2 = 'topic/2/data';
        dict.push(key2, obj1);
        expect(Object.keys(dict.dict).length).to.equal(2);
        expect(dict.dict[key2].regexp).to.equal(key2);
        expect(Object.keys(dict.dict[key1].array).length).to.equal(2);
        expect(Object.keys(dict.dict[key2].array).length).to.equal(1);

        dict.remove(key1, obj2);
        expect(Object.keys(dict.dict).length).to.equal(2);
        expect(Object.keys(dict.dict[key1].array).length).to.equal(1);
        expect(Object.keys(dict.dict[key2].array).length).to.equal(1);

        dict.remove(key2, obj1);
        expect(Object.keys(dict.dict).length).to.equal(2);
        expect(Object.keys(dict.dict[key1].array).length).to.equal(1);
        expect(Object.keys(dict.dict[key2].array).length).to.equal(0);

        let objects = dict.get(key1);
        expect(Object.keys(objects).length).to.equal(1);
        expect(objects[key1].length).to.equal(1);
        expect(objects[key1]).to.eql([obj1]);

        objects = dict.get(key2);
        expect(Object.keys(objects).length).to.equal(1);
        expect(objects[key2].length).to.equal(0);
        expect(objects[key2]).to.eql([]);

    });

    it('push and remove pattern', function () {

        const dict = new MqttDict();

        const obj1 = "object1";
        const pattern1 = 'topic/+/data';
        const regexp1 = new RegExp('^topic/[^/]+/data$');
        const key1 = regexp1.toString();

        dict.push(pattern1, obj1);
        expect(Object.keys(dict.dict).length).to.equal(1);
        expect(Object.keys(dict.dict)).to.eql([key1]);

        expect(dict.dict[key1].regexp).to.eql(regexp1);
        expect(Object.keys(dict.dict[key1].array).length).to.equal(1);

        const obj2 = "object2";
        dict.push(pattern1, obj2);
        expect(Object.keys(dict.dict).length).to.equal(1);
        expect(Object.keys(dict.dict[key1].array).length).to.equal(2);

        const key2 = 'topic/2/data';
        dict.push(key2, obj1);
        expect(Object.keys(dict.dict).length).to.equal(2);
        expect(dict.dict[key2].regexp).to.equal(key2);
        expect(Object.keys(dict.dict[key1].array).length).to.equal(2);
        expect(Object.keys(dict.dict[key2].array).length).to.equal(1);

        dict.remove(pattern1, obj2);
        expect(Object.keys(dict.dict).length).to.equal(2);
        expect(Object.keys(dict.dict[key1].array).length).to.equal(1);
        expect(Object.keys(dict.dict[key2].array).length).to.equal(1);

        dict.remove(key2, obj1);
        expect(Object.keys(dict.dict).length).to.equal(2);
        expect(Object.keys(dict.dict[key1].array).length).to.equal(1);
        expect(Object.keys(dict.dict[key2].array).length).to.equal(0);

        let objects = dict.get(pattern1);
        expect(Object.keys(objects).length).to.equal(1);
        expect(objects[key1].length).to.equal(1);
        expect(objects[key1]).to.eql([obj1]);

        objects = dict.get(key2);
        expect(Object.keys(objects).length).to.equal(2);
        expect(objects[key1].length).to.equal(1);
        expect(objects[key1]).to.eql([obj1]);
        expect(objects[key2].length).to.equal(0);
        expect(objects[key2]).to.eql([]);

    });

    it('push and remove pattern 2', function () {

        const dict = new MqttDict();

        const obj1 = "object1";
        const pattern1 = 'topic/+/call/+/data';
        const regexp1 = new RegExp('^topic/[^/]+/call/[^/]+/data$');
        const key1 = regexp1.toString();

        dict.push(pattern1, obj1);
        expect(Object.keys(dict.dict).length).to.equal(1);
        expect(Object.keys(dict.dict)).to.eql([key1]);

        expect(dict.dict[key1].regexp).to.eql(regexp1);
        expect(Object.keys(dict.dict[key1].array).length).to.equal(1);

        const obj2 = "object2";
        dict.push(pattern1, obj2);
        expect(Object.keys(dict.dict).length).to.equal(1);
        expect(Object.keys(dict.dict[key1].array).length).to.equal(2);

        const key2 = 'topic/2/call/3/data';
        dict.push(key2, obj1);
        expect(Object.keys(dict.dict).length).to.equal(2);
        expect(dict.dict[key2].regexp).to.equal(key2);
        expect(Object.keys(dict.dict[key1].array).length).to.equal(2);
        expect(Object.keys(dict.dict[key2].array).length).to.equal(1);

        dict.remove(pattern1, obj2);
        expect(Object.keys(dict.dict).length).to.equal(2);
        expect(Object.keys(dict.dict[key1].array).length).to.equal(1);
        expect(Object.keys(dict.dict[key2].array).length).to.equal(1);

        dict.remove(key2, obj1);
        expect(Object.keys(dict.dict).length).to.equal(2);
        expect(Object.keys(dict.dict[key1].array).length).to.equal(1);
        expect(Object.keys(dict.dict[key2].array).length).to.equal(0);

        let objects = dict.get(pattern1);
        expect(Object.keys(objects).length).to.equal(1);
        expect(objects[key1].length).to.equal(1);
        expect(objects[key1]).to.eql([obj1]);

        objects = dict.get(key2);
        expect(Object.keys(objects).length).to.equal(2);
        expect(objects[key1].length).to.equal(1);
        expect(objects[key1]).to.eql([obj1]);
        expect(objects[key2].length).to.equal(0);
        expect(objects[key2]).to.eql([]);

    });

    it('push and remove pattern 3', function () {

        const dict = new MqttDict();

        const obj1 = "object1";
        const pattern1 = 'topic/#';
        const regexp1 = new RegExp('^topic/[a-zA-Z0-9_/ ]+$');
        const key1 = regexp1.toString();

        dict.push(pattern1, obj1);
        expect(Object.keys(dict.dict).length).to.equal(1);
        expect(Object.keys(dict.dict)).to.eql([key1]);

        expect(dict.dict[key1].regexp).to.eql(regexp1);
        expect(Object.keys(dict.dict[key1].array).length).to.equal(1);

        const obj2 = "object2";
        dict.push(pattern1, obj2);
        expect(Object.keys(dict.dict).length).to.equal(1);
        expect(Object.keys(dict.dict[key1].array).length).to.equal(2);

        const key2 = 'topic/2/call/3/data';
        dict.push(key2, obj1);
        expect(Object.keys(dict.dict).length).to.equal(2);
        expect(dict.dict[key2].regexp).to.equal(key2);
        expect(Object.keys(dict.dict[key1].array).length).to.equal(2);
        expect(Object.keys(dict.dict[key2].array).length).to.equal(1);

        dict.remove(pattern1, obj2);
        expect(Object.keys(dict.dict).length).to.equal(2);
        expect(Object.keys(dict.dict[key1].array).length).to.equal(1);
        expect(Object.keys(dict.dict[key2].array).length).to.equal(1);

        dict.remove(key2, obj1);
        expect(Object.keys(dict.dict).length).to.equal(2);
        expect(Object.keys(dict.dict[key1].array).length).to.equal(1);
        expect(Object.keys(dict.dict[key2].array).length).to.equal(0);

        let objects = dict.get(pattern1);
        expect(Object.keys(objects).length).to.equal(1);
        expect(objects[key1].length).to.equal(1);
        expect(objects[key1]).to.eql([obj1]);

        objects = dict.get(key2);
        expect(Object.keys(objects).length).to.equal(2);
        expect(objects[key1].length).to.equal(1);
        expect(objects[key1]).to.eql([obj1]);
        expect(objects[key2].length).to.equal(0);
        expect(objects[key2]).to.eql([]);

    });

    it('push and remove pattern 3', function () {

        const dict = new MqttDict();

        const obj1 = "object1";
        const pattern1 = 'topic/+/call/#';
        const regexp1 = new RegExp('^topic/[^/]+/call/[a-zA-Z0-9_/ ]+$');
        const key1 = regexp1.toString();

        dict.push(pattern1, obj1);
        expect(Object.keys(dict.dict).length).to.equal(1);
        expect(Object.keys(dict.dict)).to.eql([key1]);

        expect(dict.dict[key1].regexp).to.eql(regexp1);
        expect(Object.keys(dict.dict[key1].array).length).to.equal(1);

        const obj2 = "object2";
        dict.push(pattern1, obj2);
        expect(Object.keys(dict.dict).length).to.equal(1);
        expect(Object.keys(dict.dict[key1].array).length).to.equal(2);

        const key2 = 'topic/2/call/3/data';
        dict.push(key2, obj1);
        expect(Object.keys(dict.dict).length).to.equal(2);
        expect(dict.dict[key2].regexp).to.equal(key2);
        expect(Object.keys(dict.dict[key1].array).length).to.equal(2);
        expect(Object.keys(dict.dict[key2].array).length).to.equal(1);

        dict.remove(pattern1, obj2);
        expect(Object.keys(dict.dict).length).to.equal(2);
        expect(Object.keys(dict.dict[key1].array).length).to.equal(1);
        expect(Object.keys(dict.dict[key2].array).length).to.equal(1);

        dict.remove(key2, obj1);
        expect(Object.keys(dict.dict).length).to.equal(2);
        expect(Object.keys(dict.dict[key1].array).length).to.equal(1);
        expect(Object.keys(dict.dict[key2].array).length).to.equal(0);

        let objects = dict.get(pattern1);
        expect(Object.keys(objects).length).to.equal(1);
        expect(objects[key1].length).to.equal(1);
        expect(objects[key1]).to.eql([obj1]);

        objects = dict.get(key2);
        expect(Object.keys(objects).length).to.equal(2);
        expect(objects[key1].length).to.equal(1);
        expect(objects[key1]).to.eql([obj1]);
        expect(objects[key2].length).to.equal(0);
        expect(objects[key2]).to.eql([]);

    });


});