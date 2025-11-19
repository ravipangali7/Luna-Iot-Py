"""
Due Transaction Views
Handles due transaction management endpoints with payment processing
"""
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator
from django.utils import timezone
from django.db import transaction as db_transaction
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from decimal import Decimal
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

from finance.models import DueTransaction, DueTransactionParticular, Wallet, Transaction
from core.models import User
from fleet.models import Vehicle
from device.models import UserDevice
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
from finance.management.commands.generate_due_transactions import Command as GenerateDueTransactionsCommand
from datetime import timedelta


def renew_vehicle(vehicle, pay_date):
    """
    Renew vehicle: set is_active=True and update expire_date to next year (same month/day)
    Example: if expire_date is 2025/10/23, after payment it becomes 2026/10/23
    """
    if vehicle and vehicle.expireDate:
        vehicle.is_active = True
        # Update expire_date to next year (same month/day)
        # expireDate is a DateTimeField, so we can use replace
        try:
            from datetime import datetime
            current_expire = vehicle.expireDate
            if isinstance(current_expire, datetime):
                new_year = current_expire.year + 1
                vehicle.expireDate = current_expire.replace(year=new_year)
            else:
                # Handle timezone-aware datetime
                new_year = current_expire.year + 1
                vehicle.expireDate = current_expire.replace(year=new_year)
        except Exception as e:
            # Fallback: add 365 days
            from datetime import timedelta
            vehicle.expireDate = vehicle.expireDate + timedelta(days=365)
        vehicle.save()


