/**
 * Waypoint base class
 */

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
        this.label = label;
        this.placeholderName = placeholder;
    }

    static waypointForm(label, waypoint) {

        // language=HTML
        return (
            `<ul id="waypoint-${label}-form" class="list-group">  
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

    addWaypointForm(index, waypoint, active = false) {

        $(`#call-${this.label}-carousel-items`).append(
            `<div class="carousel-item${active ? ' active' : ''}">
    ${Waypoints.waypointForm(this.label + '-' + index, waypoint)}
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

        const waypoint = new Waypoint();
        console.log(waypoint);
        this.addWaypointForm(index, waypoint);

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
            type="button" class="btn btn-secondary w-100"
            title="Skip waypoint">
        <span class="fas fa-stop"></span> 
    </button>
    <button id="call-${this.label}-waypoints-forward-button" 
            type="button" class="btn btn-warning w-100"
            title="Mark as visiting">
        <span class="fas fa-forward"></span> 
    </button>
    <button id="call-${this.label}-waypoints-add-button" 
            type="button" class="btn btn-info w-100"
            title="Add waypoint">
        <span class="fas fa-plus"></span> 
    </button>
</div>`
        );

        // add existing waypoints
        let index = 0;
        this.waypoints.forEach( (waypoint) => {

            this.addWaypointForm(index, waypoint, index === 0);
            index += 1;

        });

        // add waypoint point
        $(`#call-${this.label}-waypoints-add-button`)
            .on('click', function (event) {

                event.stopPropagation();

                this.addBlankWaypointForm();

            });

        // activate carousel
        $(`#call-${this.label}-carousel`)
            .carousel({
                interval: false,
                wrap: false
            })
            .on('slide.bs.carousel', function (e) {

                console.log(e);

                // get current waypoint

                // enable/disable buttons

            });

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