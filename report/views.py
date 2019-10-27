import logging

from django.views.generic.base import TemplateView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from login.permissions import IsUserOrAdminOrSuper

logger = logging.getLogger(__name__)


class ReportIndexView(TemplateView):
    template_name = 'report/index.html'


class DailyReportView(APIView):
    """
       View to retrieve current session.
       * Requires token authentication.
       """
    permission_classes = (IsAuthenticated,
                          IsUserOrAdminOrSuper,)

    def get(self, request, **kwargs):
        """
        Return current session.
        """
        session = SessionSerializer(request.auth.session)
        return Response(session.data)
