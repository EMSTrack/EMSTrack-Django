import { stackedIconFactory } from "../stacked-icon";

describe('stacked icon', () => {

    it('default', function() {

        const iconFactory = stackedIconFactory('leaflet');
        const json = iconFactory.createIcon();
        expect(json).to.eql({});

    });

});