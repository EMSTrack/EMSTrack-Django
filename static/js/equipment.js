import { logger } from './logger';

let apiClient;

// add initialization hook
add_init_function(init);

// initialization function
function init (client) {

    logger.log('info', '> equipment.js');

    // set apiClient
    apiClient = client;

}

function equipmentSelected(select, value) {
    console.log('equipment selected: ' + value);
    console.log(select);
    const prefix = select.getAttribute('id').replace('-equipment', '');
    console.log(prefix);
    const disabled = value === "";
    $(`#${prefix}-value`).prop('disabled', disabled);
    $(`#${prefix}-comment`).prop('disabled', disabled);
}

