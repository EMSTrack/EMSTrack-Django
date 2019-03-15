const expect = require('chai').expect;
const assert = require('chai').assert;

import { Observer } from "../observer";

describe('observer subscribe', () => {

    const observer = new Observer();
    const fn = () => {};
    observer.subscribe(fn);

    context('subscribe',
        () => { it('should return 0',
            () => {

                expect(observer.observers.length).to.equal(1)
            })
        })
    
});
