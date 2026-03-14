from rest_framework import serializers
from applications.hr2.models import LTCform, CPDAAdvanceform, CPDAReimbursementform, LeaveForm, Appraisalform, LeaveBalance


class LTC_serializer(serializers.ModelSerializer):
    class Meta:
        model = LTCform
        fields = (
            'id',
            'employeeId',
            'name',
            'blockYear',
            'pfNo',
            'basicPaySalary',
            'designation',
            'departmentInfo',
            'leaveRequired',
            'leaveStartDate',
            'leaveEndDate',
            'dateOfDepartureForFamily',
            'natureOfLeave',
            'purposeOfLeave',
            'hometownOrNot',
            'placeOfVisit',
            'addressDuringLeave',
            'modeofTravel',
            'detailsOfFamilyMembersAlreadyDone',
            'detailsOfFamilyMembersAboutToAvail',
            'detailsOfDependents',
            'amountOfAdvanceRequired',
            'certifiedThatFamilyDependents',
            'certifiedThatAdvanceTakenOn',
            'adjustedMonth',
            'submissionDate',
            'phoneNumberForContact',
            'approved',
            'approvedDate',
            'created_by',
            'approved_by',
        )

    def create(self, validated_data):
        return LTCform.objects.create(**validated_data)


class CPDAAdvance_serializer(serializers.ModelSerializer):
    class Meta:
        model = CPDAAdvanceform
        fields = (
            'id',
            'employeeId',
            'name',
            'designation',
            'pfNo',
            'purpose',
            'amountRequired',
            'advanceDueAdjustment',
            'submissionDate',
            'balanceAvailable',
            'advanceAmountPDA',
            'amountCheckedInPDA',
            'approved',
            'approvedDate',
            'created_by',
            'approved_by',
        )

    def create(self, validated_data):
        return CPDAAdvanceform.objects.create(**validated_data)


class Appraisal_serializer(serializers.ModelSerializer):
    class Meta:
        model = Appraisalform
        fields = (
            'id',
            'employeeId',
            'name',
            'designation',
            'disciplineInfo',
            'specificFieldOfKnowledge',
            'currentResearchInterests',
            'coursesTaught',
            'newCoursesIntroduced',
            'newCoursesDeveloped',
            'otherInstructionalTasks',
            'thesisSupervision',
            'sponsoredReseachProjects',
            'otherResearchElement',
            'publication',
            'referredConference',
            'conferenceOrganised',
            'membership',
            'honours',
            'editorOfPublications',
            'expertLectureDelivered',
            'membershipOfBOS',
            'otherExtensionTasks',
            'administrativeAssignment',
            'serviceToInstitute',
            'otherContribution',
            'performanceComments',
            'submissionDate',
            'approved',
            'approvedDate',
            'created_by',
            'approved_by',
        )

    def create(self, validated_data):
        return Appraisalform.objects.create(**validated_data)


class CPDAReimbursement_serializer(serializers.ModelSerializer):
    class Meta:
        model = CPDAReimbursementform
        fields = (
            'id',
            'employeeId',
            'name',
            'designation',
            'pfNo',
            'advanceTaken',
            'purpose',
            'adjustmentSubmitted',
            'balanceAvailable',
            'advanceDueAdjustment',
            'advanceAmountPDA',
            'amountCheckedInPDA',
            'submissionDate',
            'approved',
            'approvedDate',
            'created_by',
            'approved_by',
        )

    def create(self, validated_data):
        return CPDAReimbursementform.objects.create(**validated_data)


class Leave_serializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveForm
        fields = (
            'id',
            'employee',
            'name',
            'designation',
            'submissionDate',
            'personalfileNo',
            'departmentInfo',
            'leaveStartDate',
            'leaveEndDate',
            'Noof_CasualLeave',
            'Noof_specialCasualLeave',
            'Noof_earnedLeave',
            'Noof_commutedLeave',
            'Noof_restrictedHoliday',
            'Noof_vacationLeave',
            'Noof_maternityLeave',
            'Noof_childCareLeave',
            'Noof_paternityLeave',
            'Noof_halfPayLeave',
            'LeavingStation',
            'StationLeave_startdate',
            'StationLeave_enddate',
            'Address_During_StationLeave',
            'Purpose_of_leave',
            'AcademicResponsibility_user',
            'AcademicResponsibility_designation',
            'AcademicResponsibility_status',
            'AdministrativeResponsibility_user',
            'AdministrativeResponsibility_designation',
            'AdministrativeResponsibility_status',
            'Remarks',
            'approvedDate',
            'approved_by',
            'approved_by_designation',
            'first_recieved_by',
            'first_recieved_designation',
            'status',
            'attached_pdf',
            'attached_pdf_name',
            'file_id',
            'application_type',
        )

    def create(self, validated_data):
        return LeaveForm.objects.create(**validated_data)


class LeaveBalanace_serializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveBalance
        fields = (
            'empid',
            'casual_leave_taken',
            'special_casual_leave_taken',
            'earned_leave_taken',
            'half_pay_leave_taken',
            'maternity_leave_taken',
            'child_care_leave_taken',
            'paternity_leave_taken',
            'leave_encashment_taken',
            'restricted_holiday_taken',
        )

    def create(self, validated_data):
        return LeaveBalance.objects.create(**validated_data)


# class Deignations(serializers.ModelSerializer):
#     class Meta:
#         model = Deignations
#         fields = '__all__'

#     def create(self,validated_data):
#         return
