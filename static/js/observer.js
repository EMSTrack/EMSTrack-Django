/**
 * Observer pattern base class
 */
export class Observer {

    constructor() {
        this.observers = [];
    }

    observe(fn) {
        this.observers.push(fn);
    }

    remove(fn) {
        this.observers = this.observers.filter((subscriber) => subscriber !== fn);
    }

    broadcast(data) {
        this.observers.forEach((subscriber) => subscriber(data));
    }

}