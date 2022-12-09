from django.urls import path
from . import views

urlpatterns = [
    path('place_order/', views.place_order, name='place_order'),
    # path('payments/', views.payments, name='payments'),
    # path('order_complete/', views.order_complete, name='order_complete'),
    path('accept_order/<int:order_number>/', views.accept_order, name='accept_order'),
    path('reject_order/<int:order_number>/', views.reject_order, name='reject_order'),
    path('complete_order/<int:order_number>/', views.complete_order, name='complete_order'),
    path('cancel_order/<int:order_number>/', views.cancel_order, name='cancel_order'),
]