var expect = require('chai').expect;

import { Observer } from "../observer";

describe('observer subscribe', () => {

    const observer = new Observer();
    const fn = () => {};
    observer.subscribe(fn);
    expect(observer.observers.length).to.equal(1);

    expect(1).to.equal(1);

});
