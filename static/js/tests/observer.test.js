const expect = require('chai').expect;
const assert = require('chai').assert;

import { Observer } from "../observer";

describe('observer subscribe', () => {

    const observer = new Observer();
    const fn = () => {};
    observer.subscribe(fn);
    assert.lengthOf(observer.observers.length, 1, 'has length 1');

});
