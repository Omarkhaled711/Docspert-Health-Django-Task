from django.urls import path
from .views import AccountListView, AccountDetailView, TransferFundsView, ImportAccountsView

urlpatterns = [
    path('', AccountListView.as_view(), name='account_list_api'),
    path('<uuid:account_id>/',
         AccountDetailView.as_view(), name='account_detail_api'),
    path('transfer/', TransferFundsView.as_view(), name='transfer_funds_api'),
    path('import/', ImportAccountsView.as_view(), name='import_accounts_api'),
]
