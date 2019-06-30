export class Settings {

    constructor(parameters) {

        if (!Settings.instance) {
            Settings.instance = this;
        }

        Object.assign(Settings.instance, parameters);

        return Settings.instance;
    }

}

Settings.default  = {
    locations: {},
    location_type: {},
    translation_table: {},
    map_provider: undefined,
};

Settings.instance = new Settings(Settings.default);
Object.freeze(Settings.instance);
