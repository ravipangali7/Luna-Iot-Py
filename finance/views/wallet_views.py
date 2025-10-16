"""
Wallet Views
Handles wallet management endpoints with transaction tracking
"""
from django.http import JsonResponse
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from decimal import Decimal

from finance.models import Wallet, Transaction
from core.models import User
from finance.serializers import (
    WalletSerializer, 
    WalletCreateSerializer, 
    WalletUpdateSerializer, 
    WalletListSerializer,
    WalletBalanceUpdateSerializer,
    WalletTopUpSerializer,
    WalletDetailSerializer,
    WalletSummarySerializer
)
from api_common.utils.response_utils import success_response, error_response
from api_common.constants.api_constants import SUCCESS_MESSAGES, ERROR_MESSAGES, HTTP_STATUS
from api_common.decorators.response_decorators import api_response
from api_common.decorators.auth_decorators import require_auth


@api_view(['GET'])
@require_auth
@api_response
def get_all_wallets(request):
    """
    Get all wallets with filtering and pagination
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
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        
        # Start with all wallets
        wallets = Wallet.objects.select_related('user').all()
        
        # Apply search filter
        if search_query:
            wallets = wallets.filter(
                Q(user__name__icontains=search_query) |
                Q(user__phone__icontains=search_query)
            )
        
        # Order by created_at descending
        wallets = wallets.order_by('-created_at')
        
        # Pagination
        paginator = Paginator(wallets, page_size)
        page_obj = paginator.get_page(page)
        
        # Serialize data
        serializer = WalletListSerializer(page_obj.object_list, many=True)
        
        return success_response(
            message=SUCCESS_MESSAGES['DATA_RETRIEVED'],
            data={
                'wallets': serializer.data,
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
            message="Error retrieving wallets",
            data=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET'])
@require_auth
@api_response
def get_wallet_by_user(request, user_id):
    """
    Get wallet by user ID - automatically creates wallet if it doesn't exist
    """
    try:
        # First verify the user exists
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return error_response(
                message="User not found",
                status_code=HTTP_STATUS['NOT_FOUND']
            )

        # Get or create wallet for the user
        wallet, created = Wallet.objects.select_related('user').get_or_create(
            user_id=user_id,
            defaults={'balance': Decimal('0.00')}
        )
        
        # Check permissions
        if not request.user.groups.filter(name='Super Admin').exists():
            # Regular users can only see their own wallet
            if wallet.user != request.user:
                return error_response(
                    message="Access denied. You can only view your own wallet.",
                    status_code=HTTP_STATUS['FORBIDDEN']
                )
        
        serializer = WalletSerializer(wallet)
        
        # Return success message indicating if wallet was created or retrieved
        message = "Wallet created successfully" if created else SUCCESS_MESSAGES['DATA_RETRIEVED']
        
        return success_response(
            message=message,
            data=serializer.data
        )
        
    except Exception as e:
        return error_response(
            message="Error retrieving wallet",
            data=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET'])
@require_auth
@api_response
def get_wallet_by_id(request, wallet_id):
    """
    Get wallet by wallet ID
    """
    try:
        try:
            wallet = Wallet.objects.select_related('user').get(id=wallet_id)
        except Wallet.DoesNotExist:
            return error_response(
                message="Wallet not found",
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        # Check permissions
        if not request.user.groups.filter(name='Super Admin').exists():
            # Regular users can only see their own wallet
            if wallet.user != request.user:
                return error_response(
                    message="Access denied. You can only view your own wallet.",
                    status_code=HTTP_STATUS['FORBIDDEN']
                )
        
        serializer = WalletSerializer(wallet)
        
        return success_response(
            message=SUCCESS_MESSAGES['DATA_RETRIEVED'],
            data=serializer.data
        )
        
    except Exception as e:
        return error_response(
            message="Error retrieving wallet",
            data=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['POST'])
@require_auth
@api_response
def create_wallet(request):
    """
    Create new wallet
    Super Admin only
    """
    try:
        # Check if user is Super Admin
        if not request.user.groups.filter(name='Super Admin').exists():
            return error_response(
                message="Access denied. Super Admin role required.",
                status_code=HTTP_STATUS['FORBIDDEN']
            )
        
        serializer = WalletCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            wallet = serializer.save()
            response_serializer = WalletSerializer(wallet)
            
            return success_response(
                data=response_serializer.data,
                message="Wallet created successfully",
                status_code=HTTP_STATUS['CREATED']
            )
        else:
            return error_response(
                message="Invalid wallet data",
                data=serializer.errors,
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
            
    except Exception as e:
        return error_response(
            message="Error creating wallet",
            data=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['PUT'])
@require_auth
@api_response
def update_wallet_balance(request, wallet_id):
    """
    Update wallet balance (direct set)
    Super Admin only
    """
    try:
        # Check if user is Super Admin
        if not request.user.groups.filter(name='Super Admin').exists():
            return error_response(
                message="Access denied. Super Admin role required.",
                status_code=HTTP_STATUS['FORBIDDEN']
            )
        
        try:
            wallet = Wallet.objects.get(id=wallet_id)
        except Wallet.DoesNotExist:
            return error_response(
                message="Wallet not found",
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        serializer = WalletUpdateSerializer(wallet, data=request.data)
        
        if serializer.is_valid():
            # Update balance with transaction tracking
            description = request.data.get('description', 'Balance updated directly')
            wallet.update_balance(
                serializer.validated_data['balance'],
                description=description,
                performed_by=request.user
            )
            
            response_serializer = WalletSerializer(wallet)
            
            return success_response(
                data=response_serializer.data,
                message="Wallet balance updated successfully"
            )
        else:
            return error_response(
                message="Invalid balance data",
                data=serializer.errors,
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
            
    except Exception as e:
        return error_response(
            message="Error updating wallet balance",
            data=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['PUT'])
@require_auth
@api_response
def update_wallet_balance_operation(request, wallet_id):
    """
    Update wallet balance with operations (add, subtract, set)
    Super Admin only
    """
    try:
        # Check if user is Super Admin
        if not request.user.groups.filter(name='Super Admin').exists():
            return error_response(
                message="Access denied. Super Admin role required.",
                status_code=HTTP_STATUS['FORBIDDEN']
            )
        
        try:
            wallet = Wallet.objects.get(id=wallet_id)
        except Wallet.DoesNotExist:
            return error_response(
                message="Wallet not found",
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        serializer = WalletBalanceUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            operation = serializer.validated_data['operation']
            amount = Decimal(str(serializer.validated_data['amount']))
            description = serializer.validated_data.get('description', f'Balance {operation} operation')
            
            success = False
            message = ""
            
            if operation == 'add':
                success = wallet.add_balance(amount, description=description, performed_by=request.user)
                message = "Balance added successfully"
            elif operation == 'subtract':
                success = wallet.subtract_balance(amount, description=description, performed_by=request.user)
                if not success:
                    return error_response(
                        message="Insufficient balance",
                        status_code=HTTP_STATUS['BAD_REQUEST']
                    )
                message = "Balance subtracted successfully"
            elif operation == 'set':
                success = wallet.update_balance(amount, description=description, performed_by=request.user)
                message = "Balance set successfully"
            
            if success:
                response_serializer = WalletSerializer(wallet)
                return success_response(
                    data=response_serializer.data,
                    message=message
                )
            else:
                return error_response(
                    message="Failed to update balance",
                    status_code=HTTP_STATUS['INTERNAL_ERROR']
                )
        else:
            return error_response(
                message="Invalid operation data",
                data=serializer.errors,
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
            
    except Exception as e:
        return error_response(
            message="Error updating wallet balance",
            data=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['POST'])
@require_auth
@api_response
def topup_wallet(request, wallet_id):
    """
    Top-up wallet (Super Admin only)
    Add or subtract balance with transaction tracking
    """
    try:
        # Check if user is Super Admin
        if not request.user.groups.filter(name='Super Admin').exists():
            return error_response(
                message="Access denied. Super Admin role required.",
                status_code=HTTP_STATUS['FORBIDDEN']
            )
        
        try:
            wallet = Wallet.objects.get(id=wallet_id)
        except Wallet.DoesNotExist:
            return error_response(
                message="Wallet not found",
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        serializer = WalletTopUpSerializer(data=request.data)
        
        if serializer.is_valid():
            operation = serializer.validated_data['operation']
            amount = Decimal(str(serializer.validated_data['amount']))
            description = serializer.validated_data['description']
            performed_by_id = serializer.validated_data.get('performed_by_id')
            
            # Get performed_by user if specified
            performed_by = None
            if performed_by_id:
                try:
                    performed_by = User.objects.get(id=performed_by_id)
                except User.DoesNotExist:
                    return error_response(
                        message="Performed by user not found",
                        status_code=HTTP_STATUS['BAD_REQUEST']
                    )
            else:
                performed_by = request.user
            
            success = False
            message = ""
            
            if operation == 'add':
                success = wallet.add_balance(amount, description=description, performed_by=performed_by)
                message = "Balance topped up successfully"
            elif operation == 'subtract':
                success = wallet.subtract_balance(amount, description=description, performed_by=performed_by)
                if not success:
                    return error_response(
                        message="Insufficient balance for deduction",
                        status_code=HTTP_STATUS['BAD_REQUEST']
                    )
                message = "Balance deducted successfully"
            
            if success:
                response_serializer = WalletSerializer(wallet)
                return success_response(
                    data=response_serializer.data,
                    message=message
                )
            else:
                return error_response(
                    message="Failed to process top-up",
                    status_code=HTTP_STATUS['INTERNAL_ERROR']
                )
        else:
            return error_response(
                message="Invalid top-up data",
                data=serializer.errors,
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
            
    except Exception as e:
        return error_response(
            message="Error processing wallet top-up",
            data=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['DELETE'])
@require_auth
@api_response
def delete_wallet(request, wallet_id):
    """
    Delete wallet
    Super Admin only
    """
    try:
        # Check if user is Super Admin
        if not request.user.groups.filter(name='Super Admin').exists():
            return error_response(
                message="Access denied. Super Admin role required.",
                status_code=HTTP_STATUS['FORBIDDEN']
            )
        
        try:
            wallet = Wallet.objects.get(id=wallet_id)
        except Wallet.DoesNotExist:
            return error_response(
                message="Wallet not found",
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        wallet.delete()
        
        return success_response(
            message="Wallet deleted successfully"
        )
        
    except Exception as e:
        return error_response(
            message="Error deleting wallet",
            data=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET'])
@require_auth
@api_response
def get_wallet_summary(request):
    """
    Get wallet summary statistics
    Super Admin only
    """
    try:
        # Check if user is Super Admin
        if not request.user.groups.filter(name='Super Admin').exists():
            return error_response(
                message="Access denied. Super Admin role required.",
                status_code=HTTP_STATUS['FORBIDDEN']
            )
        
        # Calculate summary statistics
        total_wallets = Wallet.objects.count()
        total_balance = Wallet.objects.aggregate(total=Sum('balance'))['total'] or 0
        active_wallets = Wallet.objects.filter(user__is_active=True).count()
        inactive_wallets = total_wallets - active_wallets
        wallets_with_balance = Wallet.objects.filter(balance__gt=0).count()
        wallets_with_zero_balance = total_wallets - wallets_with_balance
        
        summary_data = {
            'total_wallets': total_wallets,
            'total_balance': total_balance,
            'active_wallets': active_wallets,
            'inactive_wallets': inactive_wallets,
            'wallets_with_balance': wallets_with_balance,
            'wallets_with_zero_balance': wallets_with_zero_balance
        }
        
        serializer = WalletSummarySerializer(summary_data)
        
        return success_response(
            message=SUCCESS_MESSAGES['DATA_RETRIEVED'],
            data=serializer.data
        )
        
    except Exception as e:
        return error_response(
            message="Error retrieving wallet summary",
            data=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )
