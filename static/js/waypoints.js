/**
 * Waypoint base class
 */

import { logger } from "./logger";

import { Location } from './location';

export class Waypoint {

    constructor(parameters) {
        const properties = Object.assign({...Waypoint.default}, parameters);

        this.id = properties.id;
        this.order = properties.order;
        this.status = properties.status;
        this.location = new Location(properties.location);
    }

}

Waypoint.default = {
    id: null,
    order: -1,
    status: 'C',
    location: new Location()
};


export class Waypoints {
    
    constructor(waypoints = [], label = 'new', placeholder = '#waypoints') {
        this.waypoints= waypoints;
        this.activeIndex = (waypoints.length > 0 ? 0 : -1);
        this.label = label;
        this.placeholderName = placeholder;

        // calculate maxOrder
        this.maxOrder = 0;
        for (const waypoint of this.waypoints) {
            this.maxOrder = ( this.maxOrder > waypoint.order ? this.maxOrder : waypoint.order );
        }

    }

    setActiveWaypoint(index) {
        this.activeIndex = index;
    }

    getActiveWaypoint() {
        return this.waypoints[this.activeIndex];
    }

    getNextWaypointIndex() {

        // next waypoint
        let nextWaypoint = -1;

        // loop over waypoints
        let index = 0;
        for (const waypoint of this.waypoints) {

            // is it next?
            if ((waypoint.status === 'C' || waypoint.status === 'V') && nextWaypoint === -1) {
                nextWaypoint = index;
                break;
            }

            index += 1;

        }

        return nextWaypoint;

    }

    static waypointForm(label, waypoint) {

        // language=HTML
        return (
            `<ul id="waypoint-${label}-${waypoint.order}-form" class="list-group">  
    <input id="waypoint-${label}-id" 
           name="id"           
           type="hidden" 
           value="${waypoint.id}">    
    <input id="waypoint-${label}-order"
           name="order"
           type="hidden"
           class="form-control form-control-sm"  
           value="${waypoint.order}">
    <li id="waypoint-${label}-item-type" class="list-group-item px-10">
        <em>${translation_table['Type']}:</em>
        <span class="float-right">${location_type[waypoint.location.type]}</span>
    </li>
    <li id="waypoint-${label}-item-status" class="list-group-item px-10">
        <em>${translation_table['Status']}:</em>
        <span class="float-right">${waypoint_status[waypoint.status]}</span>
    </li>
    <li id="waypoint-${label}-item-address" class="list-group-item px-10">
        ${new Location(waypoint.location).render()}
    </li>
</ul>`
        );

    }

    removeWaypointForm(index) {

        // mark as deleted
        this.placeholder
            .find('#waypoint-' + this.label + '-' + index + '-form input')
            .addClass('deleted');

        // remove from form
        this.placeholder
            .find('#waypoint-' + this.label + '-' + index + '-form')
            .hide();

    }

    addWaypointForm(index, waypoint) {

        const active = index === this.activeIndex;

        $(`#call-${this.label}-carousel-items`).append(
            `<div class="carousel-item${active ? ' active' : ''}">
    ${Waypoints.waypointForm(this.label, waypoint)}
</div>`
        );
        $(`#call-${this.label}-carousel-indicators`).append(
            `<li data-target="#call-${this.label}-carousel" 
    data-slide-to="${index}" 
    ${active ? 'class="active"' : ''}>
</li>`
        );

    }

    addBlankWaypointForm(index) {

        logger.log('info', 'adding blank waypoint');

        // create blank waypoint, update maxOrder and add to list
        const waypoint = new Waypoint();
        this.maxOrder += 1;
        waypoint.order = this.maxOrder;
        this.waypoints.push(waypoint);

        this.addWaypointForm(index, waypoint);

    }

