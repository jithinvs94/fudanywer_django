from django.contrib import admin
from vendor.models import Vendor, OpeningHour, Bill, Payment

# Register your models here.


class VendorAdmin(admin.ModelAdmin):
    list_display = ('user', 'vendor_name', 'is_approved', 'created_at')
    list_display_links = ('user', 'vendor_name')
    list_editable = ('is_approved',)

class OpeningHourAdmin(admin.ModelAdmin):
    list_display = ('vendor', 'day', 'from_hour', 'to_hour')


class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'transaction_id', 'payment_method', 'amount', 'status', 'created_at')


class BillAdmin(admin.ModelAdmin):
    list_display = ('bill_number', 'vendor', 'payment', 'payment_method', 'total_amount', 'is_payed', 'created_at', 'updated_at')


admin.site.register(Vendor, VendorAdmin)
admin.site.register(OpeningHour, OpeningHourAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Bill, BillAdmin)
