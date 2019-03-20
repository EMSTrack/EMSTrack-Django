class BaseIconFactory {

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


    constructor(bottom = {}, top = {}, options = {}) {

        this.bottom = Object.assign({}, {
            icon: 'map-marker',
            classes: 'fa-stack-2x',
            extraClasses: '',
            style: '',
            extraStyle: '',
        }, bottom);

        this.top = Object.assign({}, {
            icon: 'plus',
            classes: 'fa-stack-1x fa-inverse',
            extraClasses: '',
            style: '',
            extraStyle: '',
        }, top);

        this.options = Object.assign({}, {
            classes: 'fa-2x fa-stack-marker-xs',
            extraClasses: '',
            style: '',
            extraStyle: '',
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

    createIcon(bottom = {}, top = {}, options = {}) {
        throw new Error('Not implemented');
    }

}

class GoogleIconFactory extends BaseIconFactory {

    constructor(bottom = {}, top = {}, options = {}) {
        super(
            bottom,
            top,
            Object.assign({className: 'GoogleBoxDivIcon'}, options)
        );
    }

}

class LeafletIconFactory extends BaseIconFactory {

    constructor(bottom = {}, top = {}, options = {}) {
        super(
            Object.assign({icon: 'map-marker'}, bottom),
            Object.assign({style: 'margin-top:0.2em'}, top),
            Object.assign({popupAnchor: [0, -15], className: 'LeafletDivIcon'}, options)
        );
    }

    createIcon(bottom = {}, top = {}, options = {}) {
        const parameters = this.getParameters(bottom, top, options);

        const bottomHtml = BaseIconFactory.toHtml(
            'i',
            ['fas', 'fa-' + parameters.bottom.icon, parameters.bottom.classes, parameters.bottom.extraClasses].join(' '),
            [parameters.bottom.style, parameters.bottom.extraStyle].join(';')
        );

        const topHtml = BaseIconFactory.toHtml(
            'i',
            ['fas', 'fa-' + parameters.top.icon, parameters.top.classes, parameters.top.extraClasses].join(' '),
            [parameters.top.style, parameters.top.extraStyle].join(';')
        );

        const html = BaseIconFactory.toHtml('span',
            ['fa-stack', parameters.options.classes, parameters.options.extraClasses].join(' '),
            [parameters.options.style, parameters.options.extraStyle].join(';'),
            [bottomHtml, topHtml].join('\n')
        );

        return {
            html: html,
            popupAnchor: parameters.options.popupAnchor,
            className: parameters.options.className
        };

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
export function stackedIconFactory(provider, bottom = {}, top = {}, options = {}) {

    // Retrieve MapBox access_token
    if (provider === 'leaflet') {
        return new LeafletIconFactory(bottom, top, options);
    } else if (provider === 'google') {
        return new GoogleIconFactory(bottom, top, options);
    } else
        return null;

}
