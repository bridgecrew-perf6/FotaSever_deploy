from django.urls import path, include
from . import views
from .views import *


urlpatterns = [
    path('', views.IndexView, name="index"),
    path('login', views.login, name="login"),
    path('update', QuestionDetail.as_view(), name="update"),
    path("logout/", Logout_request, name="logout"),
    path('fetch_vin', views.VinFetchView, name="login1"),
    path('CamapainDetails', views.CamapainDetailsView, name="CampainCreate"),
    path('dk', views.CampaignSaveFirstPart, name="login3"),
    path('ECUDetails', views.CamapaignDetails1View, name="CamapaignDetails1"),
    path('ecuNameFetch', views.FetchEcuName, name="FetchEcu"),
    path('FecthScomo', views.FetchScomoName, name="FetchScomo1"),
    path('FecthPackageFile', views.FetchPackageName, name="Fetchpackagefile"),
    path('FetchEcu', views.SaveEcuDetails, name="FetchEcu"),
    path('UploadContent', views.uploadContentView, name="UploadContent"),
    path('DynamicHmi', views.DynamicHmi, name="dynamicHmi"),
    path('Dynamic_cmapaignname_fetch', views.Campaign_Name_fetch,name="campaignName"),
    path('HmiSave', views.dynamic_hmi_save_view, name="hmi_save"),
    path('LaunchCampaign', views.LauchCampaignView, name="LaunchCampaign"),
    path('CampaignData', views.Campaign_data, name="camapaignData"),
    path('contentUpload', views.ContentUpload, name="contentUpload"),
    path('Launch_campaign1', views.Launch_campaign, name="LaunchCampaign1"),
    path('CheckContent', views.CheckContent, name="ChkContent"),
    path('FetchPackageData', views.FetchPackageData, name="FetchPackageData"),
    path('SetCon1', views.SetConfigRef1, name="SetConfigRef"),
    path('SetRef1', views.SetReprogRef1, name="SetReprogRef"),
    path('update_page', views.FirstPageView, name="Update_page"),
    path('VinCheck', views.VehicleManagementVinCheck, name="vinCheck"),
    path('VehicleRegistration', views.VehicleRegistration, name="VehicleRegistration"),
    path('FetchVinECUData', views.FetchVinECUData, name="FetchVinECUData"),
    path('FetchVinOnlyData', views.FetchVinOnlyData, name="FetchVinOnlyData"),
    path('api/ExeFetchVin', ExeFetchVinAPIView.as_view()),
    path('FetchAndCheckVinDetails', views.FetchAndCheckVinDetails, name="FetchAndCheckVinDetails"),
    path('CheckCampaign', views.CampaignCheck, name="CheckCampaign"),
    path('FetchFilterCampaign', views.FetchFilterCampaign, name="FetchFilterCampaign"),
    path('GetCampaignStatus', views.GetCampaignStatus, name="GetCampaignStatus"),
    path('GetVinStatus', views.check_all_vin_status, name="GetVinStatus")
]

