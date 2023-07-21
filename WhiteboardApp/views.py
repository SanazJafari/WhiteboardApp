from django.contrib.auth import authenticate, login
from django.shortcuts import render, get_object_or_404, get_list_or_404, redirect
from .models import User, Instructor, Course, Membership, Payment, Student, Enrollment, Grade, Content, \
    Progress
from .forms import InstructorForm, CourseForm, MembershipForm, PaymentForm, StudentForm, \
    EnrollmentForm, GradeForm, SignUpForm, PaymentFormStripe, ContentForm
import os
from django.contrib.auth.views import LoginView, LogoutView
from django.http import JsonResponse
import datetime
from django.core.paginator import Paginator

import stripe
from django.conf import settings

from django.http import FileResponse
from cryptography.fernet import Fernet


# Instructor Views


def instructor_list(request):
    instructors = Instructor.objects.all()
    return render(request, 'InstructorTemplates/instructor_list.html', {'instructors': instructors})


def instructor_detail(request, pk):
    instructor = get_object_or_404(Instructor, pk=pk)
    return render(request, 'InstructorTemplates/instructor_detail.html', {'instructor': instructor})


def instructor_detail_by_userid(request, userid):
    instructor = get_object_or_404(Instructor, user_id=userid)
    return render(request, 'InstructorTemplates/instructor_detail.html', {'instructor': instructor})


def instructor_create(request):
    if request.method == 'POST':
        form = InstructorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('WhiteboardApp:instructor-list')
    else:
        form = InstructorForm()
    return render(request, 'InstructorTemplates/instructor_create.html', {'form': form})


def instructor_update(request, pk):
    instructor = get_object_or_404(Instructor, pk=pk)
    if request.method == 'POST':
        form = InstructorForm(request.POST, instance=instructor)
        if form.is_valid():
            form.save()
            return redirect('WhiteboardApp:instructor-list')
    else:
        form = InstructorForm(instance=instructor)
    return render(request, 'InstructorTemplates/instructor_update.html', {'form': form})


def instructor_update_by_userid(request, userid):
    instructor = get_object_or_404(Instructor, user_id=userid)
    user = instructor.user
    if request.method == 'POST':
        form = InstructorForm(request.POST, request.FILES, instance=instructor)
        if form.is_valid():
            form.save()
            # Update first_name and last_name of the corresponding user
            user.first_name = request.POST.get('first_name', '')
            user.last_name = request.POST.get('last_name', '')
            user.save()
            return redirect('WhiteboardApp:instructor-update-by-userId', userid=userid)
    else:
        form = InstructorForm(instance=instructor)
        form.fields['user'].queryset = User.objects.filter(pk=user.id)
    return render(request, 'InstructorTemplates/instructor_update_by_userid.html',
                  {'form': form, 'first_name': user.first_name, 'last_name': user.last_name})


# Course Views


def course_list(request):
    courses = Course.objects.all()
    return render(request, 'CourseTemplates/course_list.html', {'courses': courses})


def course_list_paginate(request):
    courses = Course.objects.all().order_by('pk')

    paginator = Paginator(courses, 8)  # Specify the number of courses to display per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'CourseTemplates/course_list.html', {'courses': page_obj})


def course_students_list_paginate(request, course_id):
    # Retrieve the Course object based on the course_id
    course = get_object_or_404(Course, id=course_id)
    # Retrieve all students enrolled in the course
    students = Student.objects.filter(courses_enrolled=course)
    paginator = Paginator(students, 5)  # Specify the number of courses to display per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'CourseTemplates/course_student_list.html', {'students': page_obj, 'course': course})


def course_list_paginate_instructor(request, instructor_id):
    courses_of_instructor = Course.objects.filter(instructor_id=instructor_id).order_by('pk')

    paginator = Paginator(courses_of_instructor, 4)  # Specify the number of courses to display per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'CourseTemplates/course_List_of_instructor.html', {'courses': page_obj})


