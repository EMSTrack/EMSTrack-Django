

class BaseIconFactory {

    constructor(bottom = {}, top = {}, options = {}) {

        this.bottom = Object.assign({}, {
            icon: 'map-marker',
            size: 'fa-stack-2x',
            extraClasses: '',
            style: '',
            extraStyle: '',
        }, bottom);

        this.top = Object.assign({}, {
            icon: 'plus fa-inverse',
            size: 'fa-stack-1x',
            extraClasses: '',
            style: '',
            extraStyle: '',
        }, top);

        this.options = Object.assign({}, {
            size: 'fa-2x fa-stack-marker-xs',
            extraStyle: '',
            extraClasses: '',
            popupAnchor: [0, 0],
            className: 'BaseDivIcon'
        }, options);

    }

    getParameters(_bottom = {}, _top = {}, _options = {}) {

        // clone and alter parameter user-provided options
        const bottom = Object.assign({}, this.bottom, _bottom);
        const top = Object.assign({}, this.top, _top);
        const options  = Object.assign({}, this.options, _options);

        return {bottom: bottom, top: top, options: options};
    }

    static toHtml(element, _class, style = '', body = '') {
        let html = '<' + element + ' class="' + _class + '"';
        if (style !== '')
            html += ' style="' + style + '"';
        html += '>';
        if (body !== '')
            html += body;
        html += '</' + element + '>';
        return html;
    }

    createIcon(bottom = {}, top = {}, options = {}) {
        const parameters = this.getParameters(bottom, top, options);

        const bottomHtml = BaseIconFactory.toHtml(
            'i',
            'fas fa-' + [parameters.bottom.icon, parameters.bottom.size, parameters.bottom.extraClasses].join(' '),
            [parameters.bottom.style, parameters.bottom.extraStyle].join(';')
        );

        const topHtml = BaseIconFactory.toHtml(
            'i',
            'fas fa-' + [parameters.top.icon, parameters.top.size, parameters.top.extraClasses].join(' '),
            [parameters.top.style, parameters.top.extraStyle].join(';')
        );

        const html = BaseIconFactory.toHtml('span',
            'fa-stack ' + parameters.options.size + ' ' + parameters.options.extraClasses,
            parameters.option.extraStyle,
            bottomHtml + topHtml
        )

        return new L.divIcon({
            html: html,
            popupAnchor: parameters.options.popupAnchor,
            className: parameters.options.className
        });

    }

}

class GoogleIconFactory extends BaseIconFactory {

    constructor(bottom = {}, top = {}, options = {}) {
        super(
            bottom,
            top,
            Object.assign({}, {className: 'GoogleBoxDivIcon'}, options)
        );
    }

}

class MapBoxIconFactory extends BaseIconFactory {

    constructor(bottom = {}, top = {}, options = {}) {
        super(
            bottom,
            Object.assign({}, {style: 'margin-top:0.2em'}, top),
            Object.assign({}, {popupAnchor: [0, -15], className: 'MapBoxDivIcon'}, options)
        );
    }

}


/**
 *
 * @param map_provider
 * @param bottom
 * @param top
 * @param options
 * @returns {*}
 */
export function iconFactory(map_provider, bottom = {}, top = {}, options = {}) {

    // default empty options
    options = options || {};

    // Retrieve MapBox access_token
    const provider = map_provider['provider'];
    if (provider === 'mapbox') {
        return new MapBoxIconFactory(bottom, top, options);
    } else if (provider === 'google') {
        return new GoogleIconFactory(bottom, top, options);
    } else
        return null;

}
