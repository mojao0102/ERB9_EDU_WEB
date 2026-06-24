from django.contrib import admin

# Register your models here.

class ModelAdminOverride(admin.ModelAdmin):

    readonly_fields = (
        'file_status', 
        'created_by', 
        'created_datetime', 
        'last_updated_by', 
        'last_updated_datetime'
    )

    def get_readonly_fields(self, request, obj=None):
        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        if not change:
            #create
            obj.created_by = request.user.username
            obj.last_updated_by = request.user.username
            obj.file_status = "created"
        else:
            #update
            obj.last_updated_by = request.user.username
            obj.file_status = "updated"
            
        #call admin's save function
        super().save_model(request, obj, form, change)