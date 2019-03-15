import { Observer } from "../observer";

test('observer subscribe', () => {

    const observer = new Observer();
    const fn = () => {};
    observer.subscribe(fn);
    expect(observer.observers.length).toBe(1);

});
