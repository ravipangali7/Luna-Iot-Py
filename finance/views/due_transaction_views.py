"""
Due Transaction Views
Handles due transaction management endpoints with payment processing
"""
from django.http import JsonResponse
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator
from django.utils import timezone
from django.db import transaction as db_transaction
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from decimal import Decimal

from finance.models import DueTransaction, DueTransactionParticular, Wallet, Transaction
from core.models import User
from finance.serializers import (
    DueTransactionSerializer,
    DueTransactionCreateSerializer,
    DueTransactionUpdateSerializer,
    DueTransactionListSerializer,
    DueTransactionPaySerializer,
    DueTransactionParticularSerializer
)
from api_common.utils.response_utils import success_response, error_response
from api_common.constants.api_constants import SUCCESS_MESSAGES, ERROR_MESSAGES, HTTP_STATUS
from api_common.decorators.response_decorators import api_response
from api_common.decorators.auth_decorators import require_auth, require_super_admin


@api_view(['GET'])
@require_auth
@api_response
def get_all_due_transactions(request):
    """
    Get all due transactions with filtering and pagination
    Super Admin only
    """
    try:
        # Check if user is Super Admin
        if not request.user.groups.filter(name='Super Admin').exists():
            return error_response(
                message="Access denied. Super Admin role required.",
                status_code=HTTP_STATUS['FORBIDDEN']
            )
        
        # Get filter parameters
        search_query = request.GET.get('search', '')
        is_paid = request.GET.get('is_paid')
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        
        # Build queryset
        queryset = DueTransaction.objects.select_related('user').prefetch_related('particulars')
        
        # Apply filters
        if search_query:
            queryset = queryset.filter(
                Q(user__name__icontains=search_query) |
                Q(user__phone__icontains=search_query) |
                Q(id__icontains=search_query)
            )
        
        if is_paid is not None:
            is_paid_bool = is_paid.lower() == 'true'
            queryset = queryset.filter(is_paid=is_paid_bool)
        
        # Order by created_at descending
        queryset = queryset.order_by('-created_at')
        
        # Paginate
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        # Serialize
        serializer = DueTransactionListSerializer(page_obj.object_list, many=True)
        
        return success_response(
            data={
                'results': serializer.data,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_pages': paginator.num_pages,
                    'total_count': paginator.count,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous(),
                }
            },
            message=SUCCESS_MESSAGES['FETCHED']
        )
    
    except Exception as e:
        return error_response(
            message=f"Error fetching due transactions: {str(e)}",
            status_code=HTTP_STATUS['INTERNAL_SERVER_ERROR']
        )


@api_view(['GET'])
@require_auth
@api_response
def get_due_transaction_by_id(request, due_transaction_id):
    """
    Get due transaction by ID
    Super Admin or the user who owns the transaction
    """
    try:
        due_transaction = DueTransaction.objects.select_related('user').prefetch_related('particulars').get(id=due_transaction_id)
        
        # Check access
        is_super_admin = request.user.groups.filter(name='Super Admin').exists()
        is_owner = due_transaction.user.id == request.user.id
        
        if not (is_super_admin or is_owner):
            return error_response(
                message="Access denied. You can only view your own due transactions.",
                status_code=HTTP_STATUS['FORBIDDEN']
            )
        
        serializer = DueTransactionSerializer(due_transaction)
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES['FETCHED']
        )
    
    except DueTransaction.DoesNotExist:
        return error_response(
            message="Due transaction not found",
            status_code=HTTP_STATUS['NOT_FOUND']
        )
    except Exception as e:
        return error_response(
            message=f"Error fetching due transaction: {str(e)}",
            status_code=HTTP_STATUS['INTERNAL_SERVER_ERROR']
        )


@api_view(['GET'])
@require_auth
@api_response
def get_user_due_transactions(request, user_id):
    """
    Get all due transactions for a specific user
    Super Admin or the user themselves
    """
    try:
        # Check access
        is_super_admin = request.user.groups.filter(name='Super Admin').exists()
        is_owner = request.user.id == user_id
        
        if not (is_super_admin or is_owner):
            return error_response(
                message="Access denied. You can only view your own due transactions.",
                status_code=HTTP_STATUS['FORBIDDEN']
            )
        
        # Get filter parameters
        is_paid = request.GET.get('is_paid')
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        
        # Build queryset
        queryset = DueTransaction.objects.filter(user_id=user_id).select_related('user').prefetch_related('particulars')
        
        # Apply filters
        if is_paid is not None:
            is_paid_bool = is_paid.lower() == 'true'
            queryset = queryset.filter(is_paid=is_paid_bool)
        
        # Order by created_at descending
        queryset = queryset.order_by('-created_at')
        
        # Paginate
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        # Serialize
        serializer = DueTransactionListSerializer(page_obj.object_list, many=True)
        
        return success_response(
            data={
                'results': serializer.data,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_pages': paginator.num_pages,
                    'total_count': paginator.count,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous(),
                }
            },
            message=SUCCESS_MESSAGES['FETCHED']
        )
    
    except Exception as e:
        return error_response(
            message=f"Error fetching user due transactions: {str(e)}",
            status_code=HTTP_STATUS['INTERNAL_SERVER_ERROR']
        )


