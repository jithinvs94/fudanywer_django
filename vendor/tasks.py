from celery import shared_task
from accounts.models import User
from vendor.models import Vendor, Bill
import datetime
from orders.models import Order
from django.db.models import Q
from orders.utils import generate_order_number
from dateutil.relativedelta import relativedelta


@shared_task(bind=True)
def vendor_bill(self):
    vendors = User.objects.filter(role=1)
    for vend in vendors:
        vendor = Vendor.objects.get(user=vend)
        orders = Order.objects.filter(vendor=vendor, is_ordered=True).order_by('-created_at')
        previous_date = datetime.datetime.now() - relativedelta(months=1)
        previous_month = previous_date.month
        # print(previous_month)
        current_month_orders = orders.filter(Q(status='Completed') | Q(status='Accepted'), vendor=vendor, created_at__month=previous_month)
        current_month_revenue = 0
        for i in current_month_orders:
            current_month_revenue += i.total
        current_month_bill = (2*current_month_revenue)/100
        bill = Bill()
        bill.vendor = vendor
        bill.total_amount = current_month_bill
        bill.save()
        bill.bill_number = generate_order_number(bill.id)
        bill.save()

    return "Done"