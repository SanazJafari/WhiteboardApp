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
    student = forms.ModelChoiceField(queryset=Student.objects.all(), widget=forms.Select(attrs={'class': 'form-select'}))
    course = forms.ModelChoiceField(queryset=Course.objects.all(), widget=forms.Select(attrs={'class': 'form-select'}))
    
    class Meta:
        model = Grade
        fields = ['student', 'course', 'grade']
        widgets = {
            'grade': forms.NumberInput(attrs={
                'min': 0, 'max': 100,
                'class': 'form-control',
                'placeholder': "Enter a grade between 0 and 100"
                })
        }


class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already in use!")
        return email

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'placeholder': 'Enter your username'})
        self.fields['email'].widget.attrs.update({'placeholder': 'Enter your email'})
        self.fields['password1'].widget.attrs.update({'placeholder': 'Enter your password'})
        self.fields['password2'].widget.attrs.update({'placeholder': 'Confirm your password'})


class ContentForm(forms.ModelForm):
    class Meta:
        model = Content
        fields = ['course', 'title', 'type', 'file']