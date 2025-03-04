from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('superadmin-dashboard/', views.superadmin_dashboard, name='superadmin_dashboard'),
    path('create-school/', views.create_school, name='create_school'),
    path('schools/', views.school_list, name='school_list'),
    path('school-admin-dashboard/', views.school_admin_dashboard, name='school_admin_dashboard'),
    path('teachers/', views.teacher_list, name='teacher_list'),
    path('teachers/add/', views.add_teacher, name='add_teacher'),
    path('students/', views.student_list, name='student_list'),
    path('students/add/', views.add_student, name='add_student'),
    path('classes/', views.class_list, name='class_list'),
    path('classes/add/', views.add_class, name='add_class'),
    path('courses/', views.course_list, name='course_list'),
    path('courses/add/', views.add_course, name='add_course'),
    path('schools/<int:pk>/manage-templates/', views.manage_school_templates, name='manage_school_templates'),
    path('schools/<int:pk>/', views.school_detail, name='school_detail'),
    path('superadmin-home', views.superadmin_home, name='superadmin_home'),
     path('', views.home, name='home'),
    path('school-admin-home/', views.school_admin_home, name='school_admin_home'),

]
