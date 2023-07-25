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
    AMOUNT_CHOICES = (
        ('20', 'Gold: 20'),
        ('10', 'Silver: 10'),
        ('5', 'Bronze: 5'),
    )
    amount = forms.ChoiceField(choices=AMOUNT_CHOICES, required=True)
    currency = forms.CharField(max_length=3, required=True)
    card_number = forms.CharField(max_length=19, required=True)
    expiration_date = forms.CharField(max_length=5, required=True)
    cvc = forms.CharField(max_length=5, required=True)

    def clean_expiration_date(self):
        expiration_date = self.cleaned_data['expiration_date']
        if len(expiration_date) != 5 or not expiration_date[2] == '/':
            raise forms.ValidationError("Invalid card expiration date format. Please enter the date in the format MM/YY.")

        month_str, year_str = expiration_date.split('/')
        try:
            month = int(month_str)
            year = int(year_str)
        except ValueError:
            raise forms.ValidationError("Invalid card expiration date. Please enter a valid date in the format MM/YY.")

        if not (1 <= month <= 12) or not (23 <= year <= 30):
            raise forms.ValidationError("Invalid card expiration date. Please enter a valid date in the format MM/YY.")

        return expiration_date

    def clean_card_number(self):
        card_number = self.cleaned_data['card_number']
        # Remove any spaces or hyphens from the card number
        card_number = card_number.replace(" ", "").replace("-", "")
        # Check if the card number contains only digits
        if not card_number.isdigit():
            raise forms.ValidationError("Invalid card number. Card number should contain only digits.")
        # Check the card number length (commonly 13 to 19 digits)
        if len(card_number) not in range(13, 20):
            raise forms.ValidationError("Invalid card number length. Card number should be between 13 and 19 digits.")

        return card_number

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