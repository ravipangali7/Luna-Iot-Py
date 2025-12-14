"""
Authentication URL Configuration
Matches Node.js auth_routes.js endpoints exactly
"""
from django.urls import path
from core.views import auth_views

urlpatterns = [
    # Public routes (no authentication required)
    path('register/send-otp', auth_views.send_registration_otp, name='send_registration_otp'),
    path('register/verify-otp', auth_views.verify_otp_and_register, name='verify_otp_and_register'),
    path('register/resend-otp', auth_views.resend_otp, name='resend_otp'),
    path('login', auth_views.login, name='login'),
    
    # Forgot password routes
    path('forgot-password/send-otp', auth_views.send_forgot_password_otp, name='send_forgot_password_otp'),
    path('forgot-password/verify-otp', auth_views.verify_forgot_password_otp, name='verify_forgot_password_otp'),
    path('forgot-password/reset-password', auth_views.reset_password, name='reset_password'),
    
    # Biometric authentication route (public)
    path('biometric-login', auth_views.biometric_login, name='biometric_login'),
    
    # Public delete account route (no authentication required)
    path('delete-account-public', auth_views.delete_account_public, name='delete_account_public'),
    
    # Protected routes (authentication required)
    path('logout', auth_views.logout, name='logout'),
    path('me', auth_views.get_current_user, name='get_current_user'),
    path('update-profile', auth_views.update_profile, name='update_profile'),
    path('verify-password', auth_views.verify_password, name='verify_password'),
    path('delete-account', auth_views.delete_account, name='delete_account'),
    path('biometric-token', auth_views.update_biometric_token, name='update_biometric_token'),
    path('biometric-token', auth_views.remove_biometric_token, name='remove_biometric_token'),
]