@api_view(['POST'])
@require_auth
@api_response
def pay_due_transaction_with_wallet(request, due_transaction_id):
    """
    Pay due transaction using wallet balance
    User can pay their own due transactions
    """
    try:
        due_transaction = DueTransaction.objects.select_related('user').get(id=due_transaction_id)
        
        # Check if user owns this transaction
        if due_transaction.user.id != request.user.id:
            return error_response(
                message="Access denied. You can only pay your own due transactions.",
                status_code=HTTP_STATUS['FORBIDDEN']
            )
        
        # Check if already paid
        if due_transaction.is_paid:
            return error_response(
                message="This due transaction has already been paid.",
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Get user's wallet
        try:
            wallet = Wallet.objects.get(user=due_transaction.user)
        except Wallet.DoesNotExist:
            return error_response(
                message="Wallet not found for this user.",
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        # Check if wallet has sufficient balance
        if wallet.balance < due_transaction.total:
            return error_response(
                message=f"Insufficient wallet balance. Required: {due_transaction.total}, Available: {wallet.balance}",
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Process payment
        with db_transaction.atomic():
            # Deduct from wallet
            success = wallet.subtract_balance(
                amount=due_transaction.total,
                description=f"Payment for Due Transaction #{due_transaction.id}",
                performed_by=request.user
            )
            
            if not success:
                return error_response(
                    message="Failed to deduct from wallet balance.",
                    status_code=HTTP_STATUS['INTERNAL_SERVER_ERROR']
                )
            
            # Update due transaction
            due_transaction.is_paid = True
            due_transaction.pay_date = timezone.now()
            due_transaction.save()
        
        # Serialize and return
        serializer = DueTransactionSerializer(due_transaction)
        return success_response(
            data=serializer.data,
            message="Due transaction paid successfully."
        )
    
    except DueTransaction.DoesNotExist:
        return error_response(
            message="Due transaction not found",
            status_code=HTTP_STATUS['NOT_FOUND']
        )
    except Exception as e:
        return error_response(
            message=f"Error processing payment: {str(e)}",
            status_code=HTTP_STATUS['INTERNAL_SERVER_ERROR']
        )


@api_view(['POST'])
@require_super_admin
@api_response
def mark_due_transaction_paid(request, due_transaction_id):
    """
    Mark due transaction as paid (Super Admin only)
    This does NOT create a wallet transaction, just marks it as paid
    """
    try:
        due_transaction = DueTransaction.objects.get(id=due_transaction_id)
        
        # Check if already paid
        if due_transaction.is_paid:
            return error_response(
                message="This due transaction has already been paid.",
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Update due transaction
        due_transaction.is_paid = True
        due_transaction.pay_date = timezone.now()
        due_transaction.save()
        
        # Serialize and return
        serializer = DueTransactionSerializer(due_transaction)
        return success_response(
            data=serializer.data,
            message="Due transaction marked as paid successfully."
        )
    
    except DueTransaction.DoesNotExist:
        return error_response(
            message="Due transaction not found",
            status_code=HTTP_STATUS['NOT_FOUND']
        )
    except Exception as e:
        return error_response(
            message=f"Error marking due transaction as paid: {str(e)}",
            status_code=HTTP_STATUS['INTERNAL_SERVER_ERROR']
        )


@api_view(['POST'])
@require_super_admin
@api_response
def create_due_transaction(request):
    """
    Create a new due transaction (Super Admin only)
    """
    try:
        serializer = DueTransactionCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            due_transaction = serializer.save()
            response_serializer = DueTransactionSerializer(due_transaction)
            return success_response(
                data=response_serializer.data,
                message="Due transaction created successfully."
            )
        else:
            return error_response(
                message="Validation error",
                data=serializer.errors,
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
    
    except Exception as e:
        return error_response(
            message=f"Error creating due transaction: {str(e)}",
            status_code=HTTP_STATUS['INTERNAL_SERVER_ERROR']
        )


@api_view(['GET'])
@require_auth
@api_response
def get_my_due_transactions(request):
    """
    Get current user's due transactions
    """
    try:
        # Get filter parameters
        is_paid = request.GET.get('is_paid')
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        
        # Build queryset
        queryset = DueTransaction.objects.filter(user=request.user).select_related('user').prefetch_related('particulars')
        
        # Apply filters
        if is_paid is not None:
            is_paid_bool = is_paid.lower() == 'true'
            queryset = queryset.filter(is_paid=is_paid_bool)
        
        # Order by created_at descending
        queryset = queryset.order_by('-created_at')
        
        # Paginate
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        # Serialize
        serializer = DueTransactionListSerializer(page_obj.object_list, many=True)
        
        return success_response(
            data={
                'results': serializer.data,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_pages': paginator.num_pages,
                    'total_count': paginator.count,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous(),
                }
            },
            message=SUCCESS_MESSAGES['FETCHED']
        )
    
    except Exception as e:
        return error_response(
            message=f"Error fetching due transactions: {str(e)}",
            status_code=HTTP_STATUS['INTERNAL_SERVER_ERROR']
        )

