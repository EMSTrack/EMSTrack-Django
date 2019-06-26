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
    <div class="col-md-7 pr-0">   
        <input id="waypoint-${label}-id" 
               name="id"           
               type="hidden" 
               value="${waypoint.id}">    
        <input id="waypoint-${label}-order"
               name="order"
               type="hidden"
               class="form-control"  
               value="${waypoint.order}">
    </div> 
    <div class="col-md-3 px-0">  
        <input id="waypoint-${label}-status"
               name="status"
               class="form-control"     
               value="${waypoint.status}"   
               placeholder="${translation_table['Age']}"> 
    </div>  
    <div class="col-md-2 pl-0">  
        <div class="btn-group d-block">   
            <button class="btn btn-default btn-block btn-sm"   
                    type="button"  
                    id="waypoint-${label}-button-up">
                <span class="fas fa-chevron-up fa-xs"></span>
            </button>  
            <button class="btn btn-default btn-block btn-sm"   
                    type="button"  
                    id="waypoint-${label}-button-down">   
                <span class="fas fa-chevron-down fa-xs"></span>  
            </button>   
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