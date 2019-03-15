const observer = require('../observer');

test('observer subscribe', () => {

    const observer = new observer.Observer();
    const fn = () => {};
    observer.subscribe(fn);
    expect(observer.observers.length).toBe(1);

});

