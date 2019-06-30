import {logger} from "../logger";

export class Dialog {

    constructor(parameters) {
        const properties = Object.assign({...Dialog.default}, parameters);

        this.label = properties.label;
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

        options = Object.assign(options, this);

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
            $(`#${this.label}-modal-button-close`).show();

        $(`#${this.label}-modal`)
            .off('hide.bs.modal')
            .on('hide.bs.modal', function(event) {

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

}

Dialog.default = {
    label: '',
    modalOptions: { show: true },
    okButtonShow: true,
    cancelButtonShow: true,
    closeButtonShow: true,
    onSelect: (retval) => { logger.log('debug', 'dialog: returned %s', retval)},
};

Dialog.OK = 'OK';
Dialog.CANCEL = 'CANCEL';
Dialog.CLOSE = 'CLOSE';