import random

from django.contrib.auth import authenticate, login
from django.contrib import auth
from django.core.mail import send_mail, EmailMessage
from django.shortcuts import render, get_object_or_404, get_list_or_404, redirect

from WhiteboardApp.models import User, Instructor, Course, Membership, Payment, Student, Enrollment, Grade, Content, \
    Progress
from .forms import InstructorForm, CourseForm, MembershipForm, PaymentForm, StudentForm, \
    EnrollmentForm, GradeForm, SignUpForm, PaymentFormStripe, ContentForm, PhoneVerificationForm, ContactForm
import os
from django.contrib.auth.views import LoginView, LogoutView
from django.http import JsonResponse, BadHeaderError, HttpResponse
import datetime
from django.core.paginator import Paginator

import stripe
from django.conf import settings

from django.http import FileResponse
from cryptography.fernet import Fernet
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from twilio.rest import Client


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


@login_required(login_url="WhiteboardApp:login_post")
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


@login_required(login_url="WhiteboardApp:login_post")
def course_students_list_paginate(request, course_id):
    # Retrieve the Course object based on the course_id
    course = get_object_or_404(Course, id=course_id)
    # Retrieve all students enrolled in the course
    students = Student.objects.filter(courses_enrolled=course)
    paginator = Paginator(students, 5)  # Specify the number of courses to display per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'CourseTemplates/course_student_list.html', {'students': page_obj, 'course': course})


@login_required(login_url="WhiteboardApp:login_post")
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


@login_required(login_url="WhiteboardApp:login_post")
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
    student_enrolled_course_count = Enrollment.objects.filter(student_id=request.user.student.id).count()
    return render(request, 'MembershipTemplates/membership_detail.html', {'membership': membership, 'student_enrolled_course_count': student_enrolled_course_count})


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


@login_required(login_url="WhiteboardApp:login_post")
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


@login_required(login_url="WhiteboardApp:login_post")
def process_payment_stripe(request, pk):
    if request.method == 'POST':
        stripe.api_key = settings.STRIPE_SECRET_KEY
        form = PaymentFormStripe(request.POST)

        # amount = form.cleaned_data['amount']
        stripe_token = request.POST['stripeToken']
        #currency = form.cleaned_data['currency']
        #card_number = form.cleaned_data['card_number']  # amount = form.cleaned_data['amount']
        #expiration_date = form.cleaned_data['expiration_date']  # currency = form.cleaned_data['currency']
        #cvc = form.cleaned_data['cvc']  # card_number = form.cleaned_data['card_number']
        #date_values = expiration_date.split('/')  # expiration_date = form.cleaned_data['expiration_date']
        #month = date_values[0]  # cvc = form.cleaned_data['cvc']
        #year = date_values[1]  # date_values = expiration_date.split('/')
        try:  # month = date_values[0]
            # this one is only in use for real case payment	        # year = date_values[1]
            # Create a payment method using Stripe Elements	        try:
            # payment_method = stripe.PaymentMethod.create(	            # this one is only in use for real case payment
            #     type='card',	            # Create a payment method using Stripe Elements
            #     card={	            # payment_method = stripe.PaymentMethod.create(
            #         'number': '4242 4242 4242 4242 ',	            #     type='card',
            #         'exp_month': month,	            #     card={
            #         'exp_year': year,	            #         'number': '4242 4242 4242 4242 ',
            #         'cvc': cvc	            #         'exp_month': month,
            #     }	            #         'exp_year': year,
            # )	            #         'cvc': cvc

            #     }
            # Create a payment intent and confirm the payment	            # )
            membership = Membership.objects.get(id=pk)
            print(request.user.student.id)
            payment_intent = stripe.PaymentIntent.create(  # Create a payment intent and confirm the payment
                amount=int(membership.price),
                # Convert amount to cents	            membership = Membership.objects.get(id=pk)
                currency='cad',
                payment_method = "pm_card_mastercard",
                confirm = True
                # Handle successful payment
            )

            #student = form.cleaned_data['student']
            payment = Payment(student_id=request.user.student.id, amount=membership.price, currency='CAD', card_number='4444',
                              expiration_date='12/24', cvc='321')
            # student = form.cleaned_data['student']
            student = get_object_or_404(Student, user_id=request.user.id)
            student.membership_id = pk
            student.save()
            payment.save()

            # request.session['expiration_date'] = expiration_date
            return render(request, 'PaymentTemplates/payment_Success.html',
                          {'amount': membership.price, 'currency': 'CAD'})

        except stripe.error.CardError as e:
            error_message = e.error.message
            return render(request, 'PaymentTemplates/payment_Error.html', {'error_message': error_message})
    else:
        # student = Student.objects.select_related('user').get(user_id=request.user.id)
        # payment = Payment(student=student)
        form = PaymentFormStripe()
        # read card_number and expiration_date from session and send to from
        card_number = request.session.get('card_number')
        expiration_date = request.session.get('expiration_date')
        return render(request, 'PaymentTemplates/payment_create_stripe.html', {'form': form,
                                                                               'card_number': card_number,
                                                                               'expiration_date': expiration_date,
                                                                               'stripe_publishable_key': settings.STRIPE_PUBLIC_KEY})


