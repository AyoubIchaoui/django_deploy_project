# router.py
from django.db import connection

class TenantRouter:
    """
    A router to control database operations based on the tenant context
    """
    def db_for_read(self, model, **hints):
        # All read operations go to the default database
        return 'default'
    
    def db_for_write(self, model, **hints):
        # All write operations go to the default database
        return 'default'
    
    def allow_relation(self, obj1, obj2, **hints):
        # Allow relations between objects in the same tenant
        if hasattr(obj1, 'tenant') and hasattr(obj2, 'tenant'):
            return obj1.tenant == obj2.tenant
        return True
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # Allow migrations on the default database
        return True