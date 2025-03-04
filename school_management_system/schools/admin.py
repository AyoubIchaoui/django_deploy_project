from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, School, Tenant
from tenant_schemas.utils import get_current_tenant

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('email', 'first_name', 'last_name', 'user_type', 'tenant', 'is_staff')
    list_filter = ('user_type', 'tenant', 'is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Tenant info', {'fields': ('tenant',)}),
        ('Permissions', {'fields': ('user_type', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'tenant', 'user_type', 'is_staff', 'is_active')}
        ),
    )
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # If user is superadmin, show all users
        if request.user.is_superuser:
            return qs
        # Otherwise, show only users from their tenant
        tenant = get_current_tenant()
        if tenant:
            return qs.filter(tenant=tenant)
        return qs.none()
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'tenant':
            # If user is superadmin, show all tenants
            if not request.user.is_superuser:
                kwargs["queryset"] = Tenant.objects.filter(id=request.user.tenant_id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class SchoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'tenant', 'contact_number', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'tenant__name')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # If user is superadmin, show all schools
        if request.user.is_superuser:
            return qs
        # Otherwise, show only school from their tenant
        tenant = get_current_tenant()
        if tenant:
            return qs.filter(tenant=tenant)
        return qs.none()
    
    def has_change_permission(self, request, obj=None):
        if not obj:
            return True
        if request.user.is_superuser:
            return True
        return obj.tenant == request.user.tenant
    
    def has_delete_permission(self, request, obj=None):
        if not obj:
            return True
        if request.user.is_superuser:
            return True
        return False  # Don't allow school admins to delete schools

admin.site.register(User, CustomUserAdmin)
admin.site.register(School, SchoolAdmin)
admin.site.register(Tenant)