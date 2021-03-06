import { logger } from '../logger';

export class Pages {

    constructor(location, sizes = [500, 1000, 5000], defaultPageSize=1000) {
        this.sizes = sizes;

        // get page and page_size parameters
        this.url = window.location.href.split('?')[0];;

        this.searchParams = new URLSearchParams(location.search);
        this.page = this.searchParams.has('page') ? Number.parseInt(this.searchParams.get('page')) : 1;
        this.page_size = this.searchParams.has('page_size') ? Number.parseInt(this.searchParams.get('page_size')) : defaultPageSize;

        console.log(this);
    }

    render(extraClasses='') {

        const element = $(`<div class="row ${extraClasses}"></div>`);

        for (let i = 0; i < this.sizes.length; i++) {

            const listItem = $('<div class="col"></div>');

            const currentSize = this.sizes[i];
            if (this.page_size === currentSize) {
                listItem.html(`<span><strong>${currentSize}</strong></span>`);
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

export class ReadPages {

    constructor(apiClient, url, page_size = 1000) {
        this.apiClient = apiClient;

        // get page and page_size parameters
        const urlParts = url.split('?');
        this.url = urlParts[0];
        this.searchParams = new URLSearchParams(urlParts.length > 1 ? urlParts[1] : '');
        this.page = this.searchParams.has('page') ? Number.parseInt(this.searchParams.get('page')) : 1;

        this.page_size = this.searchParams.has('page_size')
            ? Number.parseInt(this.searchParams.get('page_size'))
            : page_size;
        this.searchParams.set('page_size', this.page_size.toString());

        this.totalPages = -1;

        this.results = [];
        this.numberOfErrors = 0;
    }

    getPages() {

        logger.log('debug', 'Retrieving page %d...', this.page);

        // build url
        this.searchParams.set('page', this.page.toString());
        const url = this.url + '?' + this.searchParams;

        logger.log('debug', 'url: %s', url);

        return this.apiClient.httpClient.get(url)
            .then( response => {

                // retrieve updates and add to history
                const pageData = response.data;
                const pageResults = pageData.results;
                this.results = this.results.concat(pageResults);
                if (this.totalPages < 0)
                    this.totalPages =  Math.ceil(pageData.count / this.page_size);

                logger.log('debug', 'Page %d of %d: %d records, next=%s...',
                    this.page, this.totalPages, this.results.length, pageData.next);

                try {

                    // process page
                    this.afterPage(pageResults);

                } catch(error) {
                    logger.log('debug', 'Failed processing page %d, error: %s', this.page, error);
                    this.numberOfErrors++;
                }

                // has next page?
                if (pageData.next !== null) {

                    // retrieve next page
                    this.page++;
                    this.getPages();

                } else {

                    try {

                        // process vehicle history
                        this.afterAllPages();

                    } catch(error) {
                        logger.log('debug', 'Failed processing pages, error: %s', error);
                        this.numberOfErrors++;
                    }

                }

            })
            .catch((error) => {
                logger.log('error', "'Failed to retrieve page %d, error: %s", this.page, error);
                this.numberOfErrors++;

                // process vehicle history
                this.afterAllPages();

            });

    }

    afterPage(result) { }

    afterAllPages() { }

}
