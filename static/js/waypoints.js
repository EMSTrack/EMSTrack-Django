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
            `<div id="waypoint-${label}-form">  
    <input id="waypoint-${label}-id" 
           name="id"           
           type="hidden" 
           value="${waypoint.id}">    
    <input id="waypoint-${label}-order"
           name="order"
           type="hidden"
           class="form-control form-control-sm"  
           value="${waypoint.order}">
    <div class="card">
        <div class="card-header p-0" 
             id="waypoint-${label}-header">
            <div class="btn-group btn-group-xs d-block float-left">   
                <button class="btn btn-default btn-block btn-xs m-0"
                        type="button"  
                        id="waypoint-${label}-button-up">
                    <span class="fas fa-chevron-up fa-xs"></span>
                </button>  
                <button class="btn btn-default btn-block btn-xs m-0"   
                        type="button"  
                        id="waypoint-${label}-button-down">   
                    <span class="fas fa-chevron-down fa-xs"></span>  
                </button>   
            </div> 
            <span>${translation_table['Type']}:</span>
            <button class="btn btn-outline-dark btn-sm"
                    type="button"  
                    id="waypoint-${label}-button-location-type">
                <span class="fas fa-user fa-xs"></span>
            </button>
            <span>${translation_table['Status']}:</span>
            <button class="btn btn-outline-dark btn-sm"
                    type="button"  
                    id="waypoint-${label}-button-location-type">
                <span class="fas fa-user fa-xs"></span>
            </button>
            <button type="button" class="close float-right" aria-label="Close">
                <span aria-hidden="true">&times;</span>
            </button>
        </div>
        <div class="card-body" id="waypoint-${label}-body">
            ${new Location(waypoint.location).render()}
        </div>
    </div>
</div>`
        );

    }

    addBlankWaypointForm(index) {

        this.addWaypointForm(index, { id: undefined, order: '', status: '', location: undefined });

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