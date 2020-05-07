import { logger } from './logger';

let apiClient;

// add initialization hook
add_init_function(init);

// initialization function
function init (client) {

    logger.log('info', '> video.js');

    // set apiClient
    apiClient = client;

}

$(function () {

})
