from django.http import JsonResponse
from django.shortcuts import render, redirect
from marketplace.models import Cart, Tax
from marketplace.context_processors import get_cart_amounts
from menu.models import FoodItem
from .forms import OrderForm
from .models import Order, OrderedFood
import simplejson as json
from .utils import generate_order_number
from accounts.utils import SendNotificationThread
from django.contrib.auth.decorators import login_required
# import razorpay
# from fudanywer.settings import RZP_KEY_ID, RZP_KEY_SECRET
from django.contrib.sites.shortcuts import get_current_site
from vendor.models import Vendor



# client = razorpay.Client(auth=(RZP_KEY_ID, RZP_KEY_SECRET))



@login_required(login_url='login')
def place_order(request):
    cart_items = Cart.objects.filter(user=request.user).order_by('created_at')
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('marketplace')

    vendors_ids = []
    for i in cart_items:
        if i.fooditem.vendor.id not in vendors_ids:
            vendors_ids.append(i.fooditem.vendor.id)
    
    # {"vendor_id":{"subtotal":{"tax_type": {"tax_percentage": "tax_amount"}}}}
    get_tax = Tax.objects.filter(is_active=True)
    subtotal = 0
    total_data = {}
    k = {}
    for i in cart_items:
        fooditem = FoodItem.objects.get(pk=i.fooditem.id, vendor_id__in=vendors_ids)
        v_id = fooditem.vendor.id
        if v_id in k:
            subtotal = k[v_id]
            subtotal += (fooditem.price * i.quantity)
            k[v_id] = subtotal
        else:
            subtotal = (fooditem.price * i.quantity)
            k[v_id] = subtotal
    
        # Calculate the tax_data
        tax_dict = {}
        for i in get_tax:
            tax_type = i.tax_type
            tax_percentage = i.tax_percentage
            tax_amount = round((tax_percentage * subtotal)/100, 2)
            tax_dict.update({tax_type: {str(tax_percentage) : str(tax_amount)}})
        # Construct total data
        total_data.update({fooditem.vendor.id: {str(subtotal): str(tax_dict)}})
    
    order_numbers = []
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            for key1, val1 in total_data.items():
                order = Order()
                order.first_name = form.cleaned_data['first_name']
                order.last_name = form.cleaned_data['last_name']
                order.phone = form.cleaned_data['phone']
                order.email = form.cleaned_data['email']
                order.address = form.cleaned_data['address']
                order.country = form.cleaned_data['country']
                order.state = form.cleaned_data['state']
                order.city = form.cleaned_data['city']
                order.pin_code = form.cleaned_data['pin_code']
                order.user = request.user
                tax = 0
                for key, val in val1.items():
                    subtotal = float(key)
                    order.tax_data = json.dumps(val)
                    val = val.replace("'", '"')
                    val = json.loads(val)
                    for i in val:
                        for j in val[i]:
                            tax += float(val[i][j])
                
                order.total = subtotal + tax
                order.total_tax = tax
                order.save() # order id/ pk is generated
                order.order_number = generate_order_number(order.id)
                order_numbers.append(generate_order_number(order.id))
                order.vendor = Vendor.objects.get(pk=key1)
                order.is_ordered = True
                order.save()
                # MOVE THE CART ITEMS TO ORDERED FOOD MODEL
                for item in cart_items:
                    if item.fooditem.vendor == order.vendor:
                        ordered_food = OrderedFood()
                        ordered_food.order = order
                        ordered_food.user = request.user
                        ordered_food.fooditem = item.fooditem
                        ordered_food.quantity = item.quantity
                        ordered_food.price = item.fooditem.price
                        ordered_food.amount = item.fooditem.price * item.quantity # total amount
                        ordered_food.save()
                # SEND ORDER RECEIVED EMAIL TO THE VENDOR
                mail_subject = 'You have received a new order.'
                mail_template = 'orders/new_order_received.html'
                to_email = []
                to_email.append(order.vendor.user.email)
                tx_dt = json.loads(order.tax_data)
                tx_dt = tx_dt.replace("'", '"')
                tax_data = json.loads(tx_dt)
                vendor_grand_total = order.total

                ordered_food = OrderedFood.objects.filter(order=order)

                
                context = {
                    'order': order,
                    'to_email': to_email,
                    'ordered_food_to_vendor': ordered_food,
                    'domain': get_current_site(request),
                    'vendor_subtotal': subtotal,
                    'tax_data': tax_data,
                    'vendor_grand_total': vendor_grand_total,
                    }
                # send_notification(mail_subject, mail_template, context)
                SendNotificationThread(mail_subject, mail_template, context).start()
            cart_items.delete() 
        else:
            print(form.errors)

    
    try:  
        grand_subtotal = 0
        ordered_foods = []
        tax_data = {}
        total_tax = 0
        for order_number in order_numbers:
            order = Order.objects.get(order_number=order_number, is_ordered=True)
            ordered_food = OrderedFood.objects.filter(order=order)
            ordered_foods.append(ordered_food)
            vendor_subtotal = 0
            for item in ordered_food:
                vendor_subtotal += (item.price * item.quantity)
                grand_subtotal += (item.price * item.quantity)
            if tax_data == {}:
                for i in get_tax:
                    tax_type = i.tax_type
                    tax_percentage = i.tax_percentage
                    tax_amount = round((float(tax_percentage) * float(vendor_subtotal))/100, 2)
                    total_tax = float(tax_amount) + float(total_tax)
                    tax_data.update({tax_type: {str(tax_percentage) : str(tax_amount)}})  
            else:
                for i in get_tax:
                    tax_type = i.tax_type
                    tax_percentage = i.tax_percentage
                    tax_amount = round((float(tax_percentage) * float(vendor_subtotal))/100, 2)
                    ex_tax = float(tax_data[tax_type][str(tax_percentage)])
                    ex_tax += float(tax_amount)
                    total_tax += float(tax_amount)
                    tax_data[tax_type][str(tax_percentage)] = str(ex_tax)
        total_amount = total_tax + grand_subtotal

        # SEND ORDER CONFIRMATION EMAIL TO THE CUSTOMER
        mail_subject = 'Thank you for ordering with us.'
        mail_template = 'orders/order_confirmation_email.html'

        context = {
            'user': request.user,
            'order': order,
            'to_email': order.email,
            'order_numbers': order_numbers,
            'ordered_foods': ordered_foods,
            'domain': get_current_site(request),
            'grand_subtotal': grand_subtotal,
            'tax_data': tax_data,
            'totals': total_amount,
        }
        # send_notification(mail_subject, mail_template, context)
        SendNotificationThread(mail_subject, mail_template, context).start()

        context = {
            'order': order,
            'order_numbers': order_numbers,
            'ordered_foods': ordered_foods,
            'grand_subtotal': grand_subtotal,
            'tax_data': tax_data,
            'totals': total_amount,
        }
        return render(request, 'orders/order_complete.html', context)
    except:
        return redirect('home')


