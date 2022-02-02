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

    // get value and comment fields
    const prefix = select.getAttribute('id').replace('-equipment', '');
    const valueField = $(`#${prefix}-value`);
    const commentField = $(`#${prefix}-comment`);

    // disable value and comment
    valueField.prop('disabled', true);
    commentField.prop('disabled', true);

    if (value !== "") {

        apiClient.getEquipmentMetadata(value)
            .then( (equipment) => {
                logger.log('debug', "Got equipment metadata");

                if (equipment.type === 'B') {
                    valueField.attr('type', 'checkbox');
                    valueField.attr('checked', equipment.default);
                } else {
                    if (equipment.type === 'I') {
                        valueField.attr('type', 'number');
                    } else if (equipment.type === 'S') {
                        valueField.attr('type', 'text');
                    }
                    valueField.attr('value', equipment.default);
                }

                // enable fields
                valueField.prop('disabled', false);
                commentField.prop('disabled', false);

            })
            .catch( (error) => {
                logger.log('error', 'Failed to retrieve equipment metadata: %s', error);
            });

    }

}

// https://stackoverflow.com/questions/34357489/calling-webpacked-code-from-outside-html-script-tag
window.equipmentSelected = equipmentSelected;
