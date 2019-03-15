/**
 * Observer pattern base class
 */
export class Observer {

    constructor() {
        this.observers = [];
    }

    subscribe(fn) {
        this.observers.push(fn);
    }

    unsubscribe(fn) {
        this.observers = this.observers.filter((subscriber) => subscriber !== fn);
    }

    broadcast(data) {
        this.observers.forEach((subscriber) => subscriber(data));
    }

}