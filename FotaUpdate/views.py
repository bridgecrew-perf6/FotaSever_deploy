import datetime
import os
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View
from .forms import LoginForm, UpdateForm, UpdateCurrentDetails
from .Azurefunctions import get_current_version, upload_file_on_cloud, update_desired_property_and_file, update_twin, \
    get_reported_property, get_twin
from django.core.files.storage import FileSystemStorage
import uuid
from .models import VinNumber, EcuName, ScomoID, ContentFile, CampaignDetail, FwVersion, dynamichmi, DiscardedVin
from .All_functions import Read_csv
from django.contrib.auth import authenticate, logout
from django.contrib.auth import login as auth_login
from .decorators import allowed_users
from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.files.storage import default_storage
import requests
from .serializers import ExeFetchVin
import json
from datetime import datetime
import datetime
# Create your views here.

def IndexView(request):
    return render(request, 'index.html')


def login(request):
    form = LoginForm()
    if request.method == 'POST':
        forms = LoginForm(request.POST)
        if forms.is_valid():
            cd = forms.cleaned_data
            username = cd.get('username')
            request.session['username'] = username
            password = cd.get('password')
            print(request.user.username)
            user = authenticate(username=username, password=password)
            if user is not None:
                auth_login(request, user)
                return redirect('Update_page')
            else:
                return redirect('login')
    context = {'form': form}
    return render(request, 'login.html', context)


def Logout_request(request):
    logout(request)
    request.session.clear()
    return redirect('index')


class QuestionDetail(View):
    try:
        template_name = 'update.html'

        def get_context_data(self, **kwargs):
            if 'response_form' not in kwargs:
                kwargs['response_form'] = UpdateForm()
            if 'comment_form' not in kwargs:
                kwargs['comment_form'] = UpdateCurrentDetails()
            return kwargs

        def get(self, request, *args, **kwargs):
            if "username" in request.session:
                return render(request, self.template_name, self.get_context_data())
            else:
                return redirect('login')

        def post(self, request, *args, **kwargs):
            ctxt = {}
            keys = list(request.POST)
            print(keys)
            if 'response' in keys:
                response_form = UpdateForm(request.POST, initial={'kl': 'dl'})
                if response_form.is_valid() and request.POST['device_ids'] != "Select device id":
                    request.session['device_name'] = request.POST["device_ids"]
                    # pass this device_name to the get_current_version function
                    current_fw_version, previous_fw_version = get_current_version(request.POST["device_ids"])
                    ctxt['response_form'] = response_form
                    ctxt['current_fw_version'] = current_fw_version
                    ctxt['previous_fw_version'] = previous_fw_version
                else:
                    ctxt['response_form'] = response_form

            elif 'comment' in keys:
                comment_form = UpdateCurrentDetails(request.POST, request.FILES)
                get_device_name = request.session.get('device_name')
                if comment_form.is_valid() and get_device_name != "Select device id":
                    latest_version = request.POST["latest_version"]
                    latest_version = str(latest_version)
                    file_name = request.FILES["browse_file"]
                    # create unique file name
                    filename, file_extension = os.path.splitext(file_name.name)
                    file_names = filename + str(uuid.uuid4())
                    joined_name = os.path.join(file_names + file_extension)
                    fs = FileSystemStorage()
                    filename = fs.save(joined_name, file_name)
                    upload_file_on_cloud(joined_name)
                    update_desired_property_and_file(get_device_name, latest_version, joined_name)
                    # after update device twin rest session value
                    request.session['device_name'] = "Select device id"
                else:
                    ctxt['comment_form'] = comment_form
            return render(request, self.template_name, self.get_context_data(**ctxt))
    except:
        print("something went wrong")


def VinFetchView(request):
    if request.method == 'POST':
        vin = request.POST['vin']
        if vin == "GiveVin":
            vin_dict = {}
            all_vin = VinNumber.objects.values("vinNumber")
            i = 0
            for value in all_vin:
                vin_number_counter = "VinNumber"
                i = i + 1
                vin_number_counter = vin_number_counter + str(i)
                vin_dict[vin_number_counter] = value["vinNumber"]
        return JsonResponse(vin_dict)