# Student Views


def student_list(request):
    students = Student.objects.all()
    return render(request, 'StudentTemplates/student_list.html', {'students': students})


def student_detail(request, pk):
    student = get_object_or_404(Student, pk=pk)
    return render(request, 'StudentTemplates/student_detail.html', {'student': student})


@login_required(login_url="WhiteboardApp:login_post")
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


@login_required(login_url="WhiteboardApp:login_post")
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


@login_required(login_url="WhiteboardApp:login_post")
def enrollment_list_of_student(request, student_id):
    try:
        enrollments = get_list_or_404(Enrollment, student_id=student_id)
        paginator = Paginator(enrollments, 4)  # Specify the number of courses to display per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
    except:
        page_obj = None
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


@login_required(login_url="WhiteboardApp:login_post")
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

@login_required(login_url="WhiteboardApp:login_post")
def grade_list_of_course(request, course_id):
    grades = Grade.objects.filter(course_id=course_id)
    return render(request, 'GradeTemplates/Grade_list.html', {'grades': grades, 'course_id': course_id})


def grade_detail(request, pk):
    grade = get_object_or_404(Grade, pk=pk)
    return render(request, 'GradeTemplates/Grade_detail.html', {'grade': grade})


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


@login_required(login_url="WhiteboardApp:login_post")
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


@login_required(login_url="WhiteboardApp:login_post")
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


@login_required(login_url="WhiteboardApp:login_post")
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

    def form_invalid(self, form):
        # This method is called when the form is invalid (login fails)
        # You can add any custom logic here before rendering the template
        return self.render_to_response(self.get_context_data(form=form))

    # def form_valid(self, form):
    #     # Retrieve the username and password from the form
    #     username = form.cleaned_data.get('username')
    #     password = form.cleaned_data.get('password')
    #     # Encrypt the clear-text username and password(using sample key)
    #     key = b'nq_WGKCAXOc4ZL1hcd3R37aUKWyUwqAxVLA482NU1Og='
    #     fernet = Fernet(key)
    #
    #     user = auth.authenticate(self.request, username=username, password=password)
    #
    #     encrypted_username = fernet.encrypt(username.encode()).decode()
    #     encrypted_password = fernet.encrypt(password.encode()).decode()
    #     encrypted_user_id = fernet.encrypt(
    #         str(user.id).encode()).decode()  # Note: we convert the id to string before encoding
    #
    #     response = super().form_valid(form)  # Call the parent method to get the original response
    #
    #     response.set_cookie('username', encrypted_username, max_age=3600)  # Set username cookie with 1 hour expiration
    #     response.set_cookie('password', encrypted_password, max_age=3600)  # Set password cookie with 1 hour expiration
    #     response.set_cookie('user_id', encrypted_user_id, max_age=3600)
    #     return response


class CustomLogoutView(LogoutView):
    next_page = 'WhiteboardApp:main_banner'

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        response.delete_cookie('username')
        response.delete_cookie('password')
        response.delete_cookie('user_id')
        return response


def signup_post(request, userType):
    if userType == 1:
        page_title = 'Instructor Sign-Up'
    else:
        page_title = 'Student Sign-Up'

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
    return render(request, 'signup.html', {'form': form, 'pageTitle': page_title})


# Content Views

@login_required(login_url="WhiteboardApp:login_post")
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


