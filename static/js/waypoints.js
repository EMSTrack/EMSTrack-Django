/**
 * Waypoint base class
 */
export class Waypoints {
    
    constructor(waypoints = [], label = 'new', placeholder = '#waypoints') {
        this.waypoints= waypoints;
        this.label = label;
        this.placeholderName = placeholder;
    }

    static waypointForm(label, waypoint) {

        // language=HTML
        return (
            `<div class="form-row" id="waypoint-${label}-form">  
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
             id="waypoint-${label}-header"
             data-toggle="collapse" 
             data-target="#waypoint-${label}-body" 
             aria-expanded="false" 
             aria-controls="waypoint-${label}-body">
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
        <div class="collapse" id="waypoint-${label}-body">
            <div class="card-body">
                
            </div>
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

        // add existing waypoints
        let index = 0;
        this.waypoints.forEach( (waypoint) => {

            index += 1;
            this.addWaypointForm(index, waypoint);

        });

        // add blank form
        index += 1;
        this.addBlankWaypointForm(index);

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