from django.contrib.auth import get_user_model
from django.core.exceptions import MultipleObjectsReturned

from applications.filetracking.models import Tracking
from applications.globals.models import Designation, ExtraInfo, HoldsDesignation
from applications.hr2.models import (
    Appraisalform,
    CPDAAdvanceform,
    CPDAReimbursementform,
    Employee,
    EmpConfidentialDetails,
    LeaveBalance,
    LeaveForm,
    LTCform,
)


User = get_user_model()


FORM_MODEL_REGISTRY = {
    "LTC": LTCform,
    "CPDAAdvance": CPDAAdvanceform,
    "CPDAReimbursement": CPDAReimbursementform,
    "Leave": LeaveForm,
    "Appraisal": Appraisalform,
}


def get_user_by_username(username):
    return User.objects.get(username=username)


def get_user_by_id(user_id):
    return User.objects.get(id=user_id)


def get_employee_by_id(employee_id):
    return Employee.objects.get(id=employee_id)


def get_employee_for_user(user):
    return Employee.objects.get(id=user.id)


def get_designation_by_name(name):
    return Designation.objects.get(name=name)


def get_leave_balance_for_employee(employee):
    return LeaveBalance.objects.get(empid=employee)


def get_leave_balance_by_username(username):
    user = get_user_by_username(username)
    employee = get_employee_for_user(user)
    return get_leave_balance_for_employee(employee)


def get_hold_designations_for_user(user):
    return HoldsDesignation.objects.select_related("designation").filter(user=user)


def get_receiver_designation(username, designation_name=None):
    receiver = get_user_by_username(username)
    designations = get_hold_designations_for_user(receiver)
    if designation_name:
        designation = designations.filter(designation__name=designation_name).first()
    else:
        designation = designations.first()
    return receiver, designation


def get_model_for_form_type(form_type):
    return FORM_MODEL_REGISTRY[form_type]


def get_form_by_id(form_type, form_id):
    model = get_model_for_form_type(form_type)
    return model.objects.get(id=form_id)


def get_forms_for_creator(form_type, creator):
    model = get_model_for_form_type(form_type)
    try:
        one = model.objects.get(created_by=creator)
        return [one], False
    except MultipleObjectsReturned:
        many = list(model.objects.filter(created_by=creator))
        return many, True
    except model.DoesNotExist:
        return [], True


def get_latest_tracking_owner(file_id):
    owner_qs = Tracking.objects.select_related("receiver_id").filter(file_id=file_id)
    latest = owner_qs.last()
    if not latest:
        return None
    return latest.receiver_id


def get_usernames_like(search_text):
    return User.objects.filter(username__icontains=search_text)


def get_employee_initial_context(employee):
    extra_info = ExtraInfo.objects.filter(user=employee.id).first()
    confidential = EmpConfidentialDetails.objects.filter(empid=employee).first()
    return extra_info, confidential
