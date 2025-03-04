from django.conf import settings
from django.http import Http404
from django.db import connection
from schools.models import Tenant

class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(':')[0].lower()
        
        # Check if this is the main domain (used by superadmin)
        main_domain = settings.MAIN_DOMAIN
        if host == main_domain:
            request.tenant = None
            return self.get_response(request)
        
        # Check for subdomain
        subdomain = host.split('.')[0]
        if subdomain == 'www' or subdomain == main_domain:
            request.tenant = None
            return self.get_response(request)
        
        # Try to get tenant by subdomain
        try:
            tenant = Tenant.objects.get(subdomain=subdomain)
            request.tenant = tenant
        except Tenant.DoesNotExist:
            if settings.DEBUG:
                # For development, allow any subdomain
                request.tenant = None
            else:
                raise Http404("Tenant not found")
        
        return self.get_response(request)
