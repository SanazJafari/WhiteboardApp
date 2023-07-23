from django.contrib import admin
from .models import Instructor, Course, Membership, Payment, Student, Enrollment, Grade, Content, Progress, Contributors

# Register your models here.
admin.site.register(Instructor)
admin.site.register(Course)
admin.site.register(Payment)
admin.site.register(Student)
admin.site.register(Enrollment)
admin.site.register(Grade)
admin.site.register(Membership)
admin.site.register(Content)
admin.site.register(Progress)
admin.site.register(Contributors)
