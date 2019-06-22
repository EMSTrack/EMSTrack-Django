export function alert(message, type) {
    $('#alert_placeholder').append(
        '<div class="alert alert-' + type + ' alert-dismissible fade show" role="alert">' +
        '  <button type="button" class="close" data-dismiss="alert" aria-label="Close">' +
        '    <span aria-hidden="true">&times;</span>' +
        '  </button>' +
        message +
        '</div>'
    );
};
