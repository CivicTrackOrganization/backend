from django.contrib import admin

from api.models import Comment, Report, ReportStatus, User, Vote

# Register your models here.

admin.site.register(User)
admin.site.register(Report)
admin.site.register(Vote)
admin.site.register(Comment)
admin.site.register(ReportStatus)