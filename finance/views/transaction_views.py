"""
Transaction Views
Handles transaction-related API endpoints
"""
from django.http import JsonResponse
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, timedelta

from finance.models import Transaction, Wallet
from core.models import User
from finance.serializers import (
    TransactionSerializer,
    TransactionCreateSerializer,
    TransactionListSerializer,
    TransactionFilterSerializer,
    TransactionSummarySerializer
)
from api_common.utils.response_utils import success_response, error_response
from api_common.constants.api_constants import SUCCESS_MESSAGES, ERROR_MESSAGES, HTTP_STATUS
from api_common.decorators.response_decorators import api_response
from api_common.decorators.auth_decorators import require_auth


@api_view(['GET'])
@require_auth
@api_response
def get_all_transactions(request):
    """
    Get all transactions with filtering and pagination
    Super Admin only
    """
    try:
        # Check if user is Super Admin
        if not request.user.groups.filter(name='Super Admin').exists():
            return error_response(
                message="Access denied. Super Admin role required.",
                status_code=HTTP_STATUS.FORBIDDEN
            )
        
        # Get filter parameters
        filters = TransactionFilterSerializer(data=request.GET)
        if not filters.is_valid():
            return error_response(
                message="Invalid filter parameters",
                data=filters.errors,
                status_code=HTTP_STATUS.BAD_REQUEST
            )
        
        filter_data = filters.validated_data
        
        # Start with all transactions
        transactions = Transaction.objects.select_related('wallet__user', 'performed_by').all()
        
        # Apply filters
        if filter_data.get('wallet_id'):
            transactions = transactions.filter(wallet_id=filter_data['wallet_id'])
        
        if filter_data.get('user_id'):
            transactions = transactions.filter(wallet__user_id=filter_data['user_id'])
        
        if filter_data.get('transaction_type'):
            transactions = transactions.filter(transaction_type=filter_data['transaction_type'])
        
        if filter_data.get('status'):
            transactions = transactions.filter(status=filter_data['status'])
        
        if filter_data.get('date_from'):
            transactions = transactions.filter(created_at__gte=filter_data['date_from'])
        
        if filter_data.get('date_to'):
            transactions = transactions.filter(created_at__lte=filter_data['date_to'])
        
        if filter_data.get('search'):
            search_term = filter_data['search']
            transactions = transactions.filter(
                Q(description__icontains=search_term) |
                Q(wallet__user__name__icontains=search_term) |
                Q(wallet__user__phone__icontains=search_term)
            )
        
        # Order by created_at descending
        transactions = transactions.order_by('-created_at')
        
        # Pagination
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        paginator = Paginator(transactions, page_size)
        page_obj = paginator.get_page(page)
        
        # Serialize data
        serializer = TransactionListSerializer(page_obj.object_list, many=True)
        
        return success_response(
            message=SUCCESS_MESSAGES.DATA_RETRIEVED,
            data={
                'transactions': serializer.data,
                'pagination': {
                    'current_page': page_obj.number,
                    'total_pages': paginator.num_pages,
                    'total_count': paginator.count,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous()
                }
            }
        )
        
    except Exception as e:
        return error_response(
            message="Error retrieving transactions",
            data=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET'])
@require_auth
@api_response
def get_transaction_by_id(request, transaction_id):
    """
    Get transaction details by ID
    """
    try:
        transaction = Transaction.objects.select_related(
            'wallet__user', 'performed_by'
        ).get(id=transaction_id)
        
        serializer = TransactionSerializer(transaction)
        
        return success_response(
            message=SUCCESS_MESSAGES.DATA_RETRIEVED,
            data=serializer.data
        )
        
    except Transaction.DoesNotExist:
        return error_response(
            message="Transaction not found",
            status_code=HTTP_STATUS.NOT_FOUND
        )
    except Exception as e:
        return error_response(
            message="Error retrieving transaction",
            data=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET'])
@require_auth
@api_response
def get_wallet_transactions(request, wallet_id):
    """
    Get transactions for a specific wallet
    """
    try:
        # Check if wallet exists
        try:
            wallet = Wallet.objects.get(id=wallet_id)
        except Wallet.DoesNotExist:
            return error_response(
                message="Wallet not found",
                status_code=HTTP_STATUS.NOT_FOUND
            )
        
        # Check permissions
        if not request.user.groups.filter(name='Super Admin').exists():
            # Regular users can only see their own wallet transactions
            if wallet.user != request.user:
                return error_response(
                    message="Access denied. You can only view your own wallet transactions.",
                    status_code=HTTP_STATUS.FORBIDDEN
                )
        
        # Get transactions
        transactions = Transaction.objects.filter(wallet=wallet).order_by('-created_at')
        
        # Pagination
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        paginator = Paginator(transactions, page_size)
        page_obj = paginator.get_page(page)
        
        # Serialize data
        serializer = TransactionListSerializer(page_obj.object_list, many=True)
        
        return success_response(
            message=SUCCESS_MESSAGES.DATA_RETRIEVED,
            data={
                'wallet_id': wallet_id,
                'wallet_owner': {
                    'id': wallet.user.id,
                    'name': wallet.user.name,
                    'phone': wallet.user.phone
                },
                'transactions': serializer.data,
                'pagination': {
                    'current_page': page_obj.number,
                    'total_pages': paginator.num_pages,
                    'total_count': paginator.count,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous()
                }
            }
        )
        
    except Exception as e:
        return error_response(
            message="Error retrieving wallet transactions",
            data=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET'])
@require_auth
@api_response
def get_user_transactions(request, user_id):
    """
    Get transactions for a specific user's wallet
    """
    try:
        # Check if user exists
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return error_response(
                message="User not found",
                status_code=HTTP_STATUS.NOT_FOUND
            )
        
        # Check permissions
        if not request.user.groups.filter(name='Super Admin').exists():
            # Regular users can only see their own transactions
            if user != request.user:
                return error_response(
                    message="Access denied. You can only view your own transactions.",
                    status_code=HTTP_STATUS.FORBIDDEN
                )
        
        # Get user's wallet
        try:
            wallet = Wallet.objects.get(user=user)
        except Wallet.DoesNotExist:
            return error_response(
                message="User does not have a wallet",
                status_code=HTTP_STATUS.NOT_FOUND
            )
        
        # Get transactions
        transactions = Transaction.objects.filter(wallet=wallet).order_by('-created_at')
        
        # Pagination
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        paginator = Paginator(transactions, page_size)
        page_obj = paginator.get_page(page)
        
        # Serialize data
        serializer = TransactionListSerializer(page_obj.object_list, many=True)
        
        return success_response(
            message=SUCCESS_MESSAGES.DATA_RETRIEVED,
            data={
                'user_id': user_id,
                'user_name': user.name,
                'user_phone': user.phone,
                'wallet_id': wallet.id,
                'transactions': serializer.data,
                'pagination': {
                    'current_page': page_obj.number,
                    'total_pages': paginator.num_pages,
                    'total_count': paginator.count,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous()
                }
            }
        )
        
    except Exception as e:
        return error_response(
            message="Error retrieving user transactions",
            data=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['POST'])
@require_auth
@api_response
def create_transaction(request):
    """
    Create a manual transaction (Super Admin only)
    """
    try:
        # Check if user is Super Admin
        if not request.user.groups.filter(name='Super Admin').exists():
            return error_response(
                message="Access denied. Super Admin role required.",
                status_code=HTTP_STATUS.FORBIDDEN
            )
        
        serializer = TransactionCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Invalid transaction data",
                data=serializer.errors,
                status_code=HTTP_STATUS.BAD_REQUEST
            )
        
        # Create transaction
        transaction = serializer.save()
        
        # Update wallet balance
        wallet = transaction.wallet
        if transaction.transaction_type == 'CREDIT':
            wallet.add_balance(
                transaction.amount,
                description=transaction.description,
                performed_by=transaction.performed_by
            )
        else:  # DEBIT
            wallet.subtract_balance(
                transaction.amount,
                description=transaction.description,
                performed_by=transaction.performed_by
            )
        
        # Return created transaction
        response_serializer = TransactionSerializer(transaction)
        
        return success_response(
            message="Transaction created successfully",
            data=response_serializer.data,
            status_code=HTTP_STATUS.CREATED
        )
        
    except Exception as e:
        return error_response(
            message="Error creating transaction",
            data=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET'])
@require_auth
@api_response
def get_transaction_summary(request):
    """
    Get transaction summary statistics (Super Admin only)
    """
    try:
        # Check if user is Super Admin
        if not request.user.groups.filter(name='Super Admin').exists():
            return error_response(
                message="Access denied. Super Admin role required.",
                status_code=HTTP_STATUS.FORBIDDEN
            )
        
        # Get date range (default to last 30 days)
        days = int(request.GET.get('days', 30))
        date_from = datetime.now() - timedelta(days=days)
        
        # Get transactions in date range
        transactions = Transaction.objects.filter(created_at__gte=date_from)
        
        # Calculate summary
        total_transactions = transactions.count()
        total_credit = transactions.filter(transaction_type='CREDIT').aggregate(
            total=Sum('amount')
        )['total'] or 0
        total_debit = transactions.filter(transaction_type='DEBIT').aggregate(
            total=Sum('amount')
        )['total'] or 0
        net_change = total_credit - total_debit
        
        pending_transactions = transactions.filter(status='PENDING').count()
        completed_transactions = transactions.filter(status='COMPLETED').count()
        failed_transactions = transactions.filter(status='FAILED').count()
        
        summary_data = {
            'total_transactions': total_transactions,
            'total_credit': total_credit,
            'total_debit': total_debit,
            'net_change': net_change,
            'pending_transactions': pending_transactions,
            'completed_transactions': completed_transactions,
            'failed_transactions': failed_transactions,
            'date_range_days': days
        }
        
        serializer = TransactionSummarySerializer(summary_data)
        
        return success_response(
            message=SUCCESS_MESSAGES.DATA_RETRIEVED,
            data=serializer.data
        )
        
    except Exception as e:
        return error_response(
            message="Error retrieving transaction summary",
            data=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )
