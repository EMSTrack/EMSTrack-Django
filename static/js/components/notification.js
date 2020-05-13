import {logger} from "../logger";

export function showNotification(title, message) {
    if (!window.Notification) {
        logger.log('warning', 'Browser does not support notifications.');
    } else {
        // check if permission is already granted
        if (Notification.permission === 'granted') {
            // show notification here
            new Notification(title, {
                body: message,
                icon: 'https://bit.ly/2DYqRrh',
            });
        } else {
            // request permission from user
            Notification.requestPermission().then(function (p) {
                if (p === 'granted') {
                    // show notification here
                    new Notification(title, {
                        body: message,
                        icon: 'https://bit.ly/2DYqRrh',
                    });
               } else {
                    logger.log('warn', 'User blocked notifications.');
                }
            }).catch(function (err) {
                logger.log('error', 'Error: %s', err);
            });
        }
    }
}