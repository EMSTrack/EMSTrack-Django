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
    map_provider: undefined,
    ambulance_status: {},
    ambulance_status_order: {},
    ambulance_capability: {},
    ambulance_capability_order: {},
    ambulance_online: {},
    ambulance_online_order: {},
    location_type: {},
    location_type_order: {},
    call_status: {},
    call_status_order: {},
    waypoint_status: {},
    waypoint_status_order: {},
    call_priority: {},
    call_priority_order: {},
    ambulancecall_status: {},
    ambulance_css: {},
    call_priority_css: {},
    translation_table: {},
};

new Settings(Settings.default);
// Object.freeze(Settings.instance);
