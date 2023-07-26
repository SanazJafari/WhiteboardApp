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


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['student', 'amount', 'currency', 'transaction_id']


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


class PhoneVerificationForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['phone_number']
        widgets = {
            'phone_number': forms.TextInput(attrs={'placeholder': 'Enter your phone number'}),
        }


class ContactForm(forms.Form):
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    email = forms.EmailField(required=True)
    subject = forms.CharField(required=True)
    message = forms.CharField(widget=forms.Textarea, required=True)


class VerificationForm(forms.Form):
    verification_code = forms.CharField(max_length=6)