def CampaignSaveFirstPart(request):
    if request.method == 'POST':
        vin_list = []
        request.session['CamapaignName'] = request.POST["CamapaignName"]
        request.session['CampaignType'] = request.POST["CampaignType"]
        request.session['StartDate'] = request.POST["StartDate"]
        request.session['EndDate'] = request.POST["EndDate"]
        if request.POST["mode"] == "manual":
            vin_list.append(request.POST["vin"])
            request.session['vin'] = vin_list
        if request.POST["mode"] == "import":
            files = request.FILES['file']
            decoded_file = files.read().decode('utf-8').splitlines()
            vin_list = Read_csv(decoded_file)
            print(vin_list)
            request.session['vin'] = vin_list
            print(request.session.get('vin'))
        return HttpResponse("Done")
    return HttpResponse(status=204)


def FetchEcuName(request):
    all_ecu_name = EcuName.objects.values("ecuName")
    i = 0
    ecu_dict = {}
    for value in all_ecu_name:
        ecu_number_counter = "ecuNumber"
        i = i + 1
        ecu_number_counter = ecu_number_counter + str(i)
        ecu_dict[ecu_number_counter] = value["ecuName"]
    return JsonResponse(ecu_dict)


def FetchScomoName(request):
    if request.method == 'POST':
        ecu_name = request.POST['ecu_name']
        ecu_scomoId = ScomoID.objects.all().filter(ecuName=ecu_name)
        i = 0
        ecu_scomo_dict = {}
        for value in ecu_scomoId:
            scomo_number_counter = "scomo_id"
            i = i + 1
            scomo_number_counter = scomo_number_counter + str(i)
            ecu_scomo_dict[scomo_number_counter] = value.scomoID
        return JsonResponse(ecu_scomo_dict)


def FetchPackageName(request):
    if request.method == 'POST':
        scomo_id = request.POST['scomo_id']
        packagefiles = ContentFile.objects.all().filter(ScomoID=scomo_id)
        i = 0
        package_file_dict = {}
        for value in packagefiles:
            package_number_counter = "package_file"
            i = i + 1
            package_number_counter = package_number_counter + str(i)
            package_file_dict[package_number_counter] = value.FileName
        return JsonResponse(package_file_dict)


def SaveEcuDetails(request):
    if request.method == 'POST':
        request.session['ecunames'] = request.POST.getlist('ecu_name[]')
        request.session['scomo_id'] = request.POST.getlist('scomo_id[]')
        request.session['source_version'] = request.POST.getlist('source_version[]')
        request.session['target_version'] = request.POST.getlist('target_version[]')
        request.session['package_file'] = request.POST.getlist('package_file[]')
        if "CamapaignName" in request.session:
            if request.session.get('CamapaignName') != "":
                Campaign_object = CampaignDetail()
                Campaign_object.campaignName = request.session.get("CamapaignName")
                Campaign_object.CampaignType = request.session.get("CampaignType")
                Campaign_object.startdate = request.session.get("StartDate")
                Campaign_object.endDate = request.session.get("EndDate")
                Campaign_object.save()
                vin_number_list = []
                discarded_vinList = []
                for vin_number in request.session.get('vin'):
                    vin_number_object = VinNumber.objects.all().filter(vinNumber=vin_number)
                    if not vin_number_object:
                        discarded_vinList.append(vin_number)
                    else:
                        for values in vin_number_object:
                            vin_number_list.append(values)

                ecu_name_list = []
                for ecu_name in request.session.get('ecunames'):
                    ecu_name_object = EcuName.objects.all().filter(ecuName=ecu_name)
                    for values in ecu_name_object:
                        ecu_name_list.append(values)

                scomo_id_list = []
                for scomo_id in request.session.get('scomo_id'):
                    scomo_id_object = ScomoID.objects.all().filter(scomoID=scomo_id)
                    for values in scomo_id_object:
                        scomo_id_list.append(values)

                package_file_list = []
                for package_file in request.session.get('package_file'):
                    package_object = ContentFile.objects.all().filter(FileName=package_file)
                    for values in package_object:
                        package_file_list.append(values)

                Campaign_object.vinNumber.add(*vin_number_list)
                Campaign_object.ecuNames.add(*ecu_name_list)
                Campaign_object.scomoID.add(*scomo_id_list)
                Campaign_object.packageFile.add(*package_file_list)

                # discarded vin save
                for discared_vin in discarded_vinList:
                    discardedVinObject = DiscardedVin()
                    discardedVinObject.vin = discared_vin
                    discardedVinObject.campaignName = Campaign_object
                    discardedVinObject.save()

                list_all_Fw_object = []
                for sv, tv, sid in zip(request.session.get('source_version'), request.session.get('target_version'),
                                       request.session.get('scomo_id')):
                    FwVersion_object = FwVersion()
                    FwVersion_object.sourceVersion = sv
                    FwVersion_object.TargetVersion = tv
                    scomo_id_object = ScomoID.objects.all().filter(scomoID=sid)
                    for values in scomo_id_object:
                        FwVersion_object.scomoID = values
                    FwVersion_object.save()
                    list_all_Fw_object.append(FwVersion_object)
                Campaign_object.fwversion.add(*list_all_Fw_object)
                return HttpResponse("")