@login_required(login_url="WhiteboardApp:login_post")
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


@login_required(login_url="WhiteboardApp:login_post")
def download_content(request, content_id):
    content = get_object_or_404(Content, pk=content_id)
    file_path = os.path.join(settings.MEDIA_ROOT, content.file.path)
    response = FileResponse(open(file_path, 'rb'), as_attachment=True)
    return response


@login_required(login_url="WhiteboardApp:login_post")
def content_complete_for_student(request, content_id, student_id):
    content = Content.objects.get(pk=content_id)
    student_content_progress = Progress(student_id=student_id, content_id=content_id, is_completed=True)
    student_content_progress.save()
    return redirect('WhiteboardApp:course-detail', pk=content.course.id)


@login_required(login_url="WhiteboardApp:login_post")
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


# -_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_- SMS verification -_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_- #
def send_sms_verification(phone_number, verification_code):
    # Your Twilio account SID and Auth Token
    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN

    client = Client(account_sid, auth_token)

    message = client.messages.create(
        from_=settings.TWILIO_FROM_NUMBER,  # your Twilio number
        body=f'Your verification code is {verification_code}',
        to=settings.TWILIO_TO_NUMBER
    )


def phone_verification(request):
    if request.method == 'POST':
        form = PhoneVerificationForm(request.POST)
        if form.is_valid():
            phone_number = form.cleaned_data.get('phone_number')
            # Generate a 6-digit verification code
            verification_code = str(random.randint(100000, 999999))
            # Send the verification code to the user's phone
            send_sms_verification(phone_number, verification_code)
            # Store the phone number and verification code in the session
            request.session['phone_number'] = phone_number
            request.session['verification_code'] = verification_code
            # Redirect to a page where the user can enter the verification code
            return redirect('WhiteboardApp:verify_phone_number')
    else:
        form = PhoneVerificationForm()
    return render(request, 'VerificationTemplates/verify_phone_number.html',
                  {'form': form, 'pageTitle': 'Phone Verification'})



def verify_phone_number(request):
    if request.method == 'POST':
        entered_code = request.POST.get('code')
        if entered_code == request.session.get('verification_code'):
            # Don't forget to delete the phone number and verification code from the session
            del request.session['phone_number']
            del request.session['verification_code']
            user_id = request.session['user_id']  # assuming the user id is stored in the session
            return redirect('student_update_by_userid', user_id=user_id)  # replace with actual URL name and argument
        else:
            # The verification code is incorrect, show an error
            return render(request, 'VerificationTemplates/verify_phone_number.html',
                          {'error': 'The entered code is incorrect.'})


    elif request.method == 'GET':
        # Retrieve the phone number from the GET parameters
        phone_number = request.GET.get('phone_number', '')
        if phone_number:
            # Generate a 6-digit verification code
            verification_code = str(random.randint(100000, 999999))
            # Send the verification code to the user's phone
            send_sms_verification(phone_number, verification_code)
            # Store the phone number and verification code in the session
            request.session['phone_number'] = phone_number
            request.session['verification_code'] = verification_code
            return render(request, 'StudentTemplates/student_update_by_userid.html', {'phone_number': phone_number})
        else:
            return render(request, 'VerificationTemplates/verify_phone_number.html',
                          {'error': 'No phone number provided.'})
    else:
        return render(request, 'VerificationTemplates/verify_phone_number.html')


# -_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_- Contact Us -_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_- #
@login_required(login_url="WhiteboardApp:login_post")
def contact_us(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():

            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            from_email = request.user.email

            try:
                email = EmailMessage(
                    subject,
                    message,
                    from_email,
                    [settings.EMAIL_HOST_USER],
                    reply_to=[from_email],
                )
                email.send()
            except BadHeaderError:
                return HttpResponse('Invalid header found.')
            # Show a message that the email has been sent successfully, and redirect to the Contact Us page
            messages.success(request, 'Your message has been sent successfully.')
            return redirect('WhiteboardApp:contact-us')

    else:
        form = ContactForm()
    return render(request, 'ContactUsTemplates/ContactUs.html', {'form': form})


# -_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_- About Us -_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_- #
@login_required(login_url="WhiteboardApp:login_post")
def about_us(request):
    return render(request, 'AboutUsTemplates/AboutUs.html')
