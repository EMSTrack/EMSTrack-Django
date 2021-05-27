add_init_function(init);

// TODO track multiple panics 
let panics = [];

function init(client) {
    // set apiClient
    apiClient = client;

    // signup for panic updates
    apiClient.observe('ambulance/+/panic', (message) => {handlePanic(message.payload)});
}

function handlePanic(ambulance) {
    console.log('test');

    // display video modal
    $('#panicModalWindow').modal({
        backdrop: 'static',
        keyboard: false,
        show: true
    });  

}