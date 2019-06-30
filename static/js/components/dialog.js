import {logger} from "../logger";

export class Dialog {

    constructor(parameters) {
        const properties = Object.assign({...Dialog.default}, parameters);

        this.label = properties.label;
        this.title = properties.title;
        this.body = properties.body;
        this.bodyClasses = properties.bodyClasses;
        this.okButtonShow = properties.okButtonShow;
        this.cancelButtonShow = properties.cancelButtonShow;
        this.closeButtonShow = properties.closeButtonShow;
        this.onSelect = properties.onSelect;
    }

    render(classes="") {

        return `<div id="${this.label}-modal" class="modal fade" role="dialog">
    <div class="modal-dialog ${classes}">
        <!-- Modal content-->
        <div class="modal-content">
            <div class="modal-header">
                <h4 id="${this.label}-modal-title" class="modal-title"></h4>
                <button type="button" class="close" data-dismiss="modal">
                    <span aria-hidden="true">&times;</span>
                </button>
            </div>
            <div id="${this.label}-modal-body" class="modal-body">
            </div>
            <div class="modal-footer">
                <button id="${this.label}-modal-button-ok" type="button" class="btn btn-primary" data-dismiss="modal">
                    ${translation_table['Ok']}
                </button>
                <button id="${this.label}-modal-button-cancel" type="button" class="btn btn-secondary" data-dismiss="modal">
                    ${translation_table['Cancel']}
                </button>
                <button id="${this.label}-modal-button-close" type="button" class="btn btn-secondary" data-dismiss="modal">
                    ${translation_table['Close']}
                </button>
            </div>
        </div>
    </div>
</div>`;

    }

    show(options) {

        options = Object.assign(Object.assign({}, this), options);

        // Show modal
        if (options.okButtonShow)
            $(`#${this.label}-modal-button-ok`).show();
        else
            $(`#${this.label}-modal-button-ok`).hide();

        if (options.cancelButtonShow)
            $(`#${this.label}-modal-button-cancel`).show();
        else
            $(`#${this.label}-modal-button-cancel`).hide();

        if (options.closeButtonShow)
            $(`#${this.label}-modal-button-close`).show();
        else
            $(`#${this.label}-modal-button-close`).hide();

        // set title
        $(`#${this.label}-modal-title`)
            .text(options.title);

        // set body
        $(`#${this.label}-modal-body`)
            .empty()
            .append(options.body);

        // set classes
        $(`#${this.label}-modal-body`)
            .attr( "class", "modal-body" );
        if (options.bodyClasses.trim() !== '')
            $(`#${this.label}-modal-body`)
                .addClass(options.bodyClasses);

        $(`#${this.label}-modal`)
            .off('hide.bs.modal')
            .on('hide.bs.modal', () => {

                const $activeElement = $(document.activeElement);
                if ($activeElement.is('[data-toggle], [data-dismiss]')) {

                    if ($activeElement.attr('id') === `${this.label}-modal-button-ok`)
                        options.onSelect(Dialog.OK);
                    else if ($activeElement.attr('id') === `${this.label}-modal-button-cancel`)
                        options.onSelect(Dialog.CANCEL);
                    else if ($activeElement.attr('id') === `${this.label}-modal-button-close`)
                        options.onSelect(Dialog.CLOSE);

                }

            })
            .modal(options.modalOptions);

    }

    alert(message, alertClass = 'alert-danger', title) {

        // Show modal
        title = title || translation_table['Alert'];

        // dialog
        this.show({
            modalOptions: {
                backdrop: 'static'
            },
            title: title,
            body: message,
            bodyClasses: alertClass,
            okButtonShow: false,
            cancelButtonShow: false,
            closeButtonShow: true,
        });

    }

}

Dialog.default = {
    label: '',
    title: 'Modal Title',
    body: 'Modal Body',
    bodyClasses: '',
    modalOptions: { show: true },
    okButtonShow: true,
    cancelButtonShow: true,
    closeButtonShow: true,
    onSelect: (retval) => { logger.log('debug', 'dialog: returned %s', retval)},
};

Dialog.OK = 'OK';
Dialog.CANCEL = 'CANCEL';
Dialog.CLOSE = 'CLOSE';