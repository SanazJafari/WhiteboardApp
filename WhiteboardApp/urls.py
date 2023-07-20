from django.urls import path
from .views import CustomLoginView, CustomLogoutView
from . import views

app_name = 'WhiteboardApp'

urlpatterns = [
    # mainPage Urls
    path('', views.main_banner, name='main_banner'),

    #  Login and Logout Url
    # path('login/', views.login_post, name='login_post'),
    path('login/', CustomLoginView.as_view(), name='login_post'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),

    #  Signup
    path('signup/<int:userType>', views.signup_post, name='signup'),
    # path('signup/<int:userType>', views.signup_post, name='signup_Instructor'),
    # path('signup/<int:userType>', views.signup_post, name='signup_Student'),

    # Instructor Urls
    path('instructors/', views.instructor_list, name='instructor-list'),
    path('instructors/<int:pk>/', views.instructor_detail, name='instructor-detail'),
    path('instructorsByUserId/<int:userid>/', views.instructor_detail_by_userid, name='instructor-detail-by-userId'),
    path('instructors/create/', views.instructor_create, name='instructor-create'),
    path('instructors/<int:pk>/update/', views.instructor_update, name='instructor-update'),
    path('instructorsByUserId/<int:userid>/update/', views.instructor_update_by_userid,
         name='instructor-update-by-userId'),

    # Course Urls
    path('courses/', views.course_list, name='course-list'),
    path('courses/<int:pk>/', views.course_detail, name='course-detail'),
    path('courses/create/', views.course_create, name='course-create'),
    path('courses/<int:pk>/update/', views.course_update, name='course-update'),
    path('coursesPaginate/', views.course_list_paginate, name='course-list-paginate'),
    path('coursesPaginateInstructor/<int:instructor_id>', views.course_list_paginate_instructor,
         name='course-list-paginate_instructor'),
    path('course_students_pagination/<int:course_id>', views.course_students_list_paginate,
         name='course_student_list_pagination'),

    # Memberships Urls
    path('memberships/', views.membership_list, name='membership-list'),
    path('memberships/<int:pk>/', views.membership_detail, name='membership-detail'),
    path('memberships/<int:pk>/update/', views.membership_update, name='membership-update'),

    # Payment Urls
    path('payments/', views.payment_list, name='payment-list'),
    path('payments/<int:pk>/', views.payment_detail, name='payment-detail'),
    path('payments/create/', views.payment_create, name='payment-create'),
    path('payments/<int:pk>/update/', views.payment_update, name='payment-update'),
    path('paymentStripe/', views.process_payment_stripe, name='process_payment_stripe'),
    path('payments/<int:student_id>', views.payment_list_of_student, name='payment_list_of_student'),

    # Student Urls
    path('students/', views.student_list, name='student-list'),
    path('students/create/', views.student_create, name='student-create'),
    path('students/<int:pk>/', views.student_detail, name='student-detail'),
    # path('studentsByUserId/<int:userid>/', views.student_detail_by_userid, name='student-detail-by-userId'),
    path('students/<int:pk>/update/', views.student_update, name='student-update'),
    path('studentsByUserId/<int:userid>/update/', views.student_update_by_userid, name='student-update-by-userId'),

    # Enrolment Urls
    path('enrollments/', views.enrollment_list, name='enrollment-list'),
    path('enrollments/<int:student_id>', views.enrollment_list_of_student, name='enrollment-list-of-student'),
    path('enrollments/<int:pk>/', views.enrollment_detail, name='enrollment-detail'),
    path('enrollments/create/', views.enrollment_create, name='enrollment-create'),
    path('enrollments/<int:pk>/update/', views.enrollment_update, name='enrollment-update'),
    path('enroll/<int:course_id>/', views.enroll_course, name='enroll-course'),

    # Grade Urls
    # path('grades/', views.grade_list, name='grade-list'),
    # path('grades/<int:pk>/', views.grade_detail, name='grade-detail'),
    # path('grades/create/', views.grade_create, name='grade-create'),
    path('grades/<int:pk>/update/', views.grade_update, name='grade-update'),
    path('grades/update/<int:student_id>/<int:course_id>', views.grade_update_for_student_in_course,
         name='grade_update_for_student_in_course'),
    path('grades/<int:course_id>/', views.grade_list_of_course, name='grade_list_of_course'),
    path('grades/create/<int:student_id>/<int:course_id>', views.grade_create_for_student_in_course,
         name='grade_create_for_student_in_course'),
    path('grades/create/<int:course_id>', views.grade_create_in_course, name='grade_create_in_course'),

    # Content Urls
    # path('contents/', views.content_list, name='content-list'),
    path('contents/<int:instructor_id>', views.content_list_for_instructor, name='content_list_for_instructor'),
    path('contents/<int:pk>/', views.content_detail, name='content-detail'),
    path('contents/create/', views.content_create, name='content-create'),
    path('contents/create/<int:course_id>', views.content_create_for_specific_course,
         name='content_create_for_specific_course'),
    path('contents/<int:pk>/update/', views.content_update, name='content-update'),
    path('contents/<int:pk>/delete/', views.content_delete, name='content-delete'),
    path('download/<int:content_id>/', views.download_content, name='download-content'),

    # StudentContentProgress Urls
    path('student_content_complete/<int:content_id>/<int:student_id>', views.content_complete_for_student,
         name='complete-content_for_student'),
    path('course/<int:course_id>/progress/', views.course_progress, name='course-progress'),

]
