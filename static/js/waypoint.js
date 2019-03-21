import { logger } from './logger';

import { stackedIconFactory } from './stacked-icon';

const iconFactory = stackedIconFactory(mapProvider);
iconFactory.setProperties(
    {classes: [iconFactory.bottom.classes, 'marker-stacked-icon-bottom'].join(' ')},
    {classes: [iconFactory.top.classes, 'marker-stacked-icon-top'].join(' ')},
    {classes: [iconFactory.options.classes, 'marker-stacked-icon'].join(' ')});

export function waypointIcon(waypoint) {

    const location = waypoint['location'];
    let icon;
    if (location.type === 'i') {
        icon = 'plus';
    } else if (location.type === 'h') {
        icon = 'hospital';
    } else if (location.type === 'w') {
        icon = 'map';
    } else if (location.type === 'b') {
        icon = 'home';
    } else {
        logger.log('warn', "Unknown waypoint location type '%s'.", location.type);
        icon = 'question';
    }

    let color_class;
    if (waypoint.status === 'C') {
        color_class = 'text-danger';
    } else if (waypoint.status === 'V') {
        color_class = 'text-primary';
    } else if (waypoint.status === 'D') {
        color_class = 'text-success';
    } else if (waypoint.status === 'S') {
        color_class = 'text-muted';
    } else {
        logger.log('warn', "Unknown waypoint status '%s'.", waypoint.status);
        color_class = 'text-warning';
    }

    return iconFactory.createSimpleIcon(icon, {}, {}, {extraClasses: color_class});

}
