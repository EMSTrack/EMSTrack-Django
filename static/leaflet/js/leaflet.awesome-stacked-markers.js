(function (window, document, undefined) {
    "use strict";

    var newFontAwesomeStackedIcon = function (options) {
        return new L.divIcon({
            html: '<span class="fa-stack fa-2x ' + options.extraClasses + '">' +
                  '<i class="fas fa-map-marker fa-stack-2x"></i>' +
                  '<i class="fas fa-' + options.icon + ' fa-stack-1x fa-inverse" style="margin-top:-0.3em"></i>' +
                  '</span>',
            popupAnchor: [0, -30],
            className: 'myDivIcon'
        });
    }

}(this, document));