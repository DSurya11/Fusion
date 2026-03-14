import json
from datetime import datetime

from django.http import JsonResponse

from applications.filetracking.sdk.methods import archive_file, create_file, forward_file
from applications.hr2.models import LeaveForm

from . import selectors


class ServiceValidationError(Exception):
    pass


class ServiceNotFoundError(Exception):
    pass


FORM_TYPE_FILETRACKING = {
    "LTC": "LTC",
    "CPDAAdvance": "CPDAAdvance",
    "CPDAReimbursement": "CPDAReimbursement",
    "Leave": "Leave",
    "Appraisal": "Appraisal",
}


def get_payload_part(payload, index, default=None):
    if isinstance(payload, (list, tuple)) and len(payload) > index:
        return payload[index]
    return default if default is not None else {}


def get_query_param(request, key, required=True):
    value = request.query_params.get(key)
    if required and not value:
        raise ServiceValidationError(f"Missing query param: {key}")
    return value


def run_serializer(serializer_class, payload, instance=None):
    serializer = serializer_class(instance, data=payload) if instance else serializer_class(data=payload)
    if not serializer.is_valid():
        raise ServiceValidationError(serializer.errors)
    serializer.save()
    return serializer


def create_tracking_entry(user_info, src_object_id, form_type):
    return create_file(
        uploader=user_info["uploader_name"],
        uploader_designation=user_info["uploader_designation"],
        receiver=user_info["receiver_name"],
        receiver_designation=user_info["receiver_designation"],
        src_module="HR",
        src_object_id=str(src_object_id),
        file_extra_JSON={"type": FORM_TYPE_FILETRACKING[form_type]},
        attached_file=None,
    )


def forward_tracking_file(receiver_payload):
    forward_file(
        file_id=receiver_payload["file_id"],
        receiver=receiver_payload["receiver"],
        receiver_designation=receiver_payload["receiver_designation"],
        remarks=receiver_payload["remarks"],
        file_extra_JSON=receiver_payload["file_extra_JSON"],
    )


def archive_tracking_file(file_id):
    return archive_file(file_id=file_id)


def parse_offline_payload(form_data):
    try:
        return {
            "employee_details": json.loads(form_data.get("employeeDetails", "{}")),
            "leave_details": json.loads(form_data.get("leaveDetails", "{}")),
            "station_leave": json.loads(form_data.get("stationLeave", "{}")),
            "responsibility_transfer": json.loads(form_data.get("responsibilityTransfer", "{}")),
            "forward_to": json.loads(form_data.get("forwardTo", "{}")),
        }
    except json.JSONDecodeError as exc:
        raise ServiceValidationError(f"Invalid JSON format in one of the fields: {str(exc)}")


def resolve_optional_responsibilities(responsibility_transfer):
    academic_user = None
    academic_designation = None
    admin_user = None
    admin_designation = None

    if responsibility_transfer.get("academicResponsibility"):
        payload = responsibility_transfer["academicResponsibility"]
        academic_user = selectors.get_employee_by_id(payload["id"])
        academic_designation = selectors.get_designation_by_name(payload["designation"])

    if responsibility_transfer.get("administrativeResponsibility"):
        payload = responsibility_transfer["administrativeResponsibility"]
        admin_user = selectors.get_employee_by_id(payload["id"])
        admin_designation = selectors.get_designation_by_name(payload["designation"])

    return academic_user, academic_designation, admin_user, admin_designation


