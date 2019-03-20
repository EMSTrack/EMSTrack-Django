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
            extraStyle: ''
        }, bottom);

        this.top = Object.assign({}, {
            icon: 'plus',
            classes: 'fa-stack-1x fa-inverse',
            extraClasses: '',
            style: '',
            extraStyle: ''
        }, top);

        this.options = Object.assign({}, {
            classes: 'fa-1x fa-stack-marker-xs',
            extraClasses: '',
            style: '',
            extraStyle: '',
            popupAnchor: [0, -15],
            className: 'BaseDivIcon'
        }, options);

    }

    setProperties(bottom = {}, top = {}, options = {}) {
        // clone and alter parameter user-provided options
        this.bottom = Object.assign({}, this.bottom, bottom);
        this.top = Object.assign({}, this.top, top);
        this.options = Object.assign({}, this.options, options);

        return this;
    }

    getProperties(_bottom = {}, _top = {}, _options = {}) {

        // clone and alter parameter user-provided options
        const bottom = Object.assign({}, this.bottom, _bottom);
        const top = Object.assign({}, this.top, _top);
        const options  = Object.assign({}, this.options, _options);

        return {bottom: bottom, top: top, options: options};
    }

    createSimpleIcon(bottomIcon, bottom = {}, top = {}, options = {}) {
        return this.createIcon(bottom, Object.assign({icon: bottomIcon}, top), options);
    }

    createIcon(bottom = {}, top = {}, options = {}) {
        throw new Error('Not implemented');
    }

}

class LeafletIconFactory extends BaseIconFactory {

    createIcon(bottom = {}, top = {}, options = {}) {
        const parameters = this.getProperties(bottom, top, options);

        const bottomHtml = BaseIconFactory.toHtml(
            'i',
            ['fas', 'fa-' + parameters.bottom.icon,
                parameters.bottom.classes, parameters.bottom.extraClasses].filter(Boolean).join(' '),
            [parameters.bottom.style, parameters.bottom.extraStyle].filter(Boolean).join(';')
        );

        const topHtml = BaseIconFactory.toHtml(
            'i',
            ['fas', 'fa-' + parameters.top.icon,
                parameters.top.classes, parameters.top.extraClasses].filter(Boolean).join(' '),
            [parameters.top.style, parameters.top.extraStyle].filter(Boolean).join(';')
        );

        const html = BaseIconFactory.toHtml('span',
            ['fa-stack', parameters.options.classes, parameters.options.extraClasses].filter(Boolean).join(' '),
            [parameters.options.style, parameters.options.extraStyle].filter(Boolean).join(';'),
            [bottomHtml, topHtml].join('')
        );

        return {
            html: html,
            popupAnchor: parameters.options.popupAnchor,
            className: parameters.options.className
        };

    }

}

class GoogleIconFactory extends LeafletIconFactory {

    constructor(bottom = {}, top = {}, options = {}) {
        super(bottom, top, Object.assign({className: 'GoogleBoxDivIcon'}, options));
    }

}

class MapBoxIconFactory extends LeafletIconFactory {

    constructor(bottom = {}, top = {}, options = {}) {
        super(bottom, top, Object.assign({className: 'LeafletDivIcon'}, options));
    }

}


/**
 *
 * @param mapProvider
 * @param bottom
 * @param top
 * @param options
 * @returns {BaseIconFactory}
 */
export function stackedIconFactory(mapProvider, bottom = {}, top = {}, options = {}) {

    // Retrieve MapBox access_token
    const provider = mapProvider['provider'];
    if (provider === 'mapbox') {
        return new MapBoxIconFactory(bottom, top, options);
    } else if (provider === 'google') {
        return new GoogleIconFactory(bottom, top, options);
    } else
        throw new Error('Unknown map provider');

}