def _dealer_has_access_to_due_transaction(due_transaction, user):
    """
    Check if a dealer has access to a due transaction via vehicle device assignment.
    
    Args:
        due_transaction: DueTransaction instance
        user: User instance to check access for
    
    Returns:
        bool: True if dealer has access, False otherwise
    """
    # Check if user is a dealer
    is_dealer = user.groups.filter(name='Dealer').exists()
    if not is_dealer:
        return False
    
    # Check if any particular in the transaction has a vehicle whose device is assigned to the dealer
    has_access = DueTransactionParticular.objects.filter(
        due_transaction=due_transaction,
        vehicle__isnull=False,
        vehicle__device__userDevices__user=user
    ).exists()
    
    return has_access


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
            # Build search filter for text fields
            search_filter = Q(user__name__icontains=search_query) | Q(user__phone__icontains=search_query)
            
            # Try to search by ID if search query is numeric
            try:
                search_id = int(search_query)
                search_filter |= Q(id=search_id)
            except ValueError:
                # If not numeric, only search by name and phone
                pass
            
            queryset = queryset.filter(search_filter)
        
        if is_paid and is_paid.strip():
            is_paid_bool = is_paid.lower().strip() == 'true'
            queryset = queryset.filter(is_paid=is_paid_bool)
        
        # Order by created_at descending
        queryset = queryset.order_by('-created_at')
        
        # Paginate
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        # Serialize
        serializer = DueTransactionListSerializer(page_obj.object_list, many=True, context={'request': request})
        
        return success_response(
            data={
                'results': serializer.data,
                'pagination': {
                    'current_page': page,
                    'page_size': page_size,
                    'total_pages': paginator.num_pages,
                    'total_items': paginator.count,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous(),
                }
            },
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Data retrieved successfully')
        )
    
    except ValueError as e:
        return error_response(
            message=f"Invalid parameter: {str(e)}",
            status_code=HTTP_STATUS['BAD_REQUEST']
        )
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        # Log the full traceback for debugging
        print(f"Error in get_all_due_transactions: {error_trace}")
        return error_response(
            message=f"Error fetching due transactions: {str(e)}",
            status_code=HTTP_STATUS['INTERNAL_ERROR']
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
        dealer_has_access = _dealer_has_access_to_due_transaction(due_transaction, request.user)
        
        if not (is_super_admin or is_owner or dealer_has_access):
            return error_response(
                message="Access denied. You can only view your own due transactions.",
                status_code=HTTP_STATUS['FORBIDDEN']
            )
        
        serializer = DueTransactionSerializer(due_transaction, context={'request': request})
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Data retrieved successfully')
        )
    
    except DueTransaction.DoesNotExist:
        return error_response(
            message="Due transaction not found",
            status_code=HTTP_STATUS['NOT_FOUND']
        )
    except Exception as e:
        return error_response(
            message=f"Error fetching due transaction: {str(e)}",
            status_code=HTTP_STATUS['INTERNAL_ERROR']
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
        if is_paid and is_paid.strip():
            is_paid_bool = is_paid.lower().strip() == 'true'
            queryset = queryset.filter(is_paid=is_paid_bool)
        
        # Order by created_at descending
        queryset = queryset.order_by('-created_at')
        
        # Paginate
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        # Serialize
        serializer = DueTransactionListSerializer(page_obj.object_list, many=True, context={'request': request})
        
        return success_response(
            data={
                'results': serializer.data,
                'pagination': {
                    'current_page': page,
                    'page_size': page_size,
                    'total_pages': paginator.num_pages,
                    'total_items': paginator.count,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous(),
                }
            },
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Data retrieved successfully')
        )
    
    except Exception as e:
        return error_response(
            message=f"Error fetching user due transactions: {str(e)}",
            status_code=HTTP_STATUS['INTERNAL_ERROR']
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
        
        # Check access: user must own the transaction OR be Super Admin OR dealer with device access
        is_super_admin = request.user.groups.filter(name='Super Admin').exists()
        is_owner = due_transaction.user.id == request.user.id
        dealer_has_access = _dealer_has_access_to_due_transaction(due_transaction, request.user)
        
        if not (is_super_admin or is_owner or dealer_has_access):
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
        
        # Get wallet of the logged-in user (payer), not the transaction owner
        payer = request.user
        try:
            wallet = Wallet.objects.get(user=payer)
        except Wallet.DoesNotExist:
            return error_response(
                message="Wallet not found for your account. Please contact administrator.",
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        # Check if payer is Dealer
        is_dealer = payer.groups.filter(name='Dealer').exists()
        is_customer = payer.groups.filter(name='Customer').exists() and not is_dealer and not is_super_admin
        
        # Calculate payment amount based on payer's role
        payment_amount = Decimal('0.00')
        for particular in due_transaction.particulars.all():
            if is_dealer and particular.dealer_amount is not None:
                # Dealer pays dealer_amount
                payment_amount += Decimal(str(particular.dealer_amount)) * Decimal(str(particular.quantity))
            else:
                # Customer/Admin pays regular amount (price)
                payment_amount += Decimal(str(particular.amount)) * Decimal(str(particular.quantity))
        
        # Calculate VAT if needed
        # Customers: no VAT (they don't see it, so they don't pay it)
        # Dealers/Admins: VAT is shown and included in payment
        if (is_dealer or is_super_admin) and not is_customer:
            # Calculate VAT on payment amount
            try:
                from core.models import MySetting
                my_setting = MySetting.objects.first()
                vat_percent = Decimal(str(my_setting.vat_percent)) if my_setting and my_setting.vat_percent else Decimal('0.00')
            except:
                vat_percent = Decimal('0.00')
            vat_amount = (payment_amount * vat_percent) / Decimal('100')
            payment_amount = payment_amount + vat_amount
        
        # Check if payer's wallet has sufficient balance
        if wallet.balance < payment_amount:
            return error_response(
                message=f"Insufficient wallet balance. Required: {payment_amount}, Available: {wallet.balance}",
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Process payment
        pay_date = timezone.now()
        price_type = "dealer price" if is_dealer else "customer price"
        with db_transaction.atomic():
            # Deduct from payer's wallet (logged-in user's wallet)
            success = wallet.subtract_balance(
                amount=payment_amount,
                description=f"Payment for Due Transaction #{due_transaction.id} ({price_type}) (User: {due_transaction.user.name or due_transaction.user.phone})",
                performed_by=request.user
            )
            
            if not success:
                return error_response(
                    message="Failed to deduct from wallet balance.",
                    status_code=HTTP_STATUS['INTERNAL_ERROR']
                )
            
            # Update due transaction
            due_transaction.is_paid = True
            due_transaction.pay_date = pay_date
            due_transaction.paid_by = request.user
            due_transaction.save()
            
            # Renew all vehicles associated with paid particulars
            for particular in due_transaction.particulars.filter(type='vehicle', vehicle__isnull=False):
                if particular.vehicle:
                    renew_vehicle(particular.vehicle, pay_date)
        
        # Serialize and return
        serializer = DueTransactionSerializer(due_transaction, context={'request': request})
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
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['POST'])
@require_auth
@api_response
def pay_particular_with_wallet(request, particular_id):
    """
    Pay a particular (vehicle) using wallet balance
    Removes particular from original due transaction and creates new paid due transaction
    User can pay their own due transaction particulars
    """
    try:
        particular = DueTransactionParticular.objects.select_related(
            'due_transaction', 'due_transaction__user', 'vehicle'
        ).get(id=particular_id)
        
        # Check if particular is vehicle type
        if particular.type != 'vehicle':
            return error_response(
                message="Only vehicle type particulars can be paid individually.",
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Check if vehicle exists
        if not particular.vehicle:
            return error_response(
                message="This particular is not linked to a vehicle.",
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Check access: user must own the due transaction OR be Super Admin OR dealer with device access
        is_super_admin = request.user.groups.filter(name='Super Admin').exists()
        is_owner = particular.due_transaction.user.id == request.user.id
        # For vehicle particulars, check if the vehicle's device is assigned to dealer
        dealer_has_access = False
        if particular.vehicle and particular.vehicle.device:
            dealer_has_access = UserDevice.objects.filter(
                user=request.user,
                device=particular.vehicle.device
            ).exists()
        
        if not (is_super_admin or is_owner or dealer_has_access):
            return error_response(
                message="Access denied. You can only pay your own due transaction particulars.",
                status_code=HTTP_STATUS['FORBIDDEN']
            )
        
        # Check if due transaction is already paid
        if particular.due_transaction.is_paid:
            return error_response(
                message="The due transaction containing this particular is already paid.",
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Get wallet of the logged-in user (payer), not the transaction owner
        payer = request.user
        try:
            wallet = Wallet.objects.get(user=payer)
        except Wallet.DoesNotExist:
            return error_response(
                message="Wallet not found for your account. Please contact administrator.",
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        # Check if payer is Dealer
        is_dealer = payer.groups.filter(name='Dealer').exists()
        is_customer = payer.groups.filter(name='Customer').exists() and not is_dealer and not is_super_admin
        
        # Calculate payment amount based on payer's role
        if is_dealer and particular.dealer_amount is not None:
            # Dealer pays dealer_amount
            particular_payment_amount = Decimal(str(particular.dealer_amount)) * Decimal(str(particular.quantity))
        else:
            # Customer/Admin pays regular amount (price)
            particular_payment_amount = Decimal(str(particular.amount)) * Decimal(str(particular.quantity))
        
        # Calculate VAT if needed
        # Customers: no VAT (they don't see it, so they don't pay it)
        # Dealers/Admins: VAT is shown and included in payment
        if (is_dealer or is_super_admin) and not is_customer:
            try:
                from core.models import MySetting
                my_setting = MySetting.objects.first()
                vat_percent = Decimal(str(my_setting.vat_percent)) if my_setting and my_setting.vat_percent else Decimal('0.00')
            except:
                vat_percent = Decimal('0.00')
            vat_amount = (particular_payment_amount * vat_percent) / Decimal('100')
            particular_payment_amount = particular_payment_amount + vat_amount
        
        # Check if payer's wallet has sufficient balance
        if wallet.balance < particular_payment_amount:
            return error_response(
                message=f"Insufficient wallet balance. Required: {particular_payment_amount}, Available: {wallet.balance}",
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Process partial payment
        pay_date = timezone.now()
        transaction_owner = particular.due_transaction.user
        price_type = "dealer price" if is_dealer else "customer price"
        with db_transaction.atomic():
            # Deduct from payer's wallet (logged-in user's wallet)
            success = wallet.subtract_balance(
                amount=particular_payment_amount,
                description=f"Payment for Particular #{particular.id} ({price_type}) (Vehicle {particular.vehicle.id}, User: {transaction_owner.name or transaction_owner.phone})",
                performed_by=request.user
            )
            
            if not success:
                return error_response(
                    message="Failed to deduct from wallet balance.",
                    status_code=HTTP_STATUS['INTERNAL_ERROR']
                )
            
            # Get original due transaction and save vehicle reference
            original_due = particular.due_transaction
            vehicle_to_renew = particular.vehicle
            particular_particular = particular.particular
            particular_institute = particular.institute
            particular_amount = particular.amount
            particular_dealer_amount = particular.dealer_amount
            particular_quantity = particular.quantity
            
            # Calculate totals for new transaction based on payer role
            if is_dealer and particular_dealer_amount is not None:
                new_subtotal = Decimal(str(particular_dealer_amount)) * Decimal(str(particular_quantity))
            else:
                new_subtotal = Decimal(str(particular_amount)) * Decimal(str(particular_quantity))
            
            # Calculate VAT for new transaction
            # Customers: no VAT (they don't see it, so they don't pay it)
            # Dealers/Admins: VAT is shown and included in payment
            if (is_dealer or is_super_admin) and not is_customer:
                try:
                    from core.models import MySetting
                    my_setting = MySetting.objects.first()
                    vat_percent = Decimal(str(my_setting.vat_percent)) if my_setting and my_setting.vat_percent else Decimal('0.00')
                except:
                    vat_percent = Decimal('0.00')
                new_vat = (new_subtotal * vat_percent) / Decimal('100')
                new_total = new_subtotal + new_vat
            else:
                # Customer: no VAT
                new_vat = Decimal('0.00')
                new_total = new_subtotal
            
            # Create new paid due transaction for this vehicle (owner is the transaction owner, not the payer)
            new_due = DueTransaction.objects.create(
                user=transaction_owner,
                subtotal=new_subtotal,
                vat=new_vat,
                total=new_total,
                renew_date=original_due.renew_date,
                expire_date=original_due.expire_date,
                is_paid=True,
                pay_date=pay_date,
                paid_by=request.user
            )
            
            # Create new particular for the paid due transaction
            DueTransactionParticular.objects.create(
                due_transaction=new_due,
                particular=particular_particular,
                type=particular.type,
                vehicle=vehicle_to_renew,
                institute=particular_institute,
                amount=particular_amount,
                dealer_amount=particular_dealer_amount,
                quantity=particular_quantity,
                total=new_subtotal  # Store subtotal without VAT in particular.total
            )
            
            # Remove particular from original due transaction
            particular.delete()
            
            # Recalculate original due transaction totals
            remaining_particulars = original_due.particulars.all()
            if remaining_particulars.exists():
                original_due.subtotal = sum(
                    Decimal(str(p.total)) for p in remaining_particulars
                )
                original_due.calculate_totals()
                original_due.save()
            else:
                # If no particulars left, delete the empty due transaction
                original_due.delete()
            
            # Renew vehicle
            renew_vehicle(vehicle_to_renew, pay_date)
        
        # Serialize and return the new paid due transaction
        serializer = DueTransactionSerializer(new_due, context={'request': request})
        return success_response(
            data=serializer.data,
            message="Particular paid successfully. Vehicle has been renewed."
        )
    
    except DueTransactionParticular.DoesNotExist:
        return error_response(
            message="Particular not found",
            status_code=HTTP_STATUS['NOT_FOUND']
        )
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in pay_particular_with_wallet: {error_trace}")
        return error_response(
            message=f"Error processing payment: {str(e)}",
            status_code=HTTP_STATUS['INTERNAL_ERROR']
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
        pay_date = timezone.now()
        due_transaction.is_paid = True
        due_transaction.pay_date = pay_date
        due_transaction.save()
        
        # Renew all vehicles associated with paid particulars
        for particular in due_transaction.particulars.filter(type='vehicle', vehicle__isnull=False):
            if particular.vehicle:
                renew_vehicle(particular.vehicle, pay_date)
        
        # Serialize and return
        serializer = DueTransactionSerializer(due_transaction, context={'request': request})
        return success_response(
            data=serializer.data,
            message="Due transaction marked as paid successfully. Vehicles have been renewed."
        )
    
    except DueTransaction.DoesNotExist:
        return error_response(
            message="Due transaction not found",
            status_code=HTTP_STATUS['NOT_FOUND']
        )
    except Exception as e:
        return error_response(
            message=f"Error marking due transaction as paid: {str(e)}",
            status_code=HTTP_STATUS['INTERNAL_ERROR']
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
            response_serializer = DueTransactionSerializer(due_transaction, context={'request': request})
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
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['PUT'])
@require_super_admin
@api_response
def update_due_transaction(request, due_transaction_id):
    """
    Update due transaction (Super Admin only)
    """
    try:
        due_transaction = DueTransaction.objects.get(id=due_transaction_id)
        serializer = DueTransactionUpdateSerializer(due_transaction, data=request.data)
        
        if serializer.is_valid():
            updated_transaction = serializer.save()
            response_serializer = DueTransactionSerializer(updated_transaction, context={'request': request})
            return success_response(
                data=response_serializer.data,
                message="Due transaction updated successfully."
            )
        else:
            return error_response(
                message="Validation error",
                data=serializer.errors,
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
    
    except DueTransaction.DoesNotExist:
        return error_response(
            message="Due transaction not found",
            status_code=HTTP_STATUS['NOT_FOUND']
        )
    except Exception as e:
        return error_response(
            message=f"Error updating due transaction: {str(e)}",
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET'])
@require_auth
@api_response
def get_my_due_transactions(request):
    """
    Get current user's due transactions
    For dealers: includes their own due transactions + due transactions for vehicles linked to their devices
    For customers: only their own due transactions
    """
    try:
        # Get filter parameters
        is_paid = request.GET.get('is_paid')
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        
        # Check if user is a dealer
        is_dealer = request.user.groups.filter(name='Dealer').exists()
        
        # Build queryset
        if is_dealer:
            # Dealer: own due transactions + due transactions for vehicles linked to their devices
            # Use direct relationship traversal to avoid intermediate queries
            queryset = DueTransaction.objects.filter(
                Q(user=request.user) |  # Own due transactions
                Q(particulars__vehicle__device__userDevices__user=request.user)  # Vehicles with devices assigned to dealer
            ).select_related('user').prefetch_related(
                'particulars',
                'particulars__vehicle',
                'particulars__vehicle__device'
            ).distinct()
        else:
            # Customer: only own due transactions
            queryset = DueTransaction.objects.filter(user=request.user).select_related('user').prefetch_related('particulars')
        
        # Apply filters
        if is_paid and is_paid.strip():
            is_paid_bool = is_paid.lower().strip() == 'true'
            queryset = queryset.filter(is_paid=is_paid_bool)
        
        # Order by created_at descending
        queryset = queryset.order_by('-created_at')
        
        # Paginate
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        # Serialize
        serializer = DueTransactionListSerializer(page_obj.object_list, many=True, context={'request': request})
        
        return success_response(
            data={
                'results': serializer.data,
                'pagination': {
                    'current_page': page,
                    'page_size': page_size,
                    'total_pages': paginator.num_pages,
                    'total_items': paginator.count,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous(),
                }
            },
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Data retrieved successfully')
        )
    
    except Exception as e:
        return error_response(
            message=f"Error fetching due transactions: {str(e)}",
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['POST'])
@require_super_admin
@api_response
def generate_due_transactions(request):
    """
    Trigger due transaction generation (Super Admin only)
    This runs the management command to generate dues for expired vehicles and institutional modules
    """
    try:
        command = GenerateDueTransactionsCommand()
        # Capture output to return in response
        from io import StringIO
        import sys
        
        output = StringIO()
        old_stdout = sys.stdout
        sys.stdout = output
        
        try:
            command.handle(dry_run=False)
            result_output = output.getvalue()
        finally:
            sys.stdout = old_stdout
        
        return success_response(
            message="Due transactions generated successfully",
            data={'output': result_output}
        )
    except Exception as e:
        return error_response(
            message=f"Error generating due transactions: {str(e)}",
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['DELETE'])
@require_super_admin
@api_response
def delete_due_transaction(request, due_transaction_id):
    """
    Delete due transaction (Super Admin only, unpaid only)
    """
    try:
        due_transaction = DueTransaction.objects.get(id=due_transaction_id)
        
        # Only allow deletion of unpaid transactions
        if due_transaction.is_paid:
            return error_response(
                message="Cannot delete paid due transactions",
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Delete the transaction (this will cascade delete particulars)
        due_transaction.delete()
        
        return success_response(
            message="Due transaction deleted successfully"
        )
    
    except DueTransaction.DoesNotExist:
        return error_response(
            message="Due transaction not found",
            status_code=HTTP_STATUS['NOT_FOUND']
        )
    except Exception as e:
        return error_response(
            message=f"Error deleting due transaction: {str(e)}",
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET'])
@require_auth
def download_due_transaction_invoice(request, due_transaction_id):
    """
    Download due transaction invoice as PDF
    User can download their own invoices, Super Admin can download any
    """
    try:
        due_transaction = DueTransaction.objects.select_related('user').prefetch_related('particulars').get(id=due_transaction_id)
        
        # Check access
        is_super_admin = request.user.groups.filter(name='Super Admin').exists()
        is_owner = due_transaction.user.id == request.user.id
        dealer_has_access = _dealer_has_access_to_due_transaction(due_transaction, request.user)
        
        if not (is_super_admin or is_owner or dealer_has_access):
            return error_response(
                message="Access denied. You can only download your own invoices.",
                status_code=HTTP_STATUS['FORBIDDEN']
            )
        
        # Create PDF buffer
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        story = []
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#333333'),
            spaceAfter=12
        )
        normal_style = styles['Normal']
        
        # Company/Header Info
        story.append(Paragraph("INVOICE", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Invoice Details
        invoice_data = [
            ['Invoice Number:', f'INV-{due_transaction.id:06d}'],
            ['Date:', due_transaction.created_at.strftime('%B %d, %Y')],
            ['Status:', 'PAID' if due_transaction.is_paid else 'UNPAID'],
        ]
        if due_transaction.pay_date:
            invoice_data.append(['Payment Date:', due_transaction.pay_date.strftime('%B %d, %Y')])
        
        invoice_table = Table(invoice_data, colWidths=[2*inch, 4*inch])
        invoice_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(invoice_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Bill To Section
        story.append(Paragraph("Bill To:", heading_style))
        user_info = [
            ['Name:', due_transaction.user.name or 'N/A'],
            ['Phone:', due_transaction.user.phone or 'N/A'],
        ]
        if due_transaction.user.email:
            user_info.append(['Email:', due_transaction.user.email])
        
        user_table = Table(user_info, colWidths=[1.5*inch, 4.5*inch])
        user_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(user_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Dates
        dates_data = [
            ['Renew Date:', due_transaction.renew_date.strftime('%B %d, %Y')],
            ['Expire Date:', due_transaction.expire_date.strftime('%B %d, %Y')],
        ]
        dates_table = Table(dates_data, colWidths=[2*inch, 4*inch])
        dates_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(dates_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Items Table
        story.append(Paragraph("Items:", heading_style))
        items_data = [['Particular', 'Type', 'Amount', 'Qty', 'Total']]
        
        for particular in due_transaction.particulars.all():
            items_data.append([
                particular.particular[:50] + ('...' if len(particular.particular) > 50 else ''),
                particular.type.upper(),
                f"Rs. {float(particular.amount):.2f}",
                str(particular.quantity),
                f"Rs. {float(particular.total):.2f}"
            ])
        
        items_table = Table(items_data, colWidths=[3*inch, 1*inch, 1*inch, 0.8*inch, 1.2*inch])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        story.append(items_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Totals
        totals_data = [
            ['Subtotal:', f"Rs. {float(due_transaction.subtotal):.2f}"],
            ['VAT:', f"Rs. {float(due_transaction.vat):.2f}"],
            ['Total:', f"Rs. {float(due_transaction.total):.2f}"],
        ]
        totals_table = Table(totals_data, colWidths=[2*inch, 4*inch])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, -1), (1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('FONTSIZE', (1, -1), (1, -1), 14),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, -1), (-1, -1), 8),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),
        ]))
        story.append(totals_table)
        story.append(Spacer(1, 0.5*inch))
        
        # Footer
        footer_text = "Thank you for your business!"
        if not due_transaction.is_paid:
            footer_text = "Please make payment to complete this transaction."
        story.append(Paragraph(footer_text, ParagraphStyle('Footer', parent=normal_style, alignment=TA_CENTER, fontSize=10)))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        # Create HTTP response
        response = HttpResponse(buffer.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_{due_transaction.id}.pdf"'
        return response
    
    except DueTransaction.DoesNotExist:
        return error_response(
            message="Due transaction not found",
            status_code=HTTP_STATUS['NOT_FOUND']
        )
    except Exception as e:
        return error_response(
            message=f"Error generating invoice: {str(e)}",
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )

