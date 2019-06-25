/**
 * Patient base class
 */
export class Patients {
    
    constructor(patients = [], label = 'new', placeholder = '#patients') {
        this.patients= patients;
        this.label = label;
        this.placeholderName = placeholder;
    }

    static patientForm(label, symbol, patient) {

        return (
            '<div class="form-row" id="patient-' + label + '-form">' +
            '  <div class="col-md-7 pr-0">' +
            '    <input id="patient-' + label + '-id" ' +
            '           name="id"' +
            '           type="hidden" ' +
            '           value="' + patient.id + '">' +
            '    <input id="patient-' + label + '-name" ' +
            '           name="name"' +
            '           type="text" ' +
            '           class="form-control" ' +
            '           value="' + patient.name + '" ' +
            '           placeholder="' + translation_table['Name'] + '">' +
            '  </div>' +
            '  <div class="col-md-3 px-0">' +
            '    <input id="patient-' + label + '-age" ' +
            '           name="age"' +
            '           type="number" min="0" ' +
            '           class="form-control" ' +
            '           value="' + patient.age + '" ' +
            '           placeholder="' + translation_table['Age'] + '">' +
            '  </div>' +
            '  <div class="col-md-2 pl-0">' +
            '    <button class="btn btn-default btn-block btn-new-patient" ' +
            '            type="button" ' +
            '            id="patient-' + label + '-button">' +
            '      <span id="patient-' + label + '-symbol" class="fas ' + symbol + '"></span>' +
            '    </button>' +
            '  </div>' +
            '</div>'
        );

    }

    addBlankPatientForm(index) {

        this.addPatientForm(index, { id: undefined, name: '', age: '' }, 'fa-plus');

        // bind addBlankPatientForm to click
        this.placeholder.find('#patient-' + this.label + '-' + index + '-button')
            .off('click')
            .on('click', () => {

                // change icon
                this.placeholder.find('#patient-' + this.label + '-' + index + '-symbol')
                    .removeClass('fa-plus')
                    .addClass('fa-minus');

                // bind remove action
                this.placeholder.find('#patient-' + this.label + '-' + index + '-button')
                    .off('click')
                    .on('click', () => { this.removePatientForm(index); });

                // add new blank form
                this.addBlankPatientForm(index + 1);

            });

    }

    removePatientForm(index) {

        // remove from form
        this.placeholder
            .find('#patient-' + this.label + '-' + index + '-form')
            .hide();

    }

    addPatientForm(index, patient, symbol = 'fa-minus') {

        // add to form
        this.placeholder.append(Patients.patientForm(this.label + '-' + index, symbol, patient));

        // bind remove action
        this.placeholder.find('#patient-' + this.label + '-' + index + '-button')
            .on('click', () => { this.removePatientForm(index); });

    }

    createForm() {

        // create placeholder selector
        this.placeholder = $(this.placeholderName);

        // add existing patients
        let index = 0;
        this.patients.forEach( (patient) => {

            index += 1;
            this.addPatientForm(index, patient);

        });

        // add blank form
        index += 1;
        this.addBlankPatientForm(index);

    }

    getData() {

        // select all inputs
        const inputs = $(this.placeholderName + ' :input:not(:checkbox):not(:button)');

        let entry = {};
        const patients = [];
        inputs.each( function() {

            // parse values
            let value = $(this).val().trim();
            if (this.name === 'name')
                entry[this.name] = value;
            else {
                value = parseInt(value);
                entry[this.name] = isNaN(value) ? '' : value;
            }

            // is it the end of the structure?
            if (this.name === 'age') {
                if (entry.name || entry.age)
                    // skip if empty
                    patients.push(entry);
                entry = {};
            }

        });

        return patients;
    }

    same(patients) {
        return JSON.stringify(patients) === JSON.stringify(this.patients);
    }
}