from django.urls import path, include

urlpatterns = [
    path('wallet/', include('finance.urls.wallet_urls')),
    path('transaction/', include('finance.urls.transaction_urls')),
    path('due-transaction/', include('finance.urls.due_transaction_urls')),
    path('payment/', include('finance.urls.payment_urls')),
]
