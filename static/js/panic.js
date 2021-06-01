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

    // display panic modal
    isDisplayed = true;
}

$(function () {
    // TODO define click behavior of button 
    $('#panicModalWindow').modal({
        backdrop: 'static',
        keyboard: false,
        show: true
    });  

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