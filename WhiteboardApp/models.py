from bson.json_util import default
from django.db import models
from django.contrib.auth.models import User


class Instructor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='instructor')
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.CharField(max_length=255, blank=True)
    website = models.URLField(blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    expertise = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'WhiteboardApp_Instructor'
        verbose_name = 'Instructor'
        verbose_name_plural = 'Instructors'

    def __str__(self):
        return self.user.username


class Course(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    syllabus = models.FileField(upload_to='syllabus/', null=True, blank=True)
    prerequisites = models.ManyToManyField('self', blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    # a JSON field to store additional dynamic data for the course.
    additional_data = models.JSONField(blank=True, null=True)

    def __str__(self):
        return self.title


class Membership(models.Model):
    MEMBERSHIP_CHOICES = (
        ('no', 'No-Membership'),
        ('gold', 'Gold'),
        ('silver', 'Silver'),
        ('bronze', 'Bronze'),
    )

    name = models.CharField(max_length=100, choices=MEMBERSHIP_CHOICES)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    benefits = models.TextField()

    def __str__(self):
        return self.get_name_display()


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student')
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    bio = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.CharField(max_length=255, blank=True)
    website = models.URLField(blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    courses_enrolled = models.ManyToManyField(Course, through='Enrollment')
    membership = models.ForeignKey(Membership, on_delete=models.SET_NULL, null=True, default=0)
    # a JSON field to store additional dynamic data for the student.
    additional_data = models.JSONField(blank=True, null=True)
    # a field to store the verification code for the student when they want to sign up in the application.
    verification_code = models.CharField(max_length=6, blank=True, null=True)

    class Meta:
        db_table = 'WhiteboardApp_student'
        verbose_name = 'student'
        verbose_name_plural = 'students'

    def __str__(self):
        return self.user.username


class Payment(models.Model):
    CURRENCY_CHOICES = (
        ('USD', 'US Dollars'),
        ('CAD', 'Canadian Dollars'),
        ('EUR', 'Euros'),
        ('GBP', 'British Pounds'),
        ('JPY', 'Japanese Yen'),
        ('CHF', 'Swiss Francs'),
        ('AUD', 'Australian Dollars'),
        ('NZD', 'New Zealand Dollars'),
        ('BRL', 'Iranian Rial'),
        ('CNY', 'Chinese Yuan'),
    )

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    transaction_id = models.CharField(max_length=100)
    card_number = models.CharField(max_length=20, blank=True, null=True)
    expiration_date = models.CharField(max_length=8, blank=True, null=True)
    cvc = models.CharField(max_length=5, blank=True, null=True)

    def __str__(self):
        return f"{self.student.user.username} - {self.amount} {self.currency}"


class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enrollment_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.user.username} - {self.course.title}"


class Grade(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    grade = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"{self.student.user.username} - {self.course.title} - {self.grade}"


class Content(models.Model):
    content_type_choice = (
        ('PDF', 'PDF File'),
        ('Voice', 'Voice File'),
        ('Video', 'Video File'),
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=content_type_choice)
    file = models.FileField(upload_to='contents/', null=True, blank=True)

    def __str__(self):
        return self.title


class Progress(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    content = models.ForeignKey(Content, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)

    class Meta:
        db_table = 'WhiteboardApp_progress'
        verbose_name = 'progress'

    def __str__(self):
        return f"{self.student.user.username} - {self.content.course.title} -" \
               f" {self.content.title} - {self.is_completed}%"