def course_detail(request, pk):
    course = get_object_or_404(Course, pk=pk)

    instructor = None
    student = None
    is_enrolled_course = False
    grade = None
    is_current_instructor_course = False
    student_completed_contents = None
    has_enrollment_permission = False

    if request.user.is_authenticated:
        instructor = Instructor.objects.filter(user_id=request.user.id).first()
        student = Student.objects.filter(user_id=request.user.id).first()

    if student:
        student_completed_contents = Progress.objects.filter(student_id=student.id).values_list('content_id', flat=True)
        student_enrolled_course_count = Enrollment.objects.filter(student_id=student.id).count()
        has_enrollment_permission = (student.membership.name == 'bronze' and student_enrolled_course_count < 5) or \
                                    (student.membership.name == 'silver' and student_enrolled_course_count < 10) or \
                                    (student.membership.name == 'gold' and student_enrolled_course_count < 20)
        if student.courses_enrolled.filter(pk=course.pk).exists():
            is_enrolled_course = True
            grade = Grade.objects.filter(course_id=course.id, student_id=student.id).first()

    if instructor:
        if course.instructor_id == instructor.id:
            is_current_instructor_course = True

    return render(request, 'CourseTemplates/course_detail.html', {'course': course,
                                                                  'is_enrolled_course': is_enrolled_course,
                                                                  'student': student,
                                                                  'grade': grade,
                                                                  'has_enrollment_permission': has_enrollment_permission,
                                                                  'is_current_instructor_course': is_current_instructor_course,
                                                                  'completed_contents': student_completed_contents})


def course_create(request):
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('WhiteboardApp:course-list-paginate')
    else:
        form = CourseForm()
    return render(request, 'CourseTemplates/course_create.html', {'form': form})


