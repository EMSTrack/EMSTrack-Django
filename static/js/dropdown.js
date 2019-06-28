export class Dropdown {

    constructor(parameters) {

        const properties = Object.assign({...Dropdown.default}, parameters);

        this.options = properties.options;
        this.value = properties.value;
        this.prefix = properties.prefix;
        this.label = properties.label;
        this.onClick = properties.onClick;
    }

    render(classes = "") {

        // language=HTML
        let html = `<div class="dropdown ${classes}"
    id="${this.prefix}-type-menu">
    <button class="btn btn-outline-dark btn-sm dropdown-toggle" type="button" 
            id="${this.prefix}-type-menu-button" 
            data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
        <span id="${this.prefix}-type-menu-button-label">
            ${this.value < 0 ? this.label : this.options[this.value]}
        </span>
    </button>
    <div class="dropdown-menu"
         id="${this.prefix}-dropdown-menu" 
         aria-labelledby="${this.prefix}-type-menu-button">`;

        let index = 0;
        this.options.forEach((option) => {

            html += `        <a class="dropdown-item small "
        id="${this.prefix}-menu-item-value-${index}" 
        href="#">${option['label']}</a>`;

            index += 1;
        });

        // language=HTML
        html += `    </div>
</div>`;

        return html;
    }

    postRender() {

        // reference to this to be used inside method
        const self = this;

        // initialize dropdown
        $(`#${this.prefix}-type-menu .dropdown-toggle`)
            .dropdown({
                boundary: 'viewport'
            });

        $(`#${this.prefix}-type-menu a`)
            .click(function () {

                // copy to label
                $(`#${self.prefix}-type-menu-button-label`)
                    .text($(this).text());

                // get index
                const values = $(this).prop("id").split('-');
                const value = values[value.length - 1];

                self.onClick(value, options[value]);

            });

        // dropdown clipping issue
        // see https://stackoverflow.com/questions/31829312/bootstrap-dropdown-clipped-by-overflowhidden-container-how-to-change-the-conta
        $(`#${this.prefix}-type-menu`).on('show.bs.dropdown', function () {
            const selector = $(`#${self.prefix}-dropdown-menu`);
            const offset = selector.offset();
            $('body')
                .append(
                    selector.css({
                        position: 'absolute',
                        left: offset.left,
                        top: offset.top,
                        'z-index': 1100
                    }).detach());
        });

        $(`#${this.prefix}-type-menu`).on('hidden.bs.dropdown', function () {
            const selector = $(`#${self.prefix}-dropdown-menu`);
            $(`#${self.prefix}-item-type`)
                .append(selector.css({
                    position: false,
                    left: false,
                    top: false
                }).detach());
        });

    }

}

Dropdown.default = {
    options: [],
    initial: -1,
    prefix: "dropdown",
    label: "Select:",
    onClick: () => {}
};

