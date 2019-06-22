import { logger } from './logger';

import { stackedIconFactory } from './stacked-icon';

const iconFactory = stackedIconFactory(mapProvider);
iconFactory.setProperties(
    {classes: [iconFactory.bottom.classes, 'marker-stacked-icon-bottom'].join(' ')},
    {classes: [iconFactory.top.classes, 'marker-stacked-icon-top'].join(' ')},
    {classes: [iconFactory.options.classes, 'marker-stacked-icon'].join(' ')});

const settings = {
    waypoint: {
        locationTypeIcon: {
            'i': 'plus',
            'h': 'hospital',
            'w': 'map',
            'b': 'home',
            'o': 'globe-americas',
        },
        statusColor: {
            'C': 'danger',
            'V': 'primary',
            'D': 'success',
            'S': 'muted'
        }
    },
    ambulance: {
        statusIcon: {
            'AV': 'flag',
            'PB': 'ambulance',
            'AP': 'heart',
            'HB': 'ambulance',
            'AH': 'plus',
            'BB': 'ambulance',
            'AB': 'home',
            'WB': 'ambulance',
            'AW': 'map',
            'OS': 'times',
            'UK': 'question'
        },
        statusColor: {
            'AV': 'success',
            'PB': 'danger',
            'AP': 'primary',
            'HB': 'danger',
            'AH': 'primary',
            'BB': 'danger',
            'AB': 'primary',
            'WB': 'danger',
            'AW': 'primary',
            'OS': 'muted',
            'UK': 'muted'
        }
    }
};

export function waypointIcon(waypoint) {

    const location = waypoint['location'];
    let icon = settings.waypoint.locationTypeIcon[location.type];
    if (typeof icon === 'undefined') {
        logger.log('warn', "Unknown waypoint location type '%s'.", location.type);
        icon = 'question';
    }

    let color = settings.waypoint.statusColor[waypoint.status];
    if (typeof color === 'undefined') {
        logger.log('warn', "Unknown waypoint status '%s'.", waypoint.status);
        color = 'warning';
    }

    return iconFactory.createSimpleIcon(icon, {}, {}, {extraClasses: 'text-' + color});

}

export function ambulanceStatusIcon(ambulance) {

    let icon = settings.ambulance.statusIcon[ambulance.status];
    let color = settings.ambulance.statusColor[ambulance.status];
    if (typeof icon === 'undefined' || typeof color === 'undefined') {
        logger.log('warn', "Unknown ambulance status'%s'.", ambulance.status);
        icon = 'question';
        color = 'warning';
    }

    return iconFactory.createSimpleIcon(icon, {}, {}, {extraClasses: 'text-' + color});

}