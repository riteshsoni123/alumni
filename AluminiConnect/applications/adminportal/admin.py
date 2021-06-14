from django.contrib import admin

from .models import EmailTemplate, BulkEmailHistory, SingleEmailHistory

# Register your models here.

admin.site.register(EmailTemplate)
admin.site.register(BulkEmailHistory)
admin.site.register(SingleEmailHistory)
