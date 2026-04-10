from django.contrib import admin
from .models import Class, Subject, Student, SubjectCombination, Result, Notice, Parent, Attendance, ProgressReport

admin.site.register(Class)
admin.site.register(Subject)
admin.site.register(Student)
admin.site.register(SubjectCombination)
admin.site.register(Result)
admin.site.register(Notice)
admin.site.register(Parent)
admin.site.register(Attendance)
admin.site.register(ProgressReport)