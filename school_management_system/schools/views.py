# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.conf import settings
from django.http import HttpResponseForbidden,HttpResponse
from .models import School, User, Tenant,Course,Class
from tenant_schemas.utils import get_tenant_from_request
from .forms import SchoolCreationForm,TeacherCreationForm,StudentCreationForm
def is_superadmin(user):
    return user.user_type == 'superadmin' and user.tenant is None

def is_school_admin(user):
    return user.user_type == 'school_admin' and user.tenant is not None

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            # Check if trying to access tenant site as superadmin or vice versa
            tenant = get_tenant_from_request(request)
            if tenant and user.tenant != tenant and not user.is_superuser:
                messages.error(request, 'You do not have access to this school portal')
                return render(request, 'schools/login.html')
                
            login(request, user)
            
            # Redirect based on user type and tenant
            if user.user_type == 'superadmin':
                if tenant:
                    # Redirect to main domain if superadmin tries to log in to tenant
                    main_domain = settings.MAIN_DOMAIN
                    return redirect(f'http://{main_domain}/superadmin-dashboard/')
                return redirect('superadmin_dashboard')
            elif user.user_type == 'school_admin':
                if not tenant:
                    # Redirect to their tenant's domain
                    subdomain = user.tenant.subdomain
                    main_domain = settings.MAIN_DOMAIN.split(':', 1)[0]  # Remove port if any
                    if ':' in request.get_host():
                        port = request.get_host().split(':', 1)[1]
                        redirect_url = f'http://{subdomain}.{main_domain}:{port}/school-admin-dashboard/'
                    else:
                        redirect_url = f'http://{subdomain}.{main_domain}/school-admin-dashboard/'
                    return redirect(redirect_url)
                return redirect('school_admin_home')
        else:
            messages.error(request, 'Invalid email or password')
    
    return render(request, 'schools/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
@user_passes_test(is_superadmin)
def superadmin_dashboard(request):
    if get_tenant_from_request(request):
        return HttpResponseForbidden("Access Denied: Super admin dashboard not available on tenant domains")
    
    schools = School.objects.all()
    return render(request, 'schools/superadmin_dashboard.html', {'schools': schools})

@login_required
@user_passes_test(is_superadmin)
def create_school(request):
    if get_tenant_from_request(request):
        return HttpResponseForbidden("Access Denied: School creation not available on tenant domains")
    
    if request.method == 'POST':
        form = SchoolCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'School created successfully with admin account')
            return redirect('superadmin_dashboard')
    else:
        form = SchoolCreationForm()
    
    return render(request, 'schools/create_school.html', {'form': form})

@login_required
@user_passes_test(is_superadmin)
def school_list(request):
    if get_tenant_from_request(request):
        return HttpResponseForbidden("Access Denied: School list not available on tenant domains")
    
    schools = School.objects.all()
    return render(request, 'schools/school_list.html', {'schools': schools})

@login_required
@user_passes_test(is_school_admin)
def school_admin_dashboard(request):
    tenant = get_tenant_from_request(request)
    school = get_object_or_404(School, tenant=tenant)

    # Check if the school has a custom HTML template
    if school.custom_html:
        with open(school.custom_html.path, 'r') as file:
            custom_html_content = file.read()
        return HttpResponse(custom_html_content)
    # Ensure user belongs to this tenant
    if request.user.tenant != tenant:
        return HttpResponseForbidden("Access Denied: You don't have permission to access this school")
    
    school = get_object_or_404(School, tenant=tenant)
    
    # Get users for this tenant
    teachers = User.objects.filter(tenant=tenant, user_type='teacher')
    students = User.objects.filter(tenant=tenant, user_type='student')
    
    context = {
        'school': school,
        'teacher_count': teachers.count(),
        'student_count': students.count(),
    }
    
    return render(request, 'schools/school_admin_dashboard.html', context, {'school': school})
@login_required
@user_passes_test(is_school_admin)
def teacher_list(request):
    tenant = get_tenant_from_request(request)
    
    # Ensure user belongs to this tenant
    if request.user.tenant != tenant:
        return HttpResponseForbidden("Access Denied: You don't have permission to access this school")
    
    teachers = User.objects.filter(tenant=tenant, user_type='teacher')
    return render(request, 'schools/teacher_list.html', {'teachers': teachers})

@login_required
@user_passes_test(is_school_admin)
def add_teacher(request):
    tenant = get_tenant_from_request(request)
    
    # Ensure user belongs to this tenant
    if request.user.tenant != tenant:
        return HttpResponseForbidden("Access Denied: You don't have permission to access this school")
    
    if request.method == 'POST':
        form = TeacherCreationForm(request.POST)
        if form.is_valid():
            form.save(tenant=tenant)
            messages.success(request, 'Teacher created successfully')
            return redirect('teacher_list')
    else:
        form = TeacherCreationForm()
    
    return render(request, 'schools/add_teacher.html', {'form': form})

@login_required
@user_passes_test(is_school_admin)
def student_list(request):
    tenant = get_tenant_from_request(request)
    
    # Ensure user belongs to this tenant
    if request.user.tenant != tenant:
        return HttpResponseForbidden("Access Denied: You don't have permission to access this school")
    
    students = User.objects.filter(tenant=tenant, user_type='student')
    return render(request, 'schools/student_list.html', {'students': students})

@login_required
@user_passes_test(is_school_admin)
def add_student(request):
    tenant = get_tenant_from_request(request)
    
    # Ensure user belongs to this tenant
    if request.user.tenant != tenant:
        return HttpResponseForbidden("Access Denied: You don't have permission to access this school")
    
    if request.method == 'POST':
        form = StudentCreationForm(tenant=tenant, data=request.POST)
        if form.is_valid():
            form.save(tenant=tenant)
            messages.success(request, 'Student created successfully')
            return redirect('student_list')
    else:
        form = StudentCreationForm(tenant=tenant)
    
    return render(request, 'schools/add_student.html', {'form': form})