def accept_order(request, order_number):
    if request.user.is_authenticated:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            try:
                order = Order.objects.get(order_number=order_number)
                order.status="Accepted"
                order.save()
                return JsonResponse({'status': 'Success', 'message': 'Accepted', 'new_status': 'Accepted'})
            except:
                return JsonResponse({'status': 'Failed', 'message': 'This order does not exist!'})
        else:
            return JsonResponse({'status': 'Failed', 'message': 'Invalid request!'})
    else:
        return JsonResponse({'status': 'login_required', 'message': 'Please login to continue'})



def reject_order(request, order_number):
    if request.user.is_authenticated:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            try:
                order = Order.objects.get(order_number=order_number)
                order.status="Rejected"
                order.save()
                return JsonResponse({'status': 'Success', 'message': 'Rejected', 'new_status': 'Rejected'})
            except:
                return JsonResponse({'status': 'Failed', 'message': 'This order does not exist!'})
        else:
            return JsonResponse({'status': 'Failed', 'message': 'Invalid request!'})
    else:
        return JsonResponse({'status': 'login_required', 'message': 'Please login to continue'})
        


def complete_order(request, order_number):
    if request.user.is_authenticated:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            try:
                order = Order.objects.get(order_number=order_number)
                order.status="Completed"
                order.save()
                return JsonResponse({'status': 'Success', 'message': 'Completed', 'new_status': 'Completed'})
            except:
                return JsonResponse({'status': 'Failed', 'message': 'This order does not exist!'})
        else:
            return JsonResponse({'status': 'Failed', 'message': 'Invalid request!'})
    else:
        return JsonResponse({'status': 'login_required', 'message': 'Please login to continue'})
        


def cancel_order(request, order_number):
    if request.user.is_authenticated:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            try:
                order = Order.objects.get(order_number=order_number)
                order.status="Cancelled"
                order.save()
                return JsonResponse({'status': 'Success', 'message': 'Cancelled', 'new_status': 'Cancelled'})
            except:
                return JsonResponse({'status': 'Failed', 'message': 'This order does not exist!'})
        else:
            return JsonResponse({'status': 'Failed', 'message': 'Invalid request!'})
    else:
        return JsonResponse({'status': 'login_required', 'message': 'Please login to continue'})
        




   