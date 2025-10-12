from django.urls import path, include

urlpatterns = [
    path('wallet/', include('finance.urls.wallet_urls')),
    path('transaction/', include('finance.urls.transaction_urls')),
]