# dynamic hmi views
def Campaign_Name_fetch(request):
    if request.method == 'POST':
        campaign_nameObject = CampaignDetail.objects.all()
        i = 0
        campaign_name_dict = {}
        for value in campaign_nameObject:
            campaign_name_counter = "Campaign_name"
            i = i + 1
            campaign_name_counter = campaign_name_counter + str(i)
            campaign_name_dict[campaign_name_counter] = value.campaignName
        return JsonResponse(campaign_name_dict)


def dynamic_hmi_save_view(request):
    if request.method == 'POST':
        files = request.FILES['file']
        cname = request.POST['cname']
        CampaignDetail_id_object = CampaignDetail.objects.all().filter(campaignName=cname)
        dynamic_hmi = dynamichmi()
        for value in CampaignDetail_id_object:
            dynamic_hmi.campaignName = value
        dynamic_hmi.xmlfile = files
        dynamic_hmi.save()
    return HttpResponse('')


def Campaign_data(request):
    if request.method == 'POST':
        Final_dict = {}
        campaign_name = request.POST['CampaignName']
        request.session['Launch_campaignName'] = campaign_name
        CampaignDetail_id_object = CampaignDetail.objects.all().filter(campaignName=campaign_name)
        for value in CampaignDetail_id_object:
            Final_dict['CT'] = value.CampaignType
            Final_dict['SD'] = value.startdate
            Final_dict['ED'] = value.endDate
            list_of_all_scomoId = []
            list_of_all_ecuName = set()
            for s in value.scomoID.all():
                list_of_all_scomoId.append(s.scomoID)
                # ecuname.
                scomo_id_object = ScomoID.objects.all().filter(scomoID=s.scomoID)
                for values in scomo_id_object:
                    ecu_name_object = values.ecuName
                    list_of_all_ecuName.add(ecu_name_object.ecuName)
            Final_dict['SI'] = list_of_all_scomoId
            Final_dict['EN'] = list(list_of_all_ecuName)
            return JsonResponse(Final_dict)


def ContentUpload(request):
    if request.method == 'POST':
        scomo_id = request.POST['scomo_id']
        ecu_name = request.POST['ecu_name']
        files = request.FILES['file']
        file_name = request.FILES['file'].name
        Content_object = ContentFile()
        Content_object.FileName = file_name
        Content_object.BrowsFile = files
        Content_object.Date = datetime.datetime.now()
        scomo_id_object = ScomoID.objects.all().filter(scomoID=scomo_id)
        for value in scomo_id_object:
            print(value)
            Content_object.ScomoID = value
        Content_object.save()
        return HttpResponse('')


