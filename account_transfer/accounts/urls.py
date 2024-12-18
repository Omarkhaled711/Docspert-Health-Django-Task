from django.urls import path
from . import views

urlpatterns = [
    path('', views.account_list, name='account_list'),
    path('import/', views.import_accounts, name='import_accounts'),
    path('<uuid:account_id>/',
         views.account_detail, name='account_detail'),
    path('transfer/', views.transfer_funds, name='transfer_funds'),
]
