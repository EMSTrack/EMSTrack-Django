import { logger } from '../logger';

export class Pages {

    constructor(location, sizes = [100, 500, 1000], defaultPageSize=500) {
        this.sizes = sizes;

        // get page and page_size parameters
        this.url = window.location.href.split('?')[0];;

        this.searchParams = new URLSearchParams(location.search);
        this.page = this.searchParams.has('page') ? Number.parseInt(this.searchParams.get('page')) : 1;
        this.page_size = this.searchParams.has('page_size') ? Number.parseInt(this.searchParams.get('page_size')) : defaultPageSize;

        console.log(this);
    }

    render() {

        const element = $(`<ul class="list-unstyled"></ul>`);

        for (let i = 0; i < this.sizes.length; i++) {

            const listItem = $('<li class="float-left align-middle ml-1"></li>');

            const currentSize = this.sizes[i];
            if (this.page_size === currentSize) {
                listItem.html(`<span>${currentSize}</span>`);
            } else {
                this.searchParams.set('page_size', currentSize);
                const url = this.url + '?' + this.searchParams;
                console.log(url);
                listItem.html(`<a href="${url}">${currentSize}</a>`);
            }

            element.append(listItem);
        }

        return element;
    }

}

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

        const element = $(`<li class="page-item ${options.extraClasses}"></li>`);

        if (options.callback !== null)
            element.append(options.callback(page, options));
        else
            element.append(`<a class="page-link" href="${options.href}" aria-label="${options.ariaLabel}">${options.label}</a>`);

        return element;
    }

    render_link(page, callback, _options) {

        const options = Object.assign({
            label: page,
            ariaLabel: `page-${page}`,
            extraClasses: '',
            callback: callback
        }, _options);

        options.extraClasses += (page === this.page_number ? ' active' : '');
        return Pagination.render_page_item(page, options);

    }

    render(callback) {

        const number_of_pages = Math.ceil(this.count / this.page_size);
        logger.log('debug', 'number_of_pages = %d', number_of_pages);

        // calculate pages
        const first_page = Math.max(this.page_number - this.number_of_surrounding_pages, 1);
        const last_page = Math.min(this.page_number + this.number_of_surrounding_pages, number_of_pages);

        const paginationElement = $(`<ul class="pagination"></ul>`);

        // add previous
        if (this.previous === null)
            paginationElement.append(
                Pagination.render_page_item(-1, {label: '&laquo;', ariaLabel: 'Previous', extraClasses: 'disabled'})
            );
        else
            paginationElement.append(
                this.render_link(this.page_number - 1, callback, {label: '&laquo;', ariaLabel: 'Previous'})
            );

        // add first page and ellipses if needed
        if (first_page !== 1) {

            paginationElement.append(
                this.render_link(1, callback)
            );

            if (first_page !== 2)
                paginationElement.append(
                    Pagination.render_page_item(-1, {label: '&hellip;', extraClasses: 'disabled'})
                );
        }

        // add pages
        for (let page = first_page; page <= last_page; page++)
            paginationElement.append(
                this.render_link(page, callback)
            );

        // add last page and ellipses if needed
        if (last_page !== number_of_pages) {

            if (last_page !== number_of_pages - 1)
                paginationElement.append(
                    Pagination.render_page_item(-1, {label: '&hellip;', extraClasses: 'disabled'})
                );

            paginationElement.append(
                this.render_link(number_of_pages, callback)
            );

        }

        // add next
        if (this.next === null)
            paginationElement.append(
                Pagination.render_page_item(-1, {label: '&raquo;', ariaLabel: 'Next', extraClasses: 'disabled'})
            );
        else
            paginationElement.append(
                this.render_link(this.page_number + 1, callback, {label: '&raquo;', ariaLabel: 'Next'})
            );

        return paginationElement;

    }

}

