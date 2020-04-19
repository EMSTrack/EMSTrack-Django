import { logger } from "../logger";

export class Select {

    constructor(parameters) {

        const properties = Object.assign({...Select.default}, parameters);

        this.options = properties.options;
        this.prefix = properties.prefix;
        this.list = properties.list;
        this.label = properties.label;
        this.values = properties.values;
        this.onClick = properties.onClick;

        this.last_index = 0;
    }

    render(classes = "") {

        // language=HTML
        let html = `<input class="form-control form-control-sm"
                   id="${this.prefix}-select-input" list="${this.list}"
                   name="${this.prefix}-select-input"
                   placeholder="${this.label}">
           <ul class="${classes}"
               id="${this.prefix}-select-ul">
           </ul>`;

        return html;
    }

    postRender() {

        // reference to this to be used inside method
        const self = this;

        // initialize select
        $(`#${this.prefix}-select-input`).on('change', function() {

            // process selection
            const value = $(this).val();
            const id = $(`#${self.list} option[value=${value}]`).attr('data-id');
            self.click(key, id);

            // clear selection
            $(this).val('');

        });

    }

    click(key, id) {

        logger.debug("Select: got click");

        if (!this.values.hasOwnProperty(id)) {

            logger.debug("Adding '%d -> %s' to list", id, key);

            // add to list of values
            this.values[id] = key;
            $(`#${this.prefix}-select-ul`).append(
                `<li id="${this.prefix}-select-li-${this.last_index++}">
                   ${key}
                 </li>`
            );

        } else {

            logger.debug("'%d -> %s' already present, skipping", id, key);

        }

    }

}

Select.default = {
    options: {},
    values: {},
    list: "",
    prefix: "dropdown",
    label: "Select:",
    onClick: (value) => { logger.log('info', 'click: %s', value); }
};
