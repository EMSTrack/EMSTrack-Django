const expect = require('chai').expect;

import { Observer } from "../observer";

describe('observer', () => {

    const observer = new Observer();
    const fn1 = () => {};

    it('should observe', function() {

        observer.observe(fn1);
        expect(observer.observers.length).to.equal(1)

    });

    it('should remove', function() {

        observer.remove(fn1);
        expect(observer.observers.length).to.equal(0);

    });

    it('should receive', function () {

        let subscriberHasBeenCalled = false;
        const fn2 = (data) => subscriberHasBeenCalled = data;

        observer.observe(fn2);
        observer.broadcast(true);
        expect(subscriberHasBeenCalled).to.equal(true);

    });

});
