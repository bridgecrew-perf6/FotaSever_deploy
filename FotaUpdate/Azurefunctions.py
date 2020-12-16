import os
import sys
from time import sleep
from azure.iot.hub import IoTHubRegistryManager
from azure.iot.hub.models import Twin, TwinProperties, QuerySpecification, QueryResult
from azure.storage.blob import BlobClient
from django.conf import settings
import json

IOTHUB_CONNECTION_STRING = "HostName=fotaiothub.azure-devices.net;SharedAccessKeyName=iothubowner;SharedAccessKey=cBHlzfMi1kW35vePPexsv9mZ7wW02owBGfxTuPc/KAs="


def get_registry_manager():
    return IoTHubRegistryManager(IOTHUB_CONNECTION_STRING)


def get_list_of_all_devices():
    iothub_registry_manager = get_registry_manager()
    query_spec = QuerySpecification(query="SELECT deviceId FROM devices")
    query_result = iothub_registry_manager.query_iot_hub(query_spec, None, 100)
    list_devices_in_iot_hub = [twin.device_id for twin in query_result.items]
    return list_devices_in_iot_hub


# this function takes device id
def get_current_version(DEVICE_ID):
    try:
        iothub_registry_manager = get_registry_manager()
        twin = iothub_registry_manager.get_twin(DEVICE_ID)
        return (twin.properties.reported["firmware"]['currentFwVersion'],
                twin.properties.reported["firmware"]['priviousFwVersion'])
    except:
        print("something went wrong")


# update single device
def update_desired_property_and_file(DEVICE_ID, version, file_name):
    try:
        iothub_registry_manager = get_registry_manager()
        twin = iothub_registry_manager.get_twin(DEVICE_ID)
        twin_patch = Twin(properties=TwinProperties(desired={'fwVersion': version, 'fwPackageURI': file_name}))
        iothub_registry_manager.update_twin(DEVICE_ID, twin_patch, twin.etag)
    except:
        print("something went wrong")


# update multiple device property on device twin
def update_multiple_device(DEVICE_ID_LIST, version, file_name):
    try:
        iothub_registry_manager = get_registry_manager()
        for device_name in DEVICE_ID_LIST:
            twin = iothub_registry_manager.get_twin(device_name)
            twin_patch = Twin(properties=TwinProperties(desired={'fwVersion': version, 'fwPackageURI': file_name}))
            iothub_registry_manager.update_twin(device_name, twin_patch, twin.etag)
    except:
        print("something went wrong")


def upload_file_on_cloud(file_name):
    try:
        blob = BlobClient.from_connection_string(
            conn_str="DefaultEndpointsProtocol=https;AccountName=fotastorage1;AccountKey=ZH4xN/rJcvButa2oTELpASSq2Ag2mMDQLzWgqz6+g6nvuyY1Hs1csGUUzzquQaIS8FG7OMLzKU97r7PYAX7s+g==;EndpointSuffix=core.windows.net",
            container_name="fotacontainer",
            blob_name=file_name)
        with open(os.path.join(settings.MEDIA_ROOT, file_name), "rb") as data:
            blob.upload_blob(data)
    except:
        print("something went wrong when uploading file")


def update_twin(data_structure, vin_list, Campaign_name):
    iothub_registry_manager = get_registry_manager()
    for i in vin_list:
        twin = iothub_registry_manager.get_twin(str(i))
        x = {
            'Campaign_name': Campaign_name,
            'eculist': data_structure
        }
        twin_patch = Twin(properties=TwinProperties(desired=x))
        iothub_registry_manager.update_twin(str(i), twin_patch, twin.etag)


def get_twin(device_id):
    try:
        iothub_registry_manager = get_registry_manager()
        twin = iothub_registry_manager.get_twin(device_id)
        return twin
    except:
        print("something went wrong")


def get_reported_property(twin, ecu_name, field):
    try:
        return twin.properties.reported['eculist'][ecu_name][field]
    except:
        print("Something went wrong!")


def get_reported_status(twin):
    try:
        return twin.properties.reported['status']
    except:
        print("Something went wrong!")
