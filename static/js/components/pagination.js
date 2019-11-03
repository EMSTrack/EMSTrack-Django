import { logger } from '../logger';

export class Pagination {

    constructor(previous, next, count, page_size, page_number) {
        this.previous = previous;
        this.next = next;
        this.count = count;
        this.page_size = page_size;
        this.page_number = page_number;
        this.number_of_surrounding_pages = 2;
    }

    static render_page_item(href, value, ariaLabel, extraClasses = "", callback) {

        const linkElement = $(`<li class="page-item ${extraClasses}"></li>`);

        if (callback)
            linkElement.append(callback(page));
        else
            linkElement.append(`<a class="page-link" href="${href}" aria-label="${label}">${value}</a>`);

        return linkElement;
    }

    render_link(linkUrl, page, callback) {

        linkUrl.replace(/page=\d+/, `page=${page}`);
        logger.log('debug', 'link = %s', linkUrl);

        const extraClasses = page === this.page_number ? 'active' : '';
        return Pagination.render_page_item(linkUrl, page, `page-${page}`, extraClasses, callback);

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
        paginationElement.append(Pagination.render_page_item(this.previous, '&laquo;', "Previous", extraClasses));

        if (first_page !== 1) {

            paginationElement.append(this.render_link(linkUrl, 1, "", "", render_page_callback));

            if (first_page !== 2) {
                paginationElement.append(Pagination.render_page_item("#", '&hellip;', "", "disabled"));

            }
        }

        for (let page = first_page; page <= last_page; page++)
            paginationElement.append(this.render_link(linkUrl, page, "", "", render_page_callback));

        if (last_page !== number_of_pages) {

            if (last_page !== number_of_pages - 1)
                paginationElement.append(Pagination.render_page_item("#", '&hellip;', "", "disabled"));

            paginationElement.append(this.render_link(linkUrl, number_of_pages, render_page_callback));

        }

        extraClasses = this.next === null ? "disabled" : "";
        paginationElement.append(Pagination.render_page_item(this.next, '&raquo;', "Next", extraClasses));

        return paginationElement;

    }

}

