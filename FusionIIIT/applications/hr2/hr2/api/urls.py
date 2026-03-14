from django.urls import path

from . import views


app_name = 'hr2'

urlpatterns = [
    # LTC form
    path('ltc/', views.LTC.as_view(), name='LTC_form'),
    #  cpda advance form
    path('cpdaadv/', views.CPDAAdvance.as_view(), name='CPDAAdvance_form'),
    #  appraisal form
    path('appraisal/', views.Appraisal.as_view(), name='Appraisal_form'),
    # cpda reimbursement form
    path('cpdareim/', views.CPDAReimbursement.as_view(),
        name='CPDAReimbursement_form'),
    #  leave form
    path('leave/', views.Leave.as_view(), name='Leave_form'),
    path('formManagement/', views.FormManagement.as_view(), name='formManagement'),
    path('tracking/', views.TrackProgress.as_view(), name='tracking'),
    path('formFetch/', views.FormFetch.as_view(), name='fetch_form'),
    #  create for GetForms
    path('getForms/', views.GetFormHistory.as_view(), name='getForms'),
    path('leaveBalance/', views.CheckLeaveBalance.as_view(), name='leaveBalance'),
    path('getDesignations/', views.DropDown.as_view(), name="designations"),
    path('getOutbox/', views.GetOutbox.as_view(), name='outbox'),
    path('getArchive/', views.ViewArchived.as_view(), name='archive'),
    path('getuserbyid/', views.UserById.as_view(), name='userById'),
]