def Launch_campaign(request):
    if request.method == 'POST':
        dataStructureDict = {}
        Final_dict = {}
        Final_dict['status'] = 'OK'
        ecu_mapping = {'IVI': 'RDO', 'METER': 'TDB', 'HUD': 'HMD', 'IVC': 'TCU', 'ADAS': 'DAS'}
        Campaign_name = request.session.get("Launch_campaignName")
        CampaignDetail_id_object = CampaignDetail.objects.all().filter(campaignName=Campaign_name)
        for value in CampaignDetail_id_object:
            startDate = value.startdate
            end_date = value.endDate
            vin_number_list = []
            vinNumber_twinList = []
            for v in value.vinNumber.all():
                vin_number_list.append(v.vinNumber)
                vinNumber_twinList.append(get_twin(v.vinNumber))
            flag = 0
            scomo_set = set()

            for s in value.scomoID.all():
                temp = {}
                s.scomoID_name = s.scomoID.replace('.', '_').lower()
                scomo_name_fileref = s.scomoID_name + "_fileref"
                scomo_name_fileref = scomo_name_fileref.lower()

                # ecuname.
                scomo_id_object = ScomoID.objects.all().filter(scomoID=s.scomoID)
                for values in scomo_id_object:
                    ecu_name_object = values.ecuName
                    ecu_name_without_map = ecu_name_object.ecuName

                # scomo_id package file name.
                file_name = ""
                for values in value.packageFile.all():
                    if values.ScomoID.scomoID == s.scomoID:
                        file_name = values.FileName

                # firmware sorce and target version
                source_version = ""
                target_version = ""
                for values in value.fwversion.all():
                    if values.scomoID.scomoID == s.scomoID:
                        source_version = values.sourceVersion
                        target_version = values.TargetVersion

                # update twin according to reported property
                temp[s.scomoID_name] = target_version
                # call azure function
                sas_url = upload_file_on_cloud(file_name)
                temp[scomo_name_fileref] = sas_url
                ecu_name = ecu_mapping[ecu_name_without_map]
                dataStructureDict[ecu_name] = temp

                for k in vinNumber_twinList:
                    source_version_fromDevice = get_reported_property(k, ecu_name, s.scomoID_name)
                    if source_version != source_version_fromDevice:
                        flag = 1
                        Final_dict['status'] = "NOK"
                        scomo_set.add(s.scomoID_name)

            Final_dict['scomo_id'] = list(scomo_set)
            if flag == 0:
                update_twin(dataStructureDict, vin_number_list, Campaign_name)
                return JsonResponse(Final_dict)
            if flag == 1:
                return JsonResponse(Final_dict)


def FetchPackageData(request):
    if request.method == 'POST':
        package_data = {}
        package_file = request.POST['package_fileName']
        package_object = ContentFile.objects.all().filter(FileName=package_file)
        for value in package_object:
            package_data['filename'] = value.FileName
            package_data['date'] = value.Date
        return JsonResponse(package_data)


@allowed_users(allowed_roles=['Admin', 'Campaign Manager'])
def LauchCampaignView(request):
    ctext = {'user': request.user.username, 'profile': request.user.groups.all()[0].name}
    return render(request, 'LaunchCampaign.html', ctext)


@allowed_users(allowed_roles=['Admin', 'ECU Designer'])
def uploadContentView(request):
    ctext = {'user': request.user.username, 'profile': request.user.groups.all()[0].name}
    return render(request, 'uploadContent.html', ctext)


@allowed_users(allowed_roles=['Admin', 'Campaign Manager'])
def DynamicHmi(request):
    ctext = {'user': request.user.username, 'profile': request.user.groups.all()[0].name}
    return render(request, 'Dynamic.html', ctext)


@allowed_users(allowed_roles=['Admin', 'ECU Designer', 'Campaign Manager'])
def CheckContent(request):
    ctext = {'user': request.user.username, 'profile': request.user.groups.all()[0].name}
    return render(request, 'CheckContent.html', ctext)


