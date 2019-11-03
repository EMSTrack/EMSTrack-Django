import { logger } from '../logger';

export class Pagination {

    constructor(previous, next, count, page_size, page_number) {
        this.previous = previous;
        this.next = next;
        this.count = count;
        this.page_size = page_size;
        this.page_number = page_number;
        this.number_of_surrounding_pages = 1;
    }

    static render_page_item(page, _options) {

        const options = Object.assign({
            href: '#',
            label: page,
            ariaLabel: '',
            extraClasses: '',
            callback: null
        }, _options);

        logger.log('debug', 'options = %j', options);

        const linkElement = $(`<li class="page-item ${options.extraClasses}"></li>`);

        if (options.callback)
            linkElement.append(options.callback(page, options));
        else
            linkElement.append(`<a class="page-link" href="${options.href}" aria-label="${options.ariaLabel}">${options.label}</a>`);

        return linkElement;
    }

    render_link(page, _options) {

        const options = Object.assign({
            href: '#',
            label: page,
            ariaLabel: `page-${page}`,
            extraClasses: '',
            callback: null
        }, _options);

        options.href.replace(/page=\d+/, `page=${page}`);
        options.extraClasses += (page === this.page_number ? ' active' : '');
        return Pagination.render_page_item(page, options);

    }

    render(render_page_callback) {

        const number_of_pages = (this.count / this.page_size | 0);
        logger.log('debug', 'number_of_pages = %d', number_of_pages);

        const linkUrl = this.previous != null ? this.previous : this.next;
        logger.log('debug', 'link = %s', linkUrl);

        // calculate pages
        const first_page = Math.max(this.page_number - this.number_of_surrounding_pages, 1);
        const last_page = Math.min(this.page_number + this.number_of_surrounding_pages, number_of_pages);

        const paginationElement = $(`<ul class="pagination"></ul>`);

        let extraClasses = this.previous === null ? "disabled" : "";
        paginationElement.append(
            this.render_link(-1, {label: '&laquo;', ariaLabel: 'Previous', extraClasses: extraClasses})
        );

        if (first_page !== 1) {

            paginationElement.append(
                this.render_link(1, {href: linkUrl, callback: render_page_callback})
            );

            paginationElement.append(
                Pagination.render_page_item(-1, {label: '&hellip;', extraClasses: 'disabled'})
            );
        }

        for (let page = first_page; page <= last_page; page++)
            paginationElement.append(
                this.render_link(page, {href: linkUrl, callback: render_page_callback})
            );

        if (last_page !== number_of_pages) {

            paginationElement.append(
                Pagination.render_page_item(-1, {label: '&hellip;', extraClasses: 'disabled'})
            );

            paginationElement.append(
                this.render_link(last_page, {href: linkUrl, callback: render_page_callback})
            );

        }

        extraClasses = this.next === null ? "disabled" : "";
        paginationElement.append(
            this.render_link(-1, {label: '&raquo;', ariaLabel: 'Next', extraClasses: extraClasses})
        );

        return paginationElement;

    }

}

