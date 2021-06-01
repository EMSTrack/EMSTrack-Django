add_init_function(init);

// TODO track multiple panics 
let panics = [];
let isDisplayed = false; 

function init(client) {
    logger.log('info', '> panic.js');

    // set apiClient
    apiClient = client;

    // signup for panic updates
    logger.log('info', 'Signing up for panic updates');
    apiClient.observe('ambulance/+/panic', (message) => {handlePanic(message.payload)});
}

$(function () {
    // TODO define click behavior of button  

    $('#videoPanicWindow').on('hide.bs.modal', function (e) {
        isDisplayed = false; 
        promptPanic();
    });
})

function promptPanic() {
    if(isDisplayed || panics.length === 0) {
        return; 
    }

    const message = panics.pop();

    // if we published it, do nothing 
    if(message.type === 'acknolwedge') {
        return;
    }

    // add panic content
    // TODO add map with ambulance highlighted
    $('#panicModalBody').append(
        `<div class="row">
            <div class="col">
                <h2>Ambulance: ${message.ambulance}</h2>
                <h2>Call Identifier: ${message.call}</h2>
                <h2>Location Last Updated: ${message.time}</h2>
            </div>
            <div class="col">
                <img src="https://www.google.com/maps/d/u/0/thumbnail?mid=19H5OPnebQva3tPbEXOu1MgfSwKc" alt="MAP GOES HERE">
            </div>
        </div>`
    );

    // display panic modal
    isDisplayed = true;
    $('#panicModalWindow').modal({
        backdrop: 'static',
        keyboard: false,
        show: true
    });  
}

function handlePanic(payload) {
    panics.push(payload);
    promptPanic();
}