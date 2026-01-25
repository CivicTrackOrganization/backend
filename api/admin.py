from django.contrib import admin

from api.models import Comment, Report, User, Vote

# Register your models here.

admin.site.register(User)
admin.site.register(Report)
admin.site.register(Vote)
admin.site.register(Comment)