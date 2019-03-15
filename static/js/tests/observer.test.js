import expect from 'chai';

import { Observer } from "../observer";

describe('observer subscribe', () => {

    const observer = new Observer();
    const fn = () => {};
    observer.subscribe(fn);
    expect(observer.observers.length).to.equal(1);

});
