from django.db import transaction

from equipment.forms import EquipmentHolderUpdateForm


class EquipmentHolderCreateMixin:
    equipmentholder_form = EquipmentHolderUpdateForm

    def get_context_data(self, **kwargs):
        # Get the context
        context = super().get_context_data(**kwargs)

        # Add the equipmentholder form
        context['equipmentholder_form'] = self.equipmentholder_form

        return context

    def form_valid(self, form):
        # Get the equipmentholder form
        equipmentholder_form = self.equipmentholder_form(self.request.POST)

        # Save form
        if equipmentholder_form.is_valid():

            # wrap in atomic in case of errors
            with transaction.atomic():

                # Create equipmentholder
                equipmentholder = equipmentholder_form.save()

                # add equipmentholder to form and save
                form.instance.equipmentholder = equipmentholder

                # call super
                return super().form_valid(form)


class EquipmentHolderUpdateMixin:
    equipmentholder_form = EquipmentHolderUpdateForm

    def get_context_data(self, **kwargs):
        # Get the context
        context = super().get_context_data(**kwargs)

        # Add the equipmentholder form
        context['equipmentholder_form'] = self.equipmentholder_form(self.request.POST or None,
                                                                    instance=self.object.equipmentholder)

        return context

    def form_valid(self, form):
        # Get the equipmentholder form
        equipmentholder_form = self.equipmentholder_form(self.request.POST,
                                                         instance=self.object.equipmentholder)

        # Save form
        if equipmentholder_form.is_valid():

            # wrap in atomic in case of errors
            with transaction.atomic():

                # save equipmentholder form
                equipmentholder_form.save()

                # Call super
                return super().form_valid(form)
