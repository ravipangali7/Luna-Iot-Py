"""
Wallet Views
Handles wallet management endpoints
"""
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from decimal import Decimal

from core.models import Wallet, User
from core.serializers import (
    WalletSerializer, 
    WalletCreateSerializer, 
    WalletUpdateSerializer, 
    WalletListSerializer,
    WalletBalanceUpdateSerializer
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
    Get all wallets
    """
    try:
        wallets = Wallet.objects.select_related('user').all()
        serializer = WalletListSerializer(wallets, many=True)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('WALLETS_RETRIEVED', 'Wallets retrieved successfully')
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET'])
@require_auth
@api_response
def get_wallet_by_user(request, user_id):
    """
    Get wallet by user ID
    """
    try:
        try:
            wallet = Wallet.objects.select_related('user').get(user_id=user_id)
        except Wallet.DoesNotExist:
            return error_response(
                message=ERROR_MESSAGES.get('WALLET_NOT_FOUND', 'Wallet not found'),
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        serializer = WalletSerializer(wallet)
        
        return success_response(
            data=serializer.data,
            message='Wallet found'
        )
    except Exception as e:
        return error_response(
            message=str(e),
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
                message=ERROR_MESSAGES.get('WALLET_NOT_FOUND', 'Wallet not found'),
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        serializer = WalletSerializer(wallet)
        
        return success_response(
            data=serializer.data,
            message='Wallet found'
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['POST'])
@require_auth
@api_response
def create_wallet(request):
    """
    Create new wallet
    """
    try:
        serializer = WalletCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            wallet = serializer.save()
            response_serializer = WalletSerializer(wallet)
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('WALLET_CREATED', 'Wallet created successfully'),
                status_code=HTTP_STATUS['CREATED']
            )
        else:
            return error_response(
                message=serializer.errors,
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['PUT'])
@require_auth
@api_response
def update_wallet_balance(request, wallet_id):
    """
    Update wallet balance
    """
    try:
        try:
            wallet = Wallet.objects.get(id=wallet_id)
        except Wallet.DoesNotExist:
            return error_response(
                message=ERROR_MESSAGES.get('WALLET_NOT_FOUND', 'Wallet not found'),
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        serializer = WalletUpdateSerializer(wallet, data=request.data)
        
        if serializer.is_valid():
            wallet = serializer.save()
            response_serializer = WalletSerializer(wallet)
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('WALLET_UPDATED', 'Wallet updated successfully')
            )
        else:
            return error_response(
                message=serializer.errors,
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['PUT'])
@require_auth
@api_response
def update_wallet_balance_operation(request, wallet_id):
    """
    Update wallet balance with operations (add, subtract, set)
    """
    try:
        try:
            wallet = Wallet.objects.get(id=wallet_id)
        except Wallet.DoesNotExist:
            return error_response(
                message=ERROR_MESSAGES.get('WALLET_NOT_FOUND', 'Wallet not found'),
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        serializer = WalletBalanceUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            operation = serializer.validated_data['operation']
            amount = Decimal(str(serializer.validated_data['amount']))
            
            if operation == 'add':
                success = wallet.add_balance(amount)
                message = 'Balance added successfully'
            elif operation == 'subtract':
                success = wallet.subtract_balance(amount)
                if not success:
                    return error_response(
                        message='Insufficient balance',
                        status_code=HTTP_STATUS['BAD_REQUEST']
                    )
                message = 'Balance subtracted successfully'
            elif operation == 'set':
                success = wallet.update_balance(amount)
                message = 'Balance set successfully'
            
            if success:
                response_serializer = WalletSerializer(wallet)
                return success_response(
                    data=response_serializer.data,
                    message=message
                )
            else:
                return error_response(
                    message='Failed to update balance',
                    status_code=HTTP_STATUS['INTERNAL_ERROR']
                )
        else:
            return error_response(
                message=serializer.errors,
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['DELETE'])
@require_auth
@api_response
def delete_wallet(request, wallet_id):
    """
    Delete wallet
    """
    try:
        try:
            wallet = Wallet.objects.get(id=wallet_id)
        except Wallet.DoesNotExist:
            return error_response(
                message=ERROR_MESSAGES.get('WALLET_NOT_FOUND', 'Wallet not found'),
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        wallet.delete()
        
        return success_response(
            message=SUCCESS_MESSAGES.get('WALLET_DELETED', 'Wallet deleted successfully')
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET', 'PUT', 'DELETE'])
@api_response
def wallet_by_id_handler(request, wallet_id):
    """
    Handle wallet operations by ID based on HTTP method
    Routes GET, PUT, DELETE requests to appropriate handlers
    """
    if request.method == 'GET':
        return get_wallet_by_id(request, wallet_id)
    elif request.method == 'PUT':
        return update_wallet_balance(request, wallet_id)
    elif request.method == 'DELETE':
        return delete_wallet(request, wallet_id)
    else:
        return error_response(
            message='Method not allowed',
            status_code=405
        )
