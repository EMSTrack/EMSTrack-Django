const expect = require('chai').expect;

import { MqttDict } from "../mqtt-dict";

describe('mqtt-dict strings', () => {

    const dict = new MqttDict();

    it('push and remove', function () {

        const obj1 = "object1";
        const key1 = 'string1';
        dict.push(key1, obj1);
        expect(Object.keys(dict.dict).length).to.equal(1);
        expect(dict.dict[key1].key).to.equal(key1);
        expect(Object.keys(dict.dict[key1].array).length).to.equal(1);

        const obj2 = "object2";
        dict.push(key1, obj2);
        expect(Object.keys(dict.dict).length).to.equal(1);
        expect(Object.keys(dict.dict[key1].array).length).to.equal(2);

        const key2 = 'string2';
        dict.push(key2, obj1);
        expect(Object.keys(dict.dict).length).to.equal(2);
        expect(dict.dict[key2].key).to.equal(key2);
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

    });

});