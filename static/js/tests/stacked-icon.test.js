import { expect } from 'chai';

import { stackedIconFactory } from "../stacked-icon";

describe('stacked icon', () => {

    it('default', function() {

        const iconFactory = stackedIconFactory('leaflet');

        let json = iconFactory.createIcon();
        expect(json).to.eql({
            className: "LeafletDivIcon",
            html: "<span class=\"fa-stack fa-2x fa-stack-marker-xs\"><i class=\"fas fa-map-marker fa-stack-2x\"></i><i class=\"fas fa-plus fa-stack-1x fa-inverse\" style=\"margin-top:0.2em\"></i></span>"
            popupAnchor: [0, -15]
        });

        json = iconFactory.createSimpleIcon('hospital');
        expect(json).to.eql({
            className: "LeafletDivIcon",
            html: "<span class=\"fa-stack fa-2x fa-stack-marker-xs\"><i class=\"fas fa-map-marker fa-stack-2x\"></i><i class=\"fas fa-hospital fa-stack-1x fa-inverse\" style=\"margin-top:0.2em\"></i></span>"
            popupAnchor: [0, -15]
        });

    });

});