@allowed_users(allowed_roles=['Admin', 'ECU Designer'])
def SetConfigRef1(request):
    ctext = {'user': request.user.username, 'profile': request.user.groups.all()[0].name}
    return render(request, 'SetConfigRef.html', ctext)


@allowed_users(allowed_roles=['Admin', 'ECU Designer'])
def SetReprogRef1(request):
    ctext = {'user': request.user.username, 'profile': request.user.groups.all()[0].name}
    return render(request, 'SetReprogRef.html', ctext)


@allowed_users(allowed_roles=['Admin', 'Campaign Manager'])
def CamapainDetailsView(request):
    ctext = {'user': request.user.username, 'profile': request.user.groups.all()[0].name}
    return render(request, 'CampaignDetails.html', ctext)


@allowed_users(allowed_roles=['Admin', 'Campaign Manager'])
def CamapaignDetails1View(request):
    ctext = {'user': request.user.username, 'profile': request.user.groups.all()[0].name}
    return render(request, 'CampainDetails1.html', ctext)


@allowed_users(allowed_roles=['Admin', 'ECU Designer', 'Campaign Manager'])
def FirstPageView(request):
    ctext = {'user': request.user.username, 'profile': request.user.groups.all()[0].name}
    return render(request, 'update.html', ctext)


@allowed_users(allowed_roles=['Admin', 'Campaign Manager'])
def VehicleManagementVinCheck(request):
    ctext = {'user': request.user.username, 'profile': request.user.groups.all()[0].name}
    return render(request, 'CheckVIN.html', ctext)


@allowed_users(allowed_roles=['Admin', 'Campaign Manager'])
def VehicleRegistration(request):
    ctext = {'user': request.user.username, 'profile': request.user.groups.all()[0].name}
    return render(request, 'VehicleRegistration.html', ctext)


@allowed_users(allowed_roles=['Admin', 'Campaign Manager'])
def CampaignCheck(request):
    ctext = {'user': request.user.username, 'profile': request.user.groups.all()[0].name}
    return render(request, 'CampaignCheck.html', ctext)


def FetchVinOnlyData(request):
    if request.method == 'POST':
        vin_number = request.POST['vin']
        url = "https://vda.azurewebsites.net/api/onlyvin"
        payload = {'vin': vin_number}
        files = [
        ]
        headers = {}
        response = requests.request("POST", url, headers=headers, data=payload, files=files)
        return JsonResponse(response.json())


def FetchVinECUData(request):
    if request.method == 'POST':
        vin_number = request.POST['vin']
        Ecu = request.POST['ECU']
        url = "https://vda.azurewebsites.net/api/vinEcu"
        payload = {'vin': vin_number, 'EcuName': Ecu}
        files = [
        ]
        headers = {}
        response = requests.request("POST", url, headers=headers, data=payload, files=files)
        return JsonResponse(response.json())


class ExeFetchVinAPIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = ExeFetchVin(data=request.data)
        if serializer.is_valid():
            data = serializer.data
            vin_number = data['vin']
            url = "https://vda.azurewebsites.net/api/onlyvin"
            payload = {'vin': vin_number}
            files = [
            ]
            headers = {}
            response = requests.request("POST", url, headers=headers, data=payload, files=files)
            if response.status_code == 200:
                json_data = response.json()
                file_name = str(vin_number) + str(uuid.uuid4())
                file_name_fullPath = 'media/' + file_name
                vin_object = VinNumber()
                vin_object.vinNumber = vin_number
                with open(file_name_fullPath, 'w') as fo:
                    json.dump(json_data, fo)
                vin_object.vedFile = file_name
                vin_object.save()
                return Response(status=200)
            else:
                return Response(status=204)
        else:
            return Response(status=400)