def course_update(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            return redirect('WhiteboardApp:course-list')
    else:
        form = CourseForm(instance=course)
    return render(request, 'CourseTemplates/course_update.html', {'form': form})


# Membership Views


def membership_list(request):
    memberships = Membership.objects.all()
    return render(request, 'MembershipTemplates/membership_list.html', {'memberships': memberships})


def membership_detail(request, pk):
    membership = get_object_or_404(Membership, pk=pk)
    return render(request, 'MembershipTemplates/membership_detail.html', {'membership': membership})


def membership_update(request, pk):
    membership = get_object_or_404(Membership, pk=pk)
    if request.method == 'POST':
        form = MembershipForm(request.POST, instance=membership)
        if form.is_valid():
            form.save()
            return redirect('WhiteboardApp:membership-list')
    else:
        form = MembershipForm(instance=membership)
    return render(request, 'MembershipTemplates/membership_update.html', {'form': form})


# Payment Views


def payment_list(request):
    payments = Payment.objects.all()
    return render(request, 'PaymentTemplates/payment_list.html', {'payments': payments})


def payment_list_of_student(request, student_id):
    payments = Payment.objects.filter(student_id=student_id)
    return render(request, 'PaymentTemplates/payment_list.html', {'payments': payments})


def payment_detail(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    return render(request, 'PaymentTemplates/payment_detail.html', {'payment': payment})


def payment_create(request):
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('WhiteboardApp:payment-list')
    else:
        form = PaymentForm()
    return render(request, 'PaymentTemplates/payment_create.html', {'form': form})


def payment_update(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    if request.method == 'POST':
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            form.save()
            return redirect('WhiteboardApp:payment-list')
    else:
        form = PaymentForm(instance=payment)
    return render(request, 'PaymentTemplates/payment_update.html', {'form': form})


def process_payment_stripe(request):
    if request.method == 'POST':
        stripe.api_key = settings.STRIPE_SECRET_KEY
        form = PaymentFormStripe(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            currency = form.cleaned_data['currency']
            card_number = form.cleaned_data['card_number']
            expiration_date = form.cleaned_data['expiration_date']
            cvc = form.cleaned_data['cvc']
            date_values = expiration_date.split('/')
            month = date_values[0]
            year = date_values[1]
            try:
                # Create a payment method using Stripe Elements
                # payment_method = stripe.PaymentMethod.create(
                #     type='card',
                #     card={
                #         'number': '4242 4242 4242 4242 ',
                #         'exp_month': month,
                #         'exp_year': year,
                #         'cvc': cvc
                #     }
                # )

                # Create a payment intent and confirm the payment
                payment_intent = stripe.PaymentIntent.create(
                    amount=int(amount * 100),  # Convert amount to cents
                    currency=currency,
                    # payment_method= payment_method.id,
                    payment_method="pm_card_mastercard",
                    confirm=True
                )

                # Handle successful payment
                student = form.cleaned_data['student']
                amount = form.cleaned_data['amount']
                currency = form.cleaned_data['currency']
                card_number = form.cleaned_data['card_number']
                expiration_date = form.cleaned_data['expiration_date']
                cvc = form.cleaned_data['cvc']
                payment = Payment(student_id=student.id, amount=amount, currency=currency,
                                  card_number=card_number, expiration_date=expiration_date, cvc=cvc)
                payment.save()
                return render(request, 'PaymentTemplates/payment_Success.html', {'amount': amount, 'currency': currency})

            except stripe.error.CardError as e:
                error_message = e.error.message
                return render(request, 'PaymentTemplates/payment_Error.html', {'error_message': error_message})
    else:
        student = Student.objects.select_related('user').get(user_id=request.user.id)
        payment = Payment(student=student)
        form = PaymentFormStripe(instance=payment)
    return render(request, 'PaymentTemplates/payment_create_stripe.html', {'form': form})


# Student Views


def student_list(request):
    students = Student.objects.all()
    return render(request, 'StudentTemplates/student_list.html', {'students': students})


def student_detail(request, pk):
    student = get_object_or_404(Student, pk=pk)
    return render(request, 'StudentTemplates/student_detail.html', {'student': student})


def student_detail_by_userid(request, userid):
    student = get_object_or_404(Student, user_id=userid)
    return render(request, 'StudentTemplates/student_detail.html', {'student': student})


def student_create(request):
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('WhiteboardApp:student-list')
    else:
        form = StudentForm()
    return render(request, 'StudentTemplates/student_create.html', {'form': form})


def student_update(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            return redirect('WhiteboardApp:student-detail', pk=pk)
    else:
        form = StudentForm(instance=student)
    return render(request, 'StudentTemplates/student_update.html', {'form': form})


def student_update_by_userid(request, userid):
    student = get_object_or_404(Student, user_id=userid)
    user = student.user  # Retrieve the related User object directly from the student instance
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            # Update first_name and last_name of the corresponding user
            user.first_name = request.POST.get('first_name', '')
            user.last_name = request.POST.get('last_name', '')
            user.save()
            return redirect('WhiteboardApp:student-update-by-userId', userid=userid)
    else:
        form = StudentForm(instance=student)
        form.fields['user'].queryset = User.objects.filter(pk=user.id)
    return render(request, 'StudentTemplates/student_update_by_userid.html',
                  {'form': form, 'first_name': user.first_name, 'last_name': user.last_name})


# Enrolment Views


def enrollment_list(request):
    enrollments = Enrollment.objects.all()
    return render(request, 'EnrolmentTemplates/Enrollment_list.html', {'enrollments': enrollments})


def enrollment_list_of_student(request, student_id):
    enrollments = get_list_or_404(Enrollment, student_id=student_id)

    paginator = Paginator(enrollments, 4)  # Specify the number of courses to display per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'EnrolmentTemplates/Enrolment_List_of_student.html', {'enrollments': page_obj})


def enrollment_detail(request, pk):
    enrollment = get_object_or_404(Enrollment, pk=pk)
    return render(request, 'EnrolmentTemplates/Enrollment_detail.html', {'enrollment': enrollment})


def enrollment_create(request):
    if request.method == 'POST':
        form = EnrollmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('WhiteboardApp:enrollment-list')
    else:
        form = EnrollmentForm()
    return render(request, 'EnrolmentTemplates/Enrollment_create.html', {'form': form})


def enrollment_update(request, pk):
    enrollment = get_object_or_404(Enrollment, pk=pk)
    if request.method == 'POST':
        form = EnrollmentForm(request.POST, instance=enrollment)
        if form.is_valid():
            form.save()
            return redirect('WhiteboardApp:enrollment-list')
    else:
        form = EnrollmentForm(instance=enrollment)
    return render(request, 'EnrolmentTemplates/Enrollment_update.html', {'form': form})


def enroll_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    user = get_object_or_404(Student, user_id=request.user.id)
    enrollment = Enrollment.objects.create(student=user, course=course, enrollment_date=datetime.datetime.now())
    # Return a JSON response with the enrollment result
    data = {
        'enrollment_id': enrollment.id,
        'result': 'Enrollment successful!',
    }
    return JsonResponse(data)


# Grade Views


# def grade_list(request):
#     grades = Grade.objects.all()
#     return render(request, 'GradeTemplates/Grade_list.html', {'grades': grades})
#

def grade_list_of_course(request, course_id):
    grades = Grade.objects.filter(course_id=course_id)
    return render(request, 'GradeTemplates/Grade_list.html', {'grades': grades, 'course_id': course_id})


def grade_detail(request, pk):
    grade = get_object_or_404(Grade, pk=pk)
    return render(request, 'GradeTemplates/Grade_detail.html', {'grade': grade})


# def grade_create(request):
#     if request.method == 'POST':
#         form = GradeForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect('WhiteboardApp:grade-list')
#     else:
#         form = GradeForm()
#     return render(request, 'GradeTemplates/Grade_create.html', {'form': form})


def grade_update(request, pk):
    grade = get_object_or_404(Grade, pk=pk)
    if request.method == 'POST':
        form = GradeForm(request.POST, instance=grade)
        if form.is_valid():
            form.save()
            return redirect('WhiteboardApp:grade_list_of_course', grade.course.id)
    else:
        form = GradeForm(instance=grade)
        course = Course.objects.filter(pk=grade.course_id)  # Fetch course
        student = Student.objects.filter(pk=grade.student_id)  # Fetch student
        form.fields['course'].queryset = course  # Set the queryset of the 'course' field in the form
        form.fields['student'].queryset = student  # Set the queryset of the 'student' field in the form
    return render(request, 'GradeTemplates/Grade_update.html', {'form': form, 'course_id': grade.course.id})


def grade_update_for_student_in_course(request, student_id, course_id):
    grade = Grade.objects.filter(student_id=student_id, course_id=course_id)
    if not grade:
        return redirect('WhiteboardApp:grade_create_for_student_in_course', student_id, course_id)

    if request.method == 'POST':
        grade = get_object_or_404(Grade, student_id=student_id, course_id=course_id)
        form = GradeForm(request.POST, instance=grade)
        if form.is_valid():
            form.save()
            return redirect('WhiteboardApp:grade_list_of_course', course_id)
    else:
        form = GradeForm()
        course = Course.objects.filter(pk=course_id)  # Fetch course
        student = Student.objects.filter(pk=student_id)  # Fetch student
        form.fields['course'].queryset = course  # Set the queryset of the 'course' field in the form
        form.fields['student'].queryset = student  # Set the queryset of the 'student' field in the form
    return render(request, 'GradeTemplates/Grade_update.html', {'form': form, 'course_id': course.first().id})


def grade_create_for_student_in_course(request, student_id, course_id):
    if request.method == 'POST':
        form = GradeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('WhiteboardApp:grade_list_of_course', course_id)
    else:
        form = GradeForm()
        course = Course.objects.filter(pk=course_id)  # Fetch course
        student = Student.objects.filter(pk=student_id)  # Fetch student
        form.fields['course'].queryset = course  # Set the queryset of the 'course' field in the form
        form.fields['student'].queryset = student  # Set the queryset of the 'student' field in the form
    return render(request, 'GradeTemplates/Grade_create.html', {'form': form, 'course_id': course.first().id})


def grade_create_in_course(request, course_id):
    if request.method == 'POST':
        form = GradeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('WhiteboardApp:grade_list_of_course', course_id)
    else:
        form = GradeForm()
        course = Course.objects.filter(pk=course_id).first()  # Fetch the first course object
        students = Student.objects.filter(courses_enrolled=course)  # Fetch students of the course
        form.fields['course'].queryset = Course.objects.filter(
            pk=course_id)  # Set the queryset of the 'course' field in the form
        form.fields['student'].queryset = students  # Set the queryset of the 'student' field in the form
    return render(request, 'GradeTemplates/Grade_create.html', {'form': form, 'course_id': course_id})


def main_banner(request):
    # check cookie to see whether user is already login or not
    encrypted_username = request.COOKIES.get('username')
    encrypted_password = request.COOKIES.get('password')

    if encrypted_username and encrypted_password:
        # Decrypt the encrypted username and password using the same key that we encrypt
        key = b'nq_WGKCAXOc4ZL1hcd3R37aUKWyUwqAxVLA482NU1Og='
        fernet = Fernet(key)
        username = fernet.decrypt(encrypted_username.encode()).decode()
        password = fernet.decrypt(encrypted_password.encode()).decode()

        # use the authenticate function from Django authentication framework to verify the credentials
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Log in the user
            login(request, user)

    instructor = ''
    student = ''
    if request.user.is_authenticated:
        instructor = Instructor.objects.filter(user_id=request.user.id)
        student = Student.objects.filter(user_id=request.user.id)

    # Get the filenames of all images in the "images/banner" folder
    image_path = os.path.join('static', 'image', 'banner')
    image_files = [f for f in os.listdir(image_path) if os.path.isfile(os.path.join(image_path, f))]
    context = {'images': image_files, 'instructor': instructor, 'student': student}

    return render(request, 'base.html', context)


class CustomLoginView(LoginView):
    template_name = 'login.html'

    def form_valid(self, form):
        # Retrieve the username and password from the form
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')

        # Encrypt the clear-text username and password(using sample key)
        key = b'nq_WGKCAXOc4ZL1hcd3R37aUKWyUwqAxVLA482NU1Og='
        fernet = Fernet(key)
        encrypted_username = fernet.encrypt(username.encode()).decode()
        encrypted_password = fernet.encrypt(password.encode()).decode()

        response = super().form_valid(form)  # Call the parent method to get the original response
        response.set_cookie('username', encrypted_username, max_age=3600)  # Set username cookie with 1 hour expiration
        response.set_cookie('password', encrypted_password, max_age=3600)  # Set password cookie with 1 hour expiration
        return response


class CustomLogoutView(LogoutView):
    next_page = 'WhiteboardApp:main_banner'

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        response.delete_cookie('username')
        response.delete_cookie('password')
        return response


def signup_post(request, userType):
    if userType == 1:
        pagetitle = 'Instructor Sign-Up'
    else:
        pagetitle = 'Student Sign-Up'

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()

            if userType == 1:
                instructor = Instructor(user_id=user.id)
                instructor.save()
            else:
                student = Student(user_id=user.id)
                student.save()
            return redirect('WhiteboardApp:login_post')  # Redirect to login page after successful sign-up
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form, 'pageTitle': pagetitle})


# Content Views


# def content_list(request):
#     contents = Content.objects.all()
#     return render(request, 'ContentTemplates/Content_list.html', {'contents': contents})


def content_list_for_instructor(request, instructor_id):
    contents = Content.objects.filter(course__instructor_id=instructor_id)
    return render(request, 'ContentTemplates/Content_list.html', {'contents': contents})


def content_detail(request, pk):
    content = get_object_or_404(Content, pk=pk)
    return render(request, 'ContentTemplates/Content_detail.html', {'content': content})


def content_create(request):
    if request.method == 'POST':
        form = ContentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('WhiteboardApp:content_list_for_instructor', instructor_id=request.user.instructor.id)
    else:
        form = ContentForm()
        courses = Course.objects.filter(instructor_id=request.user.instructor.id)  # Fetch instructor course list
        form.fields['course'].queryset = courses  # Set the queryset of the 'course' field in the form
    return render(request, 'ContentTemplates/Content_create.html', {'form': form})


def content_delete(request, pk):
    content = get_object_or_404(Content, pk=pk)
    if content:
        Content.delete(content)
    return redirect('WhiteboardApp:content_list_for_instructor', instructor_id=request.user.instructor.id)


def content_create_for_specific_course(request, course_id):
    if request.method == 'POST':
        form = ContentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('WhiteboardApp:content_list_for_instructor', instructor_id=request.user.instructor.id)
    else:
        form = ContentForm()
        courses = Course.objects.filter(pk=course_id)  # Fetch course
        form.fields['course'].queryset = courses  # Set the queryset of the 'course' field in the form
    return render(request, 'ContentTemplates/Content_create.html', {'form': form})


def content_update(request, pk):
    content = get_object_or_404(Content, pk=pk)
    if request.method == 'POST':
        form = ContentForm(request.POST, request.FILES, instance=content)
        if form.is_valid():
            form.save()
            return redirect('WhiteboardApp:content_list_for_instructor', instructor_id=request.user.instructor.id)
    else:
        form = ContentForm(instance=content)
        course = Course.objects.filter(pk=content.course_id)  # Fetch related course
        form.fields['course'].queryset = course  # Set the queryset of the 'course' field in the form
    return render(request, 'ContentTemplates/Content_update.html', {'form': form})


def download_content(request, content_id):
    content = get_object_or_404(Content, pk=content_id)
    file_path = os.path.join(settings.MEDIA_ROOT, content.file.path)
    response = FileResponse(open(file_path, 'rb'), as_attachment=True)
    return response


def content_complete_for_student(request, content_id, student_id):
    content = Content.objects.get(pk=content_id)
    student_content_progress = Progress(student_id=student_id, content_id=content_id, is_completed=True)
    student_content_progress.save()
    return redirect('WhiteboardApp:course-detail', pk=content.course.id)


def course_progress(request, course_id):
    course = Course.objects.get(id=course_id)
    enrollments = Enrollment.objects.filter(course=course)
    contents = course.content_set.all()
    progress_dict = {
        (progress.student_id, progress.content_id): progress
        for progress in Progress.objects.filter(content__in=contents)
    }

    context = {
        'course': course,
        'enrollments': enrollments,
        'contents': contents,
        'progress_dict': progress_dict,
    }

    return render(request, 'CourseTemplates/course_students_progress.html', context)