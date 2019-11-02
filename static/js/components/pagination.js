import { logger } from '../logger';

export class Pagination {

    constructor(previous, next, count, page_size, page_number) {
        this.previous = previous;
        this.next = next;
        this.count = count;
        this.page_size = page_size;
        this.page_number = page_number;
    }

    render() {

        let html = `
<ul class="pagination">`;

        if (this.previous != null) {

            html += `
  <li class="page-item">
    <a class="page-link" href="${this.previous}" aria-label="Previous">
      <span aria-hidden="true">&laquo;</span>
    </a>
  </li>`;

        } else {

            html += `
  <li class="page-item disabled">
    <a class="page-link" href="#" aria-label="Previous">
      <span aria-hidden="true">&laquo;</span>
    </a>
  </li>`;

        }

        let linkUrl = this.previous != null ? this.previous : this.next;
        const regex =  /page=\d/;
        const number_of_pages = (this.count/this.page_size|0);
        for (let page = 1; page <= number_of_pages; page++) {

            linkUrl.replace(regex, `page=${page}`);
            logger.log('debug', 'link = %s', linkUrl);

            //    <li class="page-item disabled">
            //      <a class="page-link" href="#"><span aria-hidden="true">&hellip;</span></a>
            //      </li>

            html += `
  <li class="page-item ${page == this.page_number ? 'active' : ''}">
    <a class="page-link" href="${linkUrl}">${page}</a>
  </li>`;

        }

        if (this.next!= null) {

            html += `
  <li class="page-item">
    <a class="page-link" href="{{ next_url }}" aria-label="Next">
      <span aria-hidden="true">&raquo;</span>
    </a>
  </li>`;

        } else {

            html += `
  <li class="page-item disabled">
    <a class="page-link" href="#" aria-label="Next">
      <span aria-hidden="true">&raquo;</span>
    </a>
  </li>`;

        }

        html += `
</ul>`;

        return html;

    }

}

