const { createLogger, format, transports } = require('winston');

export const logger = createLogger({
    format: combine(
        format.colorize(),
        format.json()
    ),
    transports: [
        new transports.Console({ level: 'silly' }),
    ]
});
