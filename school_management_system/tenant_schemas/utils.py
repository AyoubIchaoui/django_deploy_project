from django.db import connection
from schools.models import Tenant

def get_tenant_from_request(request):
    return getattr(request, 'tenant', None)

def get_current_tenant():
    return getattr(connection, 'tenant', None)