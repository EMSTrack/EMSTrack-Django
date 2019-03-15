const expect = require('chai').expect;

import { Observer } from "../observer";

describe('observer subscribe', () => {

    const observer = new Observer();
    const fn1 = () => {};

    context('subscribe',
        () => { it('should subscribe',
            () => {
                observer.subscribe(fn1);
                expect(observer.observers.length).to.equal(1)
            })
        })

    context('unsubscribe',
        () => { it('should unsubscribe',
                () => {
                    observer.unsubscribe(fn1);
                    expect(observer.observers.length).to.equal(0);
                })
        });

    let subscriberHasBeenCalled = false;
    const fn2 = (data) => subscriberHasBeenCalled = data;

    context('broadcast',
        () => {
            it('should receive',
                () => {
                    observer.subscribe(fn2);
                    observer.broadcast(true);
                    expect(subscriberHasBeenCalled).to.equal(true);
                })
        });

});