def create_offline_leave_form(parsed, files):
    employee_details = parsed["employee_details"]
    leave_details = parsed["leave_details"]
    station_leave = parsed["station_leave"]
    responsibility_transfer = parsed["responsibility_transfer"]
    forward_to = parsed["forward_to"]

    if "id" not in forward_to:
        raise ServiceValidationError("Missing required field: forwardTo")

    required_fields = ["leaveStartDate", "leaveEndDate", "purpose"]
    missing = [field for field in required_fields if field not in leave_details]
    if missing:
        raise ServiceValidationError(f"Missing required fields: {', '.join(missing)}")

    leave_start_date = datetime.strptime(leave_details.get("leaveStartDate"), "%Y-%m-%d").date()
    leave_end_date = datetime.strptime(leave_details.get("leaveEndDate"), "%Y-%m-%d").date()
    if leave_end_date < leave_start_date:
        raise ServiceValidationError("Leave end date cannot be before start date")

    employee_id = employee_details.get("id")
    employee = selectors.get_employee_by_id(employee_id)
    forward_designation = selectors.get_designation_by_name(forward_to["designation"])

    academic_user, academic_designation, admin_user, admin_designation = resolve_optional_responsibilities(
        responsibility_transfer
    )

    attached_pdf = files.get("attachedPdf")
    leave_form = LeaveForm.objects.create(
        employee=employee,
        name=employee_details.get("name"),
        designation=employee_details.get("designation"),
        personalfileNo=employee_details.get("pfno"),
        submissionDate=datetime.now().date(),
        departmentInfo=employee_details.get("department", "N/A"),
        leaveStartDate=leave_start_date,
        leaveEndDate=leave_end_date,
        Purpose_of_leave=leave_details.get("purpose"),
        Noof_CasualLeave=int(leave_details.get("casualLeave", 0)),
        Noof_vacationLeave=int(leave_details.get("vacationLeave", 0)),
        Noof_earnedLeave=int(leave_details.get("earnedLeave", 0)),
        Noof_commutedLeave=int(leave_details.get("commutedLeave", 0)),
        Noof_specialCasualLeave=int(leave_details.get("specialCasualLeave", 0)),
        Noof_restrictedHoliday=int(leave_details.get("restrictedHoliday", 0)),
        Noof_halfPayLeave=int(leave_details.get("halfPayLeave", 0)),
        Noof_maternityLeave=int(leave_details.get("maternityLeave", 0)),
        Noof_childCareLeave=int(leave_details.get("childCareLeave", 0)),
        Noof_paternityLeave=int(leave_details.get("paternityLeave", 0)),
        Remarks=leave_details.get("remarks", "N/A"),
        LeavingStation=station_leave.get("isStationLeave", False),
        StationLeave_startdate=station_leave.get("stationLeaveStartDate"),
        StationLeave_enddate=station_leave.get("stationLeaveEndDate"),
        Address_During_StationLeave=station_leave.get("stationLeaveAddress"),
        status="Accepted",
        AcademicResponsibility_user=academic_user,
        AcademicResponsibility_designation=academic_designation,
        AcademicResponsibility_status="Accepted",
        AdministrativeResponsibility_user=admin_user,
        AdministrativeResponsibility_designation=admin_designation,
        AdministrativeResponsibility_status="Accepted",
        approved_by=selectors.get_employee_by_id(forward_to["id"]),
        approved_by_designation=forward_designation,
        approvedDate=datetime.now().date(),
        first_recieved_by=selectors.get_employee_by_id(forward_to["id"]),
        first_recieved_designation=forward_designation,
        attached_pdf=attached_pdf.read() if attached_pdf else None,
        attached_pdf_name=attached_pdf.name if attached_pdf else None,
        application_type="Offline",
    )

    uploader_employee = selectors.get_employee_by_id(employee_id)
    receiver_employee = selectors.get_employee_by_id(forward_to["id"])
    file_id = create_file(
        uploader=uploader_employee.id.username,
        uploader_designation=employee_details.get("designation"),
        receiver=receiver_employee.id.username,
        receiver_designation=forward_to["designation"],
        src_module="HR",
        src_object_id=str(leave_form.id),
        file_extra_JSON={"type": "Leave"},
        attached_file=None,
    )
    leave_form.file_id = file_id
    leave_form.save(update_fields=["file_id"])

    leave_balance = selectors.get_leave_balance_for_employee(employee)
    leave_balance.casual_leave_taken += leave_form.Noof_CasualLeave
    leave_balance.special_casual_leave_taken += leave_form.Noof_specialCasualLeave
    leave_balance.earned_leave_taken += leave_form.Noof_earnedLeave + (2 * leave_form.Noof_vacationLeave)
    leave_balance.half_pay_leave_taken += leave_form.Noof_halfPayLeave + (2 * leave_form.Noof_commutedLeave)
    leave_balance.maternity_leave_taken += leave_form.Noof_maternityLeave
    leave_balance.child_care_leave_taken += leave_form.Noof_childCareLeave
    leave_balance.paternity_leave_taken += leave_form.Noof_paternityLeave
    leave_balance.restricted_holiday_taken += leave_form.Noof_restrictedHoliday
    leave_balance.save()

    return leave_form, file_id


