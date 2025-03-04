from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _

class UserManager(BaseUserManager):
    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', 'superadmin')
        
        return self._create_user(email, password, **extra_fields)

class Tenant(models.Model):
    name = models.CharField(max_length=255)
    subdomain = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('superadmin', 'Super Admin'),
        ('school_admin', 'School Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    )
    
    username = None
    email = models.EmailField(_('email address'), unique=True)
    user_type = models.CharField(max_length=15, choices=USER_TYPE_CHOICES, default='school_admin')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True, related_name='users')
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = UserManager()
    
    def __str__(self):
        return self.email


class School(models.Model):
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name='school')
    name = models.CharField(max_length=255)
    address = models.TextField()
    contact_number = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Custom template fields
    custom_html = models.FileField(upload_to='templates/schools/', blank=True, null=True)
    custom_css = models.FileField(upload_to='static/css/schools/', blank=True, null=True)
    custom_js = models.FileField(upload_to='static/js/schools/', blank=True, null=True)
    bootstrap_theme = models.CharField(max_length=255, blank=True, null=True, help_text="URL to a custom Bootstrap theme")

    def __str__(self):
        return self.name
class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    employee_id = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)
    qualification = models.CharField(max_length=255)
    date_of_joining = models.DateField()
    
    def __str__(self):
        return f"{self.user.email} - {self.employee_id}"

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.CharField(max_length=20, unique=True)
    grade = models.CharField(max_length=20)
    section = models.CharField(max_length=10)
    date_of_birth = models.DateField()
    guardian_name = models.CharField(max_length=255)
    guardian_contact = models.CharField(max_length=20)
    
    def __str__(self):
        return f"{self.user.email} - {self.student_id}"

# 2. Let's add Course and Class models
class Course(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='courses')
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=20)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class Class(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='classes')
    name = models.CharField(max_length=100)
    grade = models.CharField(max_length=20)
    section = models.CharField(max_length=10)
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='classes_taught')
    students = models.ManyToManyField(User, related_name='enrolled_classes', blank=True)
    courses = models.ManyToManyField(Course, related_name='classes', blank=True)
    
    def __str__(self):
        return f"{self.grade} - {self.section} - {self.name}"

# 3. Let's add forms for teacher and student creation
# forms.py (additional forms)
