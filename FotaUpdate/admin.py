from django.contrib import admin
from .models import VinNumber, EcuName, ScomoID, ContentFile, CampaignDetail, dynamichmi, FwVersion, DiscardedVin


# Register your models here.
admin.site.site_header = "FOTA ADMINISTRATION"
admin.site.site_title = "fota"
admin.site.index_title = "Welcome to FOTA Administration Portal"


admin.site.register(VinNumber)

admin.site.register(EcuName)

admin.site.register(ScomoID)

admin.site.register(ContentFile)

admin.site.register(CampaignDetail)

admin.site.register(dynamichmi)

admin.site.register(FwVersion)

admin.site.register(DiscardedVin)