def create_online_leave_form(user, form_data, files):
    required_fields = [
        "name",
        "designation",
        "pfno",
        "department",
        "leaveStartDate",
        "leaveEndDate",
        "purpose",
        "forwardTo",
    ]
    missing = [field for field in required_fields if not form_data.get(field)]
    if missing:
        raise ServiceValidationError(f"Missing required fields: {', '.join(missing)}")

    leave_start_date = datetime.strptime(form_data.get("leaveStartDate"), "%Y-%m-%d").date()
    leave_end_date = datetime.strptime(form_data.get("leaveEndDate"), "%Y-%m-%d").date()
    if leave_end_date < leave_start_date:
        raise ServiceValidationError("Leave end date cannot be before start date")

    station_leave = form_data.get("stationLeave", "false").lower() == "true"
    station_leave_start = form_data.get("stationLeaveStartDate")
    station_leave_end = form_data.get("stationLeaveEndDate")
    station_leave_address = form_data.get("stationLeaveAddress")

    if station_leave:
        if not all([station_leave_start, station_leave_end, station_leave_address]):
            raise ServiceValidationError("Station leave details are required when station leave is checked")
        station_leave_start = datetime.strptime(station_leave_start, "%Y-%m-%d").date()
        station_leave_end = datetime.strptime(station_leave_end, "%Y-%m-%d").date()
        if station_leave_end < station_leave_start:
            raise ServiceValidationError("Station leave end date cannot be before start date")
    else:
        station_leave_start = None
        station_leave_end = None
        station_leave_address = None

    employee = selectors.get_employee_for_user(user)

    academic_user = None
    academic_designation = None
    academic_responsibility_id = form_data.get("academicResponsibility")
    if academic_responsibility_id:
        academic_user = selectors.get_employee_by_id(academic_responsibility_id)
        academic_designation = selectors.get_designation_by_name(form_data.get("academicResponsibility_designation"))

    admin_user = None
    admin_designation = None
    administrative_responsibility_id = form_data.get("administrativeResponsibility")
    if administrative_responsibility_id:
        admin_user = selectors.get_employee_by_id(administrative_responsibility_id)
        admin_designation = selectors.get_designation_by_name(form_data.get("administrativeResponsibility_designation"))

    first_received_by = selectors.get_employee_by_id(form_data.get("forwardTo"))
    first_received_designation = selectors.get_designation_by_name(form_data.get("forwardTo_designation"))

    attached_pdf = files.get("attached_pdf")
    leave_form = LeaveForm.objects.create(
        employee=employee,
        name=form_data.get("name"),
        designation=form_data.get("designation"),
        personalfileNo=form_data.get("pfno"),
        submissionDate=form_data.get("date"),
        departmentInfo=form_data.get("department"),
        leaveStartDate=leave_start_date,
        leaveEndDate=leave_end_date,
        Purpose_of_leave=form_data.get("purpose"),
        Noof_CasualLeave=int(form_data.get("casualLeave", 0)),
        Noof_vacationLeave=int(form_data.get("vacationLeave", 0)),
        Noof_earnedLeave=int(form_data.get("earnedLeave", 0)),
        Noof_commutedLeave=int(form_data.get("commutedLeave", 0)),
        Noof_specialCasualLeave=int(form_data.get("specialCasualLeave", 0)),
        Noof_restrictedHoliday=int(form_data.get("restrictedHoliday", 0)),
        Noof_halfPayLeave=int(form_data.get("halfPayLeave", 0)),
        Noof_maternityLeave=int(form_data.get("maternityLeave", 0)),
        Noof_childCareLeave=int(form_data.get("childCareLeave", 0)),
        Noof_paternityLeave=int(form_data.get("paternityLeave", 0)),
        Remarks=form_data.get("remarks", "N/A"),
        LeavingStation=station_leave,
        StationLeave_startdate=station_leave_start,
        StationLeave_enddate=station_leave_end,
        Address_During_StationLeave=station_leave_address,
        AcademicResponsibility_user=academic_user,
        AcademicResponsibility_designation=academic_designation,
        AcademicResponsibility_status="Pending" if academic_user else "Accepted",
        AdministrativeResponsibility_user=admin_user,
        AdministrativeResponsibility_designation=admin_designation,
        AdministrativeResponsibility_status="Pending" if admin_user else "Accepted",
        first_recieved_by=first_received_by,
        first_recieved_designation=first_received_designation,
        status="Pending",
        attached_pdf=attached_pdf.read() if attached_pdf else None,
        attached_pdf_name=attached_pdf.name if attached_pdf else None,
    )

    file_id = None
    if not academic_user and not admin_user:
        file_id = create_file(
            uploader=employee.id,
            uploader_designation=form_data.get("designation"),
            receiver=first_received_by.id.username,
            receiver_designation=first_received_designation.name,
            src_module="HR",
            src_object_id=str(leave_form.id),
            file_extra_JSON={"type": "Leave"},
            attached_file=None,
        )
        leave_form.file_id = file_id
        leave_form.save(update_fields=["file_id"])

    return leave_form, file_id


def build_employee_search_response(search_text):
    users = selectors.get_usernames_like(search_text)
    user_list = []
    for user in users:
        designations = selectors.get_hold_designations_for_user(user)
        if not designations.exists():
            continue
        for hd in designations:
            user_list.append(
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "designation": hd.designation.name,
                }
            )
    return user_list
