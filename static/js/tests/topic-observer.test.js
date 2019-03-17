const expect = require('chai').expect;

import { TopicObserver } from "../topic-observer";

describe('topic observer', () => {

    const observer = new TopicObserver();
    const fn3 = () => {};

    it('should observe topic', function() {

        expect(observer.observers.contains('topic')).to.equal(false);
        observer.observe('topic', fn3);
        expect(observer.observers.contains('topic')).to.equal(true);
        expect(observer.observers.matches('topic')).to.equal(true);

    });

    it('should remove topic', function() {

        observer.remove('topic', fn3);
        expect(observer.observers.contains('topic')).to.equal(true);
        expect(observer.observers.get('topic')).to.eql({'topic': []});

    });

    it('should receive topic', function () {

        let subscriberHasBeenCalled = false;
        const fn4 = (data) => subscriberHasBeenCalled = data;

        observer.observe('topic', fn4);
        observer.broadcast('topic', true);
        expect(subscriberHasBeenCalled).to.equal(true);
        observer.remove('topic', fn4);

    });

    const fn5 = () => {};

    it('should observe pattern', function() {

        expect(observer.observers.contains('topic/+/all')).to.equal(false);
        observer.observe('topic/+/all', fn5);
        expect(observer.observers.contains('topic/+/all')).to.equal(true);
        expect(observer.observers.matches('topic/+/all')).to.equal(true);
        expect(observer.observers.matches('topic/1/all')).to.equal(true);
        expect(observer.observers.matches('topic/1/alla')).to.equal(false);

    });

    it('should remove pattern', function() {

        observer.remove('topic/+/all', fn5);
        expect(observer.observers.get('topic/+/all')).to.eql({ '/^topic\\/[^\\/]+\\/all$/': []});

    });

    it('should receive pattern', function () {

        let subscriberHasBeenCalled = false;
        const fn4 = (data) => subscriberHasBeenCalled = data;

        observer.observe('topic/+/all', fn4);
        expect(observer.observers.matches('topic/some/all')).to.equal(true);

        observer.broadcast('topic/some/all', true);
        expect(subscriberHasBeenCalled).to.equal(true);

        observer.remove('topic/+/all', fn4);

    });

});
