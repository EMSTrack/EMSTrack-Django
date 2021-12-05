import logging

from django.db import transaction

from equipment.forms import EquipmentHolderUpdateForm, EquipmentHolderCreateForm
from equipment.models import EquipmentItem

logger = logging.getLogger(__name__)


class EquipmentHolderCreateMixin:
    equipmentholder_form = EquipmentHolderCreateForm

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

            # assemble equipments in all equipmentsets
            equipments = set()
            for equipmentset in equipmentholder_form.cleaned_data['equipmentsets']:
                for equipmentsetitem in equipmentset.equipmentsetitem_set.all():
                    equipments.add(equipmentsetitem.equipment)

            # wrap in atomic in case of errors
            with transaction.atomic():

                # Create equipmentholder
                equipmentholder = equipmentholder_form.save()

                # Add equipments
                user = form.instance.updated_by
                for equipment in equipments:
                    EquipmentItem.objects.create(equipmentholder=equipmentholder,
                                                 equipment=equipment,
                                                 updated_by=user)

                # add equipmentholder to form and save
                form.instance.equipmentholder = equipmentholder

                # call super
                return super().form_valid(form)
        else:
            # Otherwise treat as if the first form was invalid
            return super().form_invalid(form)


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

            # assemble equipments in all equipmentsets not in current equipmentitems
            equipmentitemset = self.object.equipmentholder.equipmentitem_set.all().values('equipment_id')
            equipments = set()
            for equipmentset in equipmentholder_form.cleaned_data['equipmentsets']:
                for equipment in equipmentset.equipmentsetitem_set\
                        .exclude(equipment_id__in=equipmentitemset):
                    equipments.add(equipment.equipment)

            # wrap in atomic in case of errors
            with transaction.atomic():

                # save equipmentholder form
                equipmentholder_form.save()

                # Add missing equipments
                # Do not delete any other equipment
                user = form.instance.updated_by
                for equipment in equipments:
                    EquipmentItem.objects.create(equipmentholder=self.object.equipmentholder,
                                                 equipment=equipment,
                                                 updated_by=user)

                # Call super
                return super().form_valid(form)
