const { createLogger, format, transports } = require('winston');

export const logger = createLogger({
    format: format.combine(
        format.colorize(),
        format.simple()
    ),
    transports: [
        new transports.Console({ level: 'silly' }),
    ]
});