# 5. Let's add class management views
@login_required
@user_passes_test(is_school_admin)
def class_list(request):
    tenant = get_tenant_from_request(request)
    
    # Ensure user belongs to this tenant
    if request.user.tenant != tenant:
        return HttpResponseForbidden("Access Denied: You don't have permission to access this school")
    
    classes = Class.objects.filter(tenant=tenant)
    return render(request, 'schools/class_list.html', {'classes': classes})

@login_required
@user_passes_test(is_school_admin)
def add_class(request):
    tenant = get_tenant_from_request(request)
    
    # Ensure user belongs to this tenant
    if request.user.tenant != tenant:
        return HttpResponseForbidden("Access Denied: You don't have permission to access this school")
    
    if request.method == 'POST':
        name = request.POST.get('name')
        grade = request.POST.get('grade')
        section = request.POST.get('section')
        teacher_id = request.POST.get('teacher')
        
        try:
            teacher = None
            if teacher_id:
                teacher = User.objects.get(id=teacher_id, tenant=tenant, user_type='teacher')
            
            new_class = Class.objects.create(
                tenant=tenant,
                name=name,
                grade=grade,
                section=section,
                teacher=teacher
            )
            
            messages.success(request, 'Class created successfully')
            return redirect('class_list')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    teachers = User.objects.filter(tenant=tenant, user_type='teacher')
    return render(request, 'schools/add_class.html', {'teachers': teachers})

# 6. Let's add course management views
@login_required
@user_passes_test(is_school_admin)
def course_list(request):
    tenant = get_tenant_from_request(request)
    
    # Ensure user belongs to this tenant
    if request.user.tenant != tenant:
        return HttpResponseForbidden("Access Denied: You don't have permission to access this school")
    
    courses = Course.objects.filter(tenant=tenant)
    return render(request, 'schools/course_list.html', {'courses': courses})

@login_required
@user_passes_test(is_school_admin)
def add_course(request):
    tenant = get_tenant_from_request(request)
    
    # Ensure user belongs to this tenant
    if request.user.tenant != tenant:
        return HttpResponseForbidden("Access Denied: You don't have permission to access this school")
    
    if request.method == 'POST':
        name = request.POST.get('name')
        code = request.POST.get('code')
        description = request.POST.get('description')
        
        try:
            Course.objects.create(
                tenant=tenant,
                name=name,
                code=code,
                description=description
            )
            
            messages.success(request, 'Course created successfully')
            return redirect('course_list')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    return render(request, 'schools/add_course.html')

# 7. Let's update the school_admin_dashboard view to include all data
@login_required
@user_passes_test(is_school_admin)
def school_admin_dashboard(request):
    tenant = get_tenant_from_request(request)
    
    # Ensure user belongs to this tenant
    if request.user.tenant != tenant:
        return HttpResponseForbidden("Access Denied: You don't have permission to access this school")
    
    school = get_object_or_404(School, tenant=tenant)
    
    # Get counts for dashboard
    teachers = User.objects.filter(tenant=tenant, user_type='teacher')
    students = User.objects.filter(tenant=tenant, user_type='student')
    classes = Class.objects.filter(tenant=tenant)
    courses = Course.objects.filter(tenant=tenant)
    
    context = {
        'school': school,
        'teacher_count': teachers.count(),
        'student_count': students.count(),
        'class_count': classes.count(),
        'course_count': courses.count(),
    }
    
    return render(request, 'schools/school_admin_dashboard.html', context)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import SchoolTemplateForm
from .models import School

def is_superadmin(user):
    return user.user_type == 'superadmin' and user.tenant is None

@login_required
@user_passes_test(is_superadmin)
def manage_school_templates(request, pk):
    school = get_object_or_404(School, pk=pk)

    if request.method == 'POST':
        form = SchoolTemplateForm(request.POST, request.FILES, instance=school)
        if form.is_valid():
            form.save()
            messages.success(request, f"Custom templates for {school.name} have been updated successfully.")
            return redirect('school_list')
    else:
        form = SchoolTemplateForm(instance=school)

    context = {
        'form': form,
        'school': school,
    }
    return render(request, 'schools/manage_templates.html', context)
from django.shortcuts import render, get_object_or_404
from .models import School

@login_required
def school_detail(request, pk):
    school = get_object_or_404(School, pk=pk)
    
    # Verify that the user has permission to view this school
    if not (request.user.user_type == 'superadmin' or 
            (request.user.user_type == 'school_admin' and request.user.tenant == school.tenant)):
        return HttpResponseForbidden("Access Denied: You don't have permission to access this school")
    
    context = {
        'school': school,
    }
    return render(request, 'schools/school_detail.html', context)
@login_required
@user_passes_test(lambda u: u.user_type == 'superadmin')
def superadmin_home(request):
    schools = School.objects.all()
    context = {
        'schools': schools,
    }
    return render(request, 'schools/superadmin_home.html', context)
@login_required
@user_passes_test(lambda u: u.user_type == 'school_admin')
def school_admin_home(request):
    tenant = get_tenant_from_request(request)
    if not tenant:
        return HttpResponseForbidden("Access Denied: Tenant not found.")

    school = get_object_or_404(School, tenant=tenant)
    teachers = User.objects.filter(tenant=tenant, user_type='teacher')
    students = User.objects.filter(tenant=tenant, user_type='student')

    context = {
        'school': school,
        'teachers': teachers,
        'students': students,
    }
    return render(request, 'schools/school_admin_home.html', context)
def home(request):
    return render(request, 'schools/index.html')
