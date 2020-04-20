import { logger } from "../logger";

export class Select {

    constructor(parameters) {

        const properties = Object.assign({...Select.default}, parameters);

        this.options = properties.options;
        this.prefix = properties.prefix;
        this.list = properties.list;
        this.label = properties.label;
        this.values = properties.values;
        this.initial_values = properties.initial_values;
        this.onClick = properties.onClick;
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

        // set initial values
        for (const value of this.initial_values) {
            const item = $(`#${self.list} option[data-id=${value}]`);
            if (item.length) {
                const first = item.first();
                this.addItem(first.attr('data-id'), first.attr('value'));
            }
        }

        // initialize select
        $(`#${this.prefix}-select-input`).on('change', function() {

            // process selection
            const value = $(this).val();
            const item = $(`#${self.list} option[value=${value}]`);
            if (item.length) {
                const id = item.first().attr('data-id');
                self.addItem(id, value);
            }
            // clear selection
            $(this).val('');

        });

    }

    getItems() {
        return this.values;
    }

    resetItems() {
        this.values = {};
    }

    removeItem(id, value) {

        // remove from list of values
        delete this.values[id];

        // remove li element
        $(`#${this.prefix}-select-li-${id}`).remove();
    }

    addItem(id, value) {

        logger.debug("Select: got click");

        if (!this.values.hasOwnProperty(id)) {

            logger.debug("Adding '%d -> %s' to list", id, value);

            // add to list of values
            this.values[id] = value;

            // create list entry
            const li = $(`<div id="${this.prefix}-select-li-${id}">
                <li>
                    ${value}
                    <button type="button" class="close" aria-label="Close">
                        <span aria-hidden="true">&times;</span>
                    </button>
                </li>
            </div>`);
            li.on('click', () => this.removeItem(id, value));

            $(`#${this.prefix}-select-ul`).append(li);

        } else {

            logger.debug("'%d -> %s' already present, skipping", id, value);

        }

    }

}

Select.default = {
    options: {},
    values: {},
    initial_values: [],
    list: "",
    prefix: "dropdown",
    label: "Select:",
    onClick: (value) => { logger.log('info', 'click: %s', value); }
};
