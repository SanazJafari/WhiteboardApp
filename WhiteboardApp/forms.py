from django import forms
from .models import Instructor, Course, Membership, Payment, Student, Enrollment, Grade, User, Content
from django.contrib.auth.forms import UserCreationForm


class InstructorForm(forms.ModelForm):
    class Meta:
        model = Instructor
        fields = ['user', 'profile_picture', 'bio', 'date_of_birth', 'address', 'website',
                  'phone_number', 'expertise']


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'instructor', 'start_date', 'end_date', 'is_active', 'syllabus',
                  'prerequisites', 'avatar', 'additional_data']


class MembershipForm(forms.ModelForm):
    class Meta:
        model = Membership
        fields = ['name', 'description', 'price', 'benefits']


class PaymentFormStripe(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['student', 'amount', 'currency', 'card_number', 'expiration_date', 'cvc']


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ('user', 'profile_picture', 'bio', 'date_of_birth', 'address', 'website', 'phone_number',
                  'courses_enrolled', 'membership', 'additional_data')


class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ['student', 'course']


class GradeForm(forms.ModelForm):
    class Meta:
        model = Grade
        fields = ['student', 'course', 'grade']

# Signup form extendinding UserCreationForm class 
class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already in use!")
        return email
        
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match. Please try again.")
        
        return cleaned_data

    widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Enter your username'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Enter your email'}),
            'password1': forms.PasswordInput(attrs={'placeholder': 'Enter your password'}),
            'password2': forms.PasswordInput(attrs={'placeholder': 'Confirm your password'}),
        }

class ContentForm(forms.ModelForm):
    class Meta:
        model = Content
        fields = ['course', 'title', 'type', 'file']