def FetchAndCheckVinDetails(request):
    if request.method == 'POST':
        Final_dict = {}
        vin_number = request.POST['vin']
        mode = request.POST['mode']
        VinNumbers = VinNumber.objects.all().filter(vinNumber=vin_number)
        if not VinNumbers:
            Final_dict['status'] = "NO"
        else:
            Final_dict['status'] = "YES"
            for values in VinNumbers:
                vins = values.vinNumber
                twin = get_twin(vins)
                connection_state = twin.connection_state
                Final_dict['connection_state'] = connection_state
        if mode == "check":
            return JsonResponse(Final_dict)
        if mode == "search":
            if Final_dict['status'] == "YES":
                file = None
                for values in VinNumbers:
                    file = values.vedFile.path
                with open(file) as json_file:
                    data = json.load(json_file)
                return JsonResponse(data)
            else:
                return JsonResponse(Final_dict)


def FetchFilterCampaign(request):
    if request.method == 'POST':
        list_object = []
        Final_object_dict = {}
        camapignname = request.POST['cn']
        startdate = request.POST['sd']
        enddate = request.POST['ed']
        if camapignname != "":
            # by campaign name
            CampaignDetail_id_object = CampaignDetail.objects.all().filter(campaignName=camapignname)
            for values in CampaignDetail_id_object:
                list_object.append(values)
        elif startdate != "" and enddate != "":
            # by both
            startdate = (datetime.strptime(startdate, "%Y-%m-%d")).date()
            enddate = (datetime.strptime(enddate, "%Y-%m-%d")).date()
            CampaignDetail_id_object = CampaignDetail.objects.all()
            for values in CampaignDetail_id_object:
                print("startdate = {0} and campaignS_date = {1}".format(startdate, values.startdate))
                print("enddate = {0}   and campaignE_date = {1}".format(enddate, values.endDate))

                if values.startdate >= startdate and values.endDate <= enddate:
                    list_object.append(values)

        elif startdate != "" and enddate == "":
            # by start date
            startdate = (datetime.strptime(startdate, "%Y-%m-%d")).date()
            CampaignDetail_id_object = CampaignDetail.objects.all()
            for values in CampaignDetail_id_object:
                if values.startdate >= startdate:
                    list_object.append(values)
        else:
            # by end date
            enddate = (datetime.strptime(enddate, "%Y-%m-%d")).date()
            CampaignDetail_id_object = CampaignDetail.objects.all()
            for values in CampaignDetail_id_object:
                if values.endDate <= enddate:
                    list_object.append(values)
        count = 0
        for value in list_object:
            Final_dict = {}
            count = count + 1
            Final_dict['CN'] = value.campaignName
            Final_dict['CT'] = value.CampaignType
            Final_dict['SD'] = value.startdate
            Final_dict['ED'] = value.endDate
            list_of_all_scomoId = []
            list_of_all_ecuName = set()
            for s in value.scomoID.all():
                list_of_all_scomoId.append(s.scomoID)
                # ecuname.
                scomo_id_object = ScomoID.objects.all().filter(scomoID=s.scomoID)
                for values in scomo_id_object:
                    ecu_name_object = values.ecuName
                    list_of_all_ecuName.add(ecu_name_object.ecuName)
            Final_dict['SI'] = list_of_all_scomoId
            Final_dict['EN'] = list(list_of_all_ecuName)
            Final_object_dict[count] = Final_dict
        return JsonResponse(Final_object_dict)


def GetCampaignStatus(request):
    if request.method == 'POST':
        campaignName = request.POST['CampaignName']
        CampaignDetail_id_object = CampaignDetail.objects.all().filter(campaignName=campaignName)
        Final_dict = {}
        for value in CampaignDetail_id_object:
            for v in value.vinNumber.all():
                twin = get_twin(v.vinNumber)
                if twin.properties.reported['Campaign_name'] == campaignName:
                    Final_dict[str(v.vinNumber)] = twin.properties.reported['status']
            return JsonResponse(Final_dict)


def check_all_vin_status():
    all_vin = VinNumber.objects.all()
    vin_dict = {}
    i = 0
    for value in all_vin:
        vin_number_counter = "VinNumber"
        i = i + 1
        vin_number_counter = vin_number_counter + str(i)
        twin = get_twin(value["vinNumber"])
        connection_state = twin.connection_state
        vin_dict[vin_number_counter] = (value["vinNumber"], connection_state)
        return JsonResponse(vin_dict)









