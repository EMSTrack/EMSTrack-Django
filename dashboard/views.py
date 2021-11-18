import logging
from django.views.generic.base import TemplateView
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

logger = logging.getLogger(__name__)

class DashboardView(TemplateView):
    template_name = 'dashboard/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # for user in User.objects.all():
        #     Token.objects.get_or_create(user=user)
        
        context['token'] = None
        logger.error(request.user)

        return context