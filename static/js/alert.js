// internal counter for uniqueness
let counter = 0;

export function alert(message, type = 'warning', timeout = 3000, placeholder = '#alert_placeholder') {

    // increment counter
    counter += 1;

    // language=HTML
    $(placeholder).append(
`<div class="alert alert-${ type } alert-dismissible fade show" id="alert-${ counter }" role="alert">
  <button type="button" class="close" data-dismiss="alert" aria-label="Close">
  <span aria-hidden="true">&times;</span>
  </button>
  ${ message }
</div>`);

    if (timeout > 0)
        setTimeout( () => { $(placeholder).remove('#alert-' + counter); }, timeout);
}
