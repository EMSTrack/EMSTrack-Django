add_init_function(init);

function init(client) {
    // set apiClient
    apiClient = client;

    // signup for panic updates
    apiClient.observe('ambulance/+/panic', (message) => {handlePanic(message.payload)});
}

function handlePanic(ambulance) {
    // TODO
}
