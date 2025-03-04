from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, School, Tenant, TeacherProfile, StudentProfile, Class

class SchoolAdminCreationForm(UserCreationForm):
    """
    Form to create a new School Admin user.
    """
    class Meta:
        model = User
        fields = ('email', 'password1', 'password2', 'first_name', 'last_name')

    def __init__(self, tenant=None, *args, **kwargs):
        self.tenant = tenant
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'school_admin'
        if self.tenant:
            user.tenant = self.tenant
        if commit:
            user.save()
        return user

class SchoolTemplateForm(forms.ModelForm):
    class Meta:
        model = School
        fields = ('custom_html', 'custom_css', 'custom_js', 'bootstrap_theme')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['custom_html'].required = False
        self.fields['custom_css'].required = False
        self.fields['custom_js'].required = False
        self.fields['bootstrap_theme'].required = False
        
class SchoolCreationForm(forms.ModelForm):
    """
    Form to create a new School with a Tenant.
    """
    subdomain = forms.CharField(
        max_length=100,
        required=True,
        help_text="This will be used for accessing the school portal (e.g., school.example.com)"
    )
    admin_email = forms.EmailField(required=True)
    admin_password = forms.CharField(widget=forms.PasswordInput(), required=True)

    class Meta:
        model = School
        fields = ('name', 'address', 'contact_number', 'subdomain', 'admin_email', 'admin_password')

    def clean_subdomain(self):
        subdomain = self.cleaned_data.get('subdomain')
        if Tenant.objects.filter(subdomain=subdomain).exists():
            raise forms.ValidationError("This subdomain is already taken.")
        return subdomain

    def clean_admin_email(self):
        email = self.cleaned_data.get('admin_email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already taken.")
        return email

    def save(self, commit=True):
        subdomain = self.cleaned_data.pop('subdomain')
        admin_email = self.cleaned_data.pop('admin_email')
        admin_password = self.cleaned_data.pop('admin_password')

        # Create tenant first
        tenant = Tenant.objects.create(
            name=self.cleaned_data['name'],
            subdomain=subdomain
        )

        # Create school with tenant
        school = School(
            tenant=tenant,
            **self.cleaned_data
        )
        if commit:
            school.save()

        # Create school admin user
        admin_user = User.objects.create_user(
            email=admin_email,
            password=admin_password,
            user_type='school_admin',
            tenant=tenant,
            is_staff=True  # Make them staff to access Django admin for their tenant
        )

        return school


class TeacherCreationForm(forms.ModelForm):
    """
    Form to create a new Teacher.
    """
    email = forms.EmailField(required=True)
    password = forms.CharField(widget=forms.PasswordInput(), required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = TeacherProfile
        fields = ('employee_id', 'department', 'designation', 'qualification', 'date_of_joining')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already taken.")
        return email

    def clean_employee_id(self):
        employee_id = self.cleaned_data.get('employee_id')
        if TeacherProfile.objects.filter(employee_id=employee_id).exists():
            raise forms.ValidationError("This employee ID is already taken.")
        return employee_id

    def save(self, tenant, commit=True):
        # Get user data
        email = self.cleaned_data.pop('email')
        password = self.cleaned_data.pop('password')
        first_name = self.cleaned_data.pop('first_name')
        last_name = self.cleaned_data.pop('last_name')

        # Create user
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            user_type='teacher',
            tenant=tenant
        )

        # Create teacher profile
        teacher_profile = TeacherProfile(
            user=user,
            **self.cleaned_data
        )
        if commit:
            teacher_profile.save()

        return teacher_profile


class StudentCreationForm(forms.ModelForm):
    """
    Form to create a new Student.
    """
    email = forms.EmailField(required=True)
    password = forms.CharField(widget=forms.PasswordInput(), required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    class_id = forms.ModelChoiceField(queryset=Class.objects.none(), required=False, label="Assign to Class")

    class Meta:
        model = StudentProfile
        fields = ('student_id', 'grade', 'section', 'date_of_birth', 'guardian_name', 'guardian_contact')

    def __init__(self, tenant=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['class_id'].queryset = Class.objects.filter(tenant=tenant)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already taken.")
        return email

    def clean_student_id(self):
        student_id = self.cleaned_data.get('student_id')
        if StudentProfile.objects.filter(student_id=student_id).exists():
            raise forms.ValidationError("This student ID is already taken.")
        return student_id

    def save(self, tenant, commit=True):
        # Get user data
        email = self.cleaned_data.pop('email')
        password = self.cleaned_data.pop('password')
        first_name = self.cleaned_data.pop('first_name')
        last_name = self.cleaned_data.pop('last_name')
        class_id = self.cleaned_data.pop('class_id', None)

        # Create user
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            user_type='student',
            tenant=tenant
        )

        # Create student profile
        student_profile = StudentProfile(
            user=user,
            **self.cleaned_data
        )
        if commit:
            student_profile.save()
            if class_id:
                class_id.students.add(user)

        return student_profile