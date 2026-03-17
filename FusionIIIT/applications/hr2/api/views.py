from django.contrib.auth import get_user_model
from django.core.exceptions import MultipleObjectsReturned
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from applications.filetracking.sdk.methods import view_archived, view_history, view_inbox, view_outbox

from .. import selectors, services
from .serializers import (
    Appraisal_serializer,
    CPDAAdvance_serializer,
    CPDAReimbursement_serializer,
    LeaveBalanace_serializer,
    Leave_serializer,
    LTC_serializer,
)


User = get_user_model()


SERIALIZER_REGISTRY = {
    "LTC": LTC_serializer,
    "CPDAAdvance": CPDAAdvance_serializer,
    "CPDAReimbursement": CPDAReimbursement_serializer,
    "Leave": Leave_serializer,
    "Appraisal": Appraisal_serializer,
}


class BaseProtectedAPIView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)


class GenericFormAPIView(BaseProtectedAPIView):
    form_type = None

    @property
    def serializer_class(self):
        return SERIALIZER_REGISTRY[self.form_type]

    def post(self, request):
        payload = services.get_payload_part(request.data, 0, {})
        user_info = services.get_payload_part(request.data, 1, {})
        try:
            serializer = services.run_serializer(self.serializer_class, payload)
            services.create_tracking_entry(user_info, serializer.data["id"], self.form_type)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except services.ServiceValidationError as exc:
            return Response(getattr(exc, "args", [str(exc)])[0], status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        creator = services.get_query_param(request, "name")
        forms, is_many = selectors.get_forms_for_creator(self.form_type, creator)
        serializer = self.serializer_class(forms, many=is_many)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        form_id = services.get_query_param(request, "id")
        receiver_payload = services.get_payload_part(request.data, 0, {})
        update_payload = services.get_payload_part(request.data, 1, {})
        form_instance = selectors.get_form_by_id(self.form_type, form_id)
        try:
            serializer = services.run_serializer(self.serializer_class, update_payload, instance=form_instance)
            services.forward_tracking_file(receiver_payload)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except services.ServiceValidationError as exc:
            return Response(getattr(exc, "args", [str(exc)])[0], status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        file_id = services.get_query_param(request, "id")
        if services.archive_tracking_file(file_id):
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class LTC(GenericFormAPIView):
    form_type = "LTC"


class CPDAAdvance(GenericFormAPIView):
    form_type = "CPDAAdvance"


class CPDAReimbursement(GenericFormAPIView):
    form_type = "CPDAReimbursement"


class Leave(GenericFormAPIView):
    form_type = "Leave"


class Appraisal(GenericFormAPIView):
    form_type = "Appraisal"


class FormManagement(BaseProtectedAPIView):
    def get(self, request, *args, **kwargs):
        username = services.get_query_param(request, "username")
        designation = services.get_query_param(request, "designation")
        inbox = view_inbox(username=username, designation=designation, src_module="HR")
        return Response(inbox, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        selectors.get_receiver_designation(request.data["receiver"], request.data.get("receiver_designation"))
        services.forward_tracking_file(request.data)
        return Response(status=status.HTTP_200_OK)


class GetFormHistory(BaseProtectedAPIView):
    def get(self, request, *args, **kwargs):
        form_type = services.get_query_param(request, "type")
        username = services.get_query_param(request, "id")
        user = selectors.get_user_by_username(username)
        forms, is_many = selectors.get_forms_for_creator(form_type, user)
        serializer = SERIALIZER_REGISTRY[form_type](forms, many=is_many)
        if is_many:
            return Response(serializer.data, status=status.HTTP_200_OK)
        if serializer.data:
            return Response([serializer.data], status=status.HTTP_200_OK)
        return Response([], status=status.HTTP_200_OK)


class TrackProgress(BaseProtectedAPIView):
    def get(self, request, *args, **kwargs):
        file_id = services.get_query_param(request, "id")
        progress = view_history(file_id)
        return Response({"status": progress}, status=status.HTTP_200_OK)


class FormFetch(BaseProtectedAPIView):
    def get(self, request, *args, **kwargs):
        file_id = services.get_query_param(request, "file_id")
        form_id = services.get_query_param(request, "id")
        form_type = services.get_query_param(request, "type")
        form = selectors.get_form_by_id(form_type, form_id)
        serializer = SERIALIZER_REGISTRY[form_type](form, many=False)
        creator = selectors.get_user_by_id(int(serializer.data["created_by"]))
        owner = selectors.get_latest_tracking_owner(file_id)
        current_owner = owner.username if owner else None
        return Response(
            {"form": serializer.data, "creator": creator.username, "current_owner": current_owner},
            status=status.HTTP_200_OK,
        )


class CheckLeaveBalance(BaseProtectedAPIView):
    serializer_class = LeaveBalanace_serializer

    def get(self, request, *args, **kwargs):
        username = services.get_query_param(request, "name")
        leave_balance = selectors.get_leave_balance_by_username(username)
        serializer = self.serializer_class(leave_balance, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        username = services.get_query_param(request, "name")
        leave_balance = selectors.get_leave_balance_by_username(username)
        payload = dict(request.data)
        payload["empid"] = leave_balance.empid.pk
        try:
            serializer = services.run_serializer(self.serializer_class, payload, instance=leave_balance)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except services.ServiceValidationError as exc:
            return Response(getattr(exc, "args", [str(exc)])[0], status=status.HTTP_400_BAD_REQUEST)


class DropDown(BaseProtectedAPIView):
    def get(self, request, *args, **kwargs):
        username = services.get_query_param(request, "username")
        user = selectors.get_user_by_username(username)
        designation_qs = selectors.get_hold_designations_for_user(user)
        data = [item.designation.name for item in designation_qs]
        return Response(data, status=status.HTTP_200_OK)


class UserById(BaseProtectedAPIView):
    def get(self, request, *args, **kwargs):
        user_id = services.get_query_param(request, "id")
        user = selectors.get_user_by_id(user_id)
        return Response({"username": user.username}, status=status.HTTP_200_OK)


class ViewArchived(BaseProtectedAPIView):
    def get(self, request, *args, **kwargs):
        username = services.get_query_param(request, "username")
        designation = services.get_query_param(request, "designation")
        archived_inbox = view_archived(username=username, designation=designation, src_module="HR")
        return Response(archived_inbox, status=status.HTTP_200_OK)


class GetOutbox(BaseProtectedAPIView):
    def get(self, request, *args, **kwargs):
        username = services.get_query_param(request, "username")
        designation = services.get_query_param(request, "designation")
        outbox = view_outbox(username=username, designation=designation, src_module="HR")
        return Response(outbox, status=status.HTTP_200_OK)
