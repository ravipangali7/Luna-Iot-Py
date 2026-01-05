"""
Phone Book URLs
URL patterns for phone book management endpoints
"""
from django.urls import path
from phone_call.views import phone_book_views, phone_book_number_views

urlpatterns = [
    # Phone Books
    path('phone-books/', phone_book_views.get_all_phone_books, name='get_all_phone_books'),
    path('phone-books/create', phone_book_views.create_phone_book, name='create_phone_book'),
    path('phone-books/user/<int:user_id>/', phone_book_views.get_phone_books_by_user, name='get_phone_books_by_user'),
    path('phone-books/institute/<int:institute_id>/', phone_book_views.get_phone_books_by_institute, name='get_phone_books_by_institute'),
    path('phone-books/<int:phone_book_id>/', phone_book_views.get_phone_book_by_id, name='get_phone_book_by_id'),
    path('phone-books/<int:phone_book_id>/update', phone_book_views.update_phone_book, name='update_phone_book'),
    path('phone-books/<int:phone_book_id>/delete', phone_book_views.delete_phone_book, name='delete_phone_book'),
    
    # Phone Book Numbers
    path('phone-books/<int:phone_book_id>/numbers/', phone_book_number_views.get_phone_book_numbers, name='get_phone_book_numbers'),
    path('phone-books/<int:phone_book_id>/numbers/create', phone_book_number_views.create_phone_book_number, name='create_phone_book_number'),
    path('phone-books/<int:phone_book_id>/numbers/bulk/', phone_book_number_views.bulk_create_phone_book_numbers, name='bulk_create_phone_book_numbers'),
    path('phone-books/<int:phone_book_id>/numbers/upload-excel/', phone_book_number_views.upload_phone_book_numbers_excel, name='upload_phone_book_numbers_excel'),
    path('phone-books/<int:phone_book_id>/numbers/download-template/', phone_book_number_views.download_phone_book_template, name='download_phone_book_template'),
    path('phone-books/<int:phone_book_id>/numbers/<int:number_id>/', phone_book_number_views.get_phone_book_number_by_id, name='get_phone_book_number_by_id'),
    path('phone-books/<int:phone_book_id>/numbers/<int:number_id>/update', phone_book_number_views.update_phone_book_number, name='update_phone_book_number'),
    path('phone-books/<int:phone_book_id>/numbers/<int:number_id>/delete', phone_book_number_views.delete_phone_book_number, name='delete_phone_book_number'),
]
