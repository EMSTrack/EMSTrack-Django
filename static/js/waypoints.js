/**
 * Waypoint base class
 */

import { Location } from './location';

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
    <li id="waypoint-${label}-item-type" class="list-group-item">
        <em>${translation_table['Type']}:</em>
        <span class="float-right">${location_type[waypoint.location.type]}</span>
    </li>
    <li id="waypoint-${label}-item-status" class="list-group-item">
        <em>${translation_table['Status']}:</em>
        <span class="float-right">${waypoint_status[waypoint.status]}</span>
    </li>
    <li id="waypoint-${label}-item-address" class="list-group-item">
        ${new Location(waypoint.location).render()}
    </li>
</ul>`
        );

    }

    addBlankWaypointForm(index) {

        this.addWaypointForm(index, { id: undefined, order: 1, status: 'C', location: new Location() });

        // bind addBlankWaypointForm to click
        this.placeholder.find('#waypoint-' + this.label + '-' + index + '-button')
            .off('click')
            .on('click', () => {

            });

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

        // add to form
        this.placeholder.append(Waypoints.waypointForm(this.label + '-' + index, waypoint));

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
</div>`
        );

        // add existing waypoints
        let index = 0;
        const carousel_indicators = $(`#call-${this.label}-carousel-indicators`);
        const carousel_items = $(`#call-${this.label}-carousel-items`);
        this.waypoints.forEach( (waypoint) => {

            carousel_items.append( this.addWaypointForm(index, waypoint) );
            carousel_indicators.append( `<li data-target="#call-${this.label}-carousel" data-slide-to="${index}" class="active"></li>` );
            index += 1;

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