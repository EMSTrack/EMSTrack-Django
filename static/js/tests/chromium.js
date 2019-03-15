const {runner} = require('mocha-headless-chrome');

const options = {
    file: 'mqtt.test.html',                      // test page path
    reporter: 'dot',                             // mocha reporter name
    width: 800,                                  // viewport width
    height: 600,                                 // viewport height
    timeout: 120000,                             // timeout in ms
    visible: true,                               // show chrome window
    args: ['--no-sandbox']                       // chrome arguments
};

runner(options)
    .then(result => {
        let json = JSON.stringify(result);
        console.log(json);
    });