const expect = require('chai').expect;

import { TopicObserver } from "../topic-observer";

describe('topic observer', () => {

    const observer = new TopicObserver();
    const fn1 = () => {};

    it('should observe all', function() {

        observer.observe(fn1);
        expect(observer.observers['__all__'].length).to.equal(1)

    });

    it('should remove all', function() {

        observer.remove(fn1);
        expect(observer.observers['__all__'].length).to.equal(0);

    });

    it('should receive all', function () {

        let subscriberHasBeenCalled = false;
        const fn2 = (data) => subscriberHasBeenCalled = data;

        observer.observe(fn2);
        observer.broadcast(true);
        expect(subscriberHasBeenCalled).to.equal(true);
        observer.remove(fn2);

    });


    const fn3 = () => {};

    it('should observe topic', function() {

        expect(observer.observers.hasTopic('topic')).to.equal(false);
        observer.observe(fn3, 'topic');
        expect(observer.observers['topic'].length).to.equal(1);
        expect(observer.observers.hasTopic('topic')).to.equal(true);

    });

    it('should remove topic', function() {

        observer.remove(fn3, 'topic');
        expect(observer.observers['topic'].length).to.equal(0);

    });

    it('should receive topic', function () {

        let subscriberHasBeenCalled = false;
        const fn4 = (data) => subscriberHasBeenCalled = data;

        observer.observe(fn4, 'topic');
        observer.broadcast(true, 'topic');
        expect(subscriberHasBeenCalled).to.equal(true);
        observer.observe(fn4, 'topic');

    });

});