    configureEditorButtons() {

        const waypoint = this.getActiveWaypoint();
        const nextWaypointIndex = this.getNextWaypointIndex();

        logger.log('debug', 'activeWaypoint = %d, nextWaypoint = %d', this.activeIndex, nextWaypointIndex);

        // enable/disable buttons
        let skipButtonDisabled = false;
        if (waypoint.status === 'S' || waypoint.status === 'D') {
            // waypoint has been skipped or visited already
            skipButtonDisabled = true;
        }

        let addButtonDisable = true;
        if (this.activeIndex >= nextWaypointIndex ||
            (this.activeIndex === this.waypoints.length - 1)) {
            // waypoint is either next, hasn't come yet or it the last one
            addButtonDisable = false;
        }

        let forwardButtonDisable = true;
        if ( this.activeIndex >= nextWaypointIndex
            && this.activeIndex < this.waypoints.length - 1
            && (waypoint.status === 'C' || waypoint.status === 'S')) {
            // waypoint is next or beyond but not last and is either created or skipped
            forwardButtonDisable = false;
        }

        let backwardButtonDisable = true;
        if ( this.activeIndex > nextWaypointIndex
            && (waypoint.status === 'C' || waypoint.status === 'S')) {
            // waypoint is beyond next  and is either created or skipped
            backwardButtonDisable = false;
        }

        // disable skip
        $(`#call-${this.label}-waypoints-skip-button`)
            .attr('disabled', skipButtonDisabled);

        // disable forward
        $(`#call-${this.label}-waypoints-forward-button`)
            .attr('disabled', forwardButtonDisable);

        // disable backward
        $(`#call-${this.label}-waypoints-backward-button`)
            .attr('disabled', backwardButtonDisable);

        // disable add
        $(`#call-${this.label}-waypoints-add-button`)
            .attr('disabled', addButtonDisable);

    }

    render() {

        // create placeholder selector
        this.placeholder = $(this.placeholderName);

        this.placeholder.html(`
<div id="call-${this.label}-carousel" class="carousel slide" data-ride="carousel">
    <ol id="call-${this.label}-carousel-indicators" class="carousel-indicators">
    </ol>
    <div id="call-${this.label}-carousel-items" class="carousel-inner">
    </div>
    <a class="carousel-control-prev" href="#call-${this.label}-carousel" role="button" data-slide="prev">
        <span class="carousel-control-prev-icon" aria-hidden="true"></span>
        <span class="sr-only">Previous</span>
    </a>
    <a class="carousel-control-next" href="#call-${this.label}-carousel" role="button" data-slide="next">
        <span class="carousel-control-next-icon" aria-hidden="true"></span>
        <span class="sr-only">Next</span>
    </a>
</div>
<div class="btn-group d-flex my-2">
    <button id="call-${this.label}-waypoints-skip-button" 
            type="button" class="btn btn-danger w-100"
            title="Skip waypoint">
        <span class="fas fa-stop"></span> 
    </button>
    <button id="call-${this.label}-waypoints-backward-button" 
            type="button" class="btn btn-warning w-100"
            title="Move waypoint back">
        <span class="fas fa-backward"></span> 
    </button>
    <button id="call-${this.label}-waypoints-add-button" 
            type="button" class="btn btn-info w-100"
            title="Add waypoint">
        <span class="fas fa-plus"></span> 
    </button>
    <button id="call-${this.label}-waypoints-forward-button" 
            type="button" class="btn btn-warning w-100"
            title="Move waypoint forth">
        <span class="fas fa-forward"></span> 
    </button>
</div>`
        );

        // add existing waypoints
        let index = 0;
        this.waypoints.forEach( (waypoint) => {

            this.addWaypointForm( index, waypoint );
            index += 1;

        });

        // configure buttons
        this.configureEditorButtons();

        // add waypoint
        $(`#call-${this.label}-waypoints-add-button`)
            .on('click', (event) => {

                event.stopPropagation();

                this.addBlankWaypointForm( this.waypoints.length );

            });

        // move back
        $(`#call-${this.label}-waypoints-backward-button`)
            .on('click', (event) => {

                event.stopPropagation();

            });

        // move forward
        $(`#call-${this.label}-waypoints-forward-button`)
            .on('click', (event) => {

                event.stopPropagation();

            });

        // activate carousel
        $(`#call-${this.label}-carousel`)
            .carousel({
                interval: false,
                wrap: false
            })
            .on('slide.bs.carousel', (event) => {

                // set active waypoint and configure buttons
                this.setActiveWaypoint(event.to);
                this.configureEditorButtons();

                logger.log('info', 'setting active waypoint %d', this.activeIndex);

            });

        logger.log('info', 'rendering waypoint editor for call %s', this.label);

    }

    getData() {

        // select all inputs
        const inputs = $(this.placeholderName + ' :input:not(:checkbox):not(:button):not(.deleted)');

        let entry = {};
        const waypoints = [];
        inputs.each( function() {

            // parse values
            let value = $(this).val().trim();
            if (this.name === 'name')
                entry[this.name] = value;
            else {
                value = parseInt(value);
                if ( !(this.name === 'id' && isNaN(value)) )
                    entry[this.name] = isNaN(value) ? null : value;
            }

            // is it the end of the structure?
            if (this.name === 'age') {
                if (entry.name || entry.age)
                    // skip if empty
                    waypoints.push(entry);
                entry = {};
            }

        });

        return waypoints;
    }

    same(waypoints) {
        return JSON.stringify(waypoints) === JSON.stringify(this.waypoints);
    }
}