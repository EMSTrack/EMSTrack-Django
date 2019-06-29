import {logger} from "../logger";

export class Dialog {

    constructor(parameters) {
        const properties = Object.assign({...Dialog.default}, parameters);

        this.okButtonShow = properties.okButtonShow;
        this.cancelButtonShow = properties.cancelButtonShow;
        this.closeButtonShow = properties.closeButtonShow;
        this.onSelect = properties.onSelect;
    }

    render(label, classes="") {

        return `<div id="${label}-modal" class="modal fade ${classes}" role="dialog">
    <div class="modal-dialog">
        <!-- Modal content-->
        <div class="modal-content">
            <div class="modal-header">
                <h4 id="${label}-modal-title" class="modal-title"></h4>
                <button type="button" class="close" data-dismiss="modal">
                    <span aria-hidden="true">&times;</span>
                </button>
            </div>
            <div id="${label}-modal-body" class="modal-body">
            </div>
            <div class="modal-footer">
                <button id="${label}-modal-button-ok" type="button" class="btn btn-primary" data-dismiss="modal">
                    {% trans "Ok" %}
                </button>
                <button id="${label}-modal-button-cancel" type="button" class="btn btn-secondary" data-dismiss="modal">
                    {% trans "Cancel" %}
                </button>
                <button id="${label}-modal-button-close" type="button" class="btn btn-secondary" data-dismiss="modal">
                    {% trans "Close" %}
                </button>
            </div>
        </div>
    </div>
</div>`;

    }

    show(label, options) {

        options = Object.assign(options, this);

        // Show modal
        if (options.okButtonShow)
            $(`#${label}-modal-button-ok`).show();
        else
            $(`#${label}-modal-button-ok`).hide();

        if (options.cancelButtonShow)
            $(`#${label}-modal-button-cancel`).show();
        else
            $(`#${label}-modal-button-cancel`).hide();

        if (options.closeButtonShow)
            $(`#${label}-modal-button-close`).show();
        else
            $(`#${label}-modal-button-close`).show();

        $(`#${label}-modal`)
            .off('hide.bs.modal')
            .on('hide.bs.modal', function(event) {

                const $activeElement = $(document.activeElement);

                if ($activeElement.is('[data-toggle], [data-dismiss]')) {

                    if ($activeElement.attr('id') === `${label}-modal-button-ok`)
                        options.onSelect(Dialog.OK);
                    else if ($activeElement.attr('id') === `${label}-modal-button-cancel`)
                        options.onSelect(Dialog.CANCEL);
                    else if ($activeElement.attr('id') === `${label}-modal-button-close`)
                        options.onSelect(Dialog.CLOSE);

                }

            })
            .modal('show');
    }

}

Dialog.default = {
    okButtonShow: true,
    cancelButtonShow: true,
    closeButtonShow: true,
    onSelect: (retval) => { logger.log('debug', 'dialog: returned %s', retval)},
};

Dialog.OK = 'OK';
Dialog.CANCEL = 'CANCEL';
Dialog.CLOSE = 'CLOSE';