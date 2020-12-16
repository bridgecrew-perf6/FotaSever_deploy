from django.db import models
from django.db.models.signals import post_save
from datetime import date
from .Azurefunctions import *


# Create your models here.


class VinNumber(models.Model):
    vinNumber = models.CharField(max_length=100, primary_key=True)
    vedFile = models.FileField()


class EcuName(models.Model):
    ecuName = models.CharField(max_length=100, primary_key=True)


class ScomoID(models.Model):
    scomoID = models.CharField(max_length=100, primary_key=True)
    ecuName = models.ForeignKey(EcuName, on_delete=models.CASCADE)


class ContentFile(models.Model):
    FileName = models.CharField(max_length=200, primary_key=True)
    BrowsFile = models.FileField()
    FileType = models.CharField(max_length=200)
    Date = models.DateTimeField()
    ScomoID = models.ForeignKey(ScomoID, on_delete=models.CASCADE)


class FwVersion(models.Model):
    sourceVersion = models.CharField(max_length=100)
    TargetVersion = models.CharField(max_length=100)
    scomoID = models.ForeignKey(ScomoID, on_delete=models.CASCADE)


class CampaignDetail(models.Model):
    campaignName = models.CharField(max_length=300, primary_key=True)
    CampaignType = models.CharField(max_length=300)
    startdate = models.DateField()
    endDate = models.DateField()
    vinNumber = models.ManyToManyField(VinNumber)
    ecuNames = models.ManyToManyField(EcuName)
    scomoID = models.ManyToManyField(ScomoID)
    packageFile = models.ManyToManyField(ContentFile)
    fwversion = models.ManyToManyField(FwVersion)


class dynamichmi(models.Model):
    campaignName = models.ForeignKey(CampaignDetail, on_delete=models.CASCADE)
    xmlfile = models.FileField()


class DiscardedVin(models.Model):
    discardedVin_id = models.AutoField(primary_key=True)
    vin = models.CharField(max_length=300)
    campaignName = models.ForeignKey(CampaignDetail, on_delete=models.CASCADE)


def launchCampaign1(CampaignDetail_id_object, vin_number_list):
    dataStructureDict = {}
    Final_dict = {}
    ecu_mapping = {'IVI': 'RDO', 'METER': 'TDB', 'HUD': 'HMD', 'IVC': 'TCU', 'ADAS': 'DAS'}
    for value in CampaignDetail_id_object:
        startDate = value.startdate
        end_date = value.endDate
        vinNumber_twinList = []
        for vin in vin_number_list:
            vinNumber_twinList.append(get_twin(vin))
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
            temp[scomo_name_fileref] = file_name
            ecu_name = ecu_mapping[ecu_name_without_map]
            dataStructureDict[ecu_name] = temp

            for k in vinNumber_twinList:
                source_version_fromDevice = get_reported_property(k, ecu_name, s.scomoID_name)
                if source_version != source_version_fromDevice:
                    flag = 1
                    scomo_set.add(s.scomoID_name)

        if flag == 0:
            update_twin(dataStructureDict, vin_number_list)
            return True
        if flag == 1:
            return False


# signal function
def save_post(sender, instance, **kwargs):
    vin_number = instance.vinNumber
    DiscardedVinObjects = DiscardedVin.objects.filter(vin=vin_number)
    vin_list = [vin_number]
    if DiscardedVinObjects:
        for value in DiscardedVinObjects:
            startdate = value.campaignName.startdate
            enddate = value.campaignName.endDate
            if startdate <= date.today() <= enddate:
                list_obj = [value.campaignName]
                if launchCampaign1(list_obj, vin_list):
                    vin_number_object = VinNumber.objects.all().filter(vinNumber=vin_number)
                    for vin_object in vin_number_object:
                        value.campaignName.vinNumber.add(vin_object)
                    DiscardedVinObjects.delete()


# signals
post_save.connect(save_post, sender=VinNumber)
