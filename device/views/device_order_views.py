"""
Device Order Views
Handles device order and cart management endpoints
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Q
from django.core.paginator import Paginator
from decimal import Decimal
import json

from ..models import DeviceOrder, DeviceOrderItem, SubscriptionPlan
from ..serializers.device_order_serializers import (
    DeviceOrderSerializer,
    DeviceOrderListSerializer,
    DeviceOrderCreateSerializer,
    DeviceOrderItemSerializer,
    CartItemSerializer,
    DeviceOrderStatusUpdateSerializer
)
from api_common.utils.response_utils import success_response, error_response
from api_common.constants.api_constants import HTTP_STATUS
from api_common.decorators.response_decorators import api_response
from api_common.decorators.auth_decorators import require_auth, require_dealer_or_admin, require_super_admin
from finance.models import Wallet


# Cart Management APIs (session-based)
@api_view(['GET'])
@require_auth
@require_dealer_or_admin
@api_response
def get_cart(request):
    """
    Get user's cart items
    Cart is stored in session, keyed by user ID
    """
    try:
        user_id = request.user.id
        cart_key = f'cart_{user_id}'
        cart_items = request.session.get(cart_key, [])
        
        # Enrich cart items with subscription plan details
        enriched_items = []
        for item in cart_items:
            try:
                plan = SubscriptionPlan.objects.get(id=item['subscription_plan_id'])
                if plan.purchasing_price is None:
                    continue  # Skip items without purchasing_price
                
                enriched_items.append({
                    'subscription_plan_id': plan.id,
                    'subscription_plan_title': plan.title,
                    'quantity': item['quantity'],
                    'price': float(plan.purchasing_price),
                    'total': float(plan.purchasing_price * Decimal(str(item['quantity'])))
                })
            except SubscriptionPlan.DoesNotExist:
                continue
        
        # Update session with cleaned items
        request.session[cart_key] = [
            {'subscription_plan_id': item['subscription_plan_id'], 'quantity': item['quantity']}
            for item in enriched_items
        ]
        request.session.modified = True
        request.session.save()  # Explicitly save session
        
        # Calculate totals
        subtotal = sum(item['total'] for item in enriched_items)
        total_quantity = sum(item['quantity'] for item in enriched_items)
        
        return success_response(
            data={
                'items': enriched_items,
                'subtotal': float(subtotal),
                'total_quantity': total_quantity,
                'item_count': len(enriched_items)
            },
            message='Cart retrieved successfully'
        )
        
    except Exception as e:
        return error_response(
            message=f'Error retrieving cart: {str(e)}',
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['POST'])
@require_auth
@require_dealer_or_admin
@api_response
def add_to_cart(request):
    """
    Add subscription plan to cart
    """
    try:
        subscription_plan_id = request.data.get('subscription_plan_id')
        quantity = int(request.data.get('quantity', 1))
        
        if not subscription_plan_id:
            return error_response(
                message='subscription_plan_id is required',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        if quantity <= 0:
            return error_response(
                message='Quantity must be greater than 0',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        try:
            plan = SubscriptionPlan.objects.get(id=subscription_plan_id)
        except SubscriptionPlan.DoesNotExist:
            return error_response(
                message='Subscription plan not found',
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        if plan.purchasing_price is None:
            return error_response(
                message='This subscription plan does not have a purchasing price',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Ensure session exists
        if not request.session.session_key:
            request.session.create()
        
        user_id = request.user.id
        cart_key = f'cart_{user_id}'
        cart_items = request.session.get(cart_key, [])
        
        # Check if item already exists in cart
        item_index = None
        for i, item in enumerate(cart_items):
            if item.get('subscription_plan_id') == subscription_plan_id:
                item_index = i
                break
        
        if item_index is not None:
            # Update quantity
            cart_items[item_index]['quantity'] += quantity
        else:
            # Add new item
            cart_items.append({
                'subscription_plan_id': subscription_plan_id,
                'quantity': quantity
            })
        
        request.session[cart_key] = cart_items
        request.session.modified = True
        request.session.save()  # Explicitly save session
        
        return success_response(
            message='Item added to cart successfully'
        )
        
    except Exception as e:
        return error_response(
            message=f'Error adding to cart: {str(e)}',
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['PUT'])
@require_auth
@require_dealer_or_admin
@api_response
def update_cart_item(request, item_index):
    """
    Update cart item quantity by index
    """
    try:
        quantity = int(request.data.get('quantity', 1))
        
        if quantity <= 0:
            return error_response(
                message='Quantity must be greater than 0',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Ensure session exists
        if not request.session.session_key:
            request.session.create()
        
        user_id = request.user.id
        cart_key = f'cart_{user_id}'
        cart_items = request.session.get(cart_key, [])
        
        item_index = int(item_index)
        if item_index < 0 or item_index >= len(cart_items):
            return error_response(
                message='Cart item not found',
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        cart_items[item_index]['quantity'] = quantity
        request.session[cart_key] = cart_items
        request.session.modified = True
        request.session.save()  # Explicitly save session
        
        return success_response(
            message='Cart item updated successfully'
        )
        
    except Exception as e:
        return error_response(
            message=f'Error updating cart item: {str(e)}',
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['DELETE'])
@require_auth
@require_dealer_or_admin
@api_response
def remove_from_cart(request, item_index):
    """
    Remove item from cart by index
    """
    try:
        # Ensure session exists
        if not request.session.session_key:
            request.session.create()
        
        user_id = request.user.id
        cart_key = f'cart_{user_id}'
        cart_items = request.session.get(cart_key, [])
        
        item_index = int(item_index)
        if item_index < 0 or item_index >= len(cart_items):
            return error_response(
                message='Cart item not found',
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        cart_items.pop(item_index)
        request.session[cart_key] = cart_items
        request.session.modified = True
        request.session.save()  # Explicitly save session
        
        return success_response(
            message='Item removed from cart successfully'
        )
        
    except Exception as e:
        return error_response(
            message=f'Error removing from cart: {str(e)}',
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['DELETE'])
@require_auth
@require_dealer_or_admin
@api_response
def clear_cart(request):
    """
    Clear entire cart
    """
    try:
        # Ensure session exists
        if not request.session.session_key:
            request.session.create()
        
        user_id = request.user.id
        cart_key = f'cart_{user_id}'
        request.session[cart_key] = []
        request.session.modified = True
        request.session.save()  # Explicitly save session
        
        return success_response(
            message='Cart cleared successfully'
        )
        
    except Exception as e:
        return error_response(
            message=f'Error clearing cart: {str(e)}',
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


# Order Management APIs
@api_view(['POST'])
@require_auth
@require_dealer_or_admin
@api_response
def create_order(request):
    """
    Create order from cart
    Validates minimum quantity, checks wallet balance, and deducts payment
    """
    try:
        # Ensure session exists
        if not request.session.session_key:
            request.session.create()
        
        user_id = request.user.id
        cart_key = f'cart_{user_id}'
        cart_items = request.session.get(cart_key, [])
        
        if not cart_items:
            return error_response(
                message='Cart is empty',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Get is_vat from request
        is_vat = request.data.get('is_vat', False)
        
        # Validate and prepare order items
        order_items_data = []
        total_quantity = 0
        
        for item in cart_items:
            try:
                plan = SubscriptionPlan.objects.get(id=item['subscription_plan_id'])
                if plan.purchasing_price is None:
                    continue
                
                quantity = item['quantity']
                total_quantity += quantity
                
                order_items_data.append({
                    'subscription_plan': plan.id,
                    'quantity': quantity
                })
            except SubscriptionPlan.DoesNotExist:
                continue
        
        # Validate minimum quantity
        if total_quantity < 50:
            return error_response(
                message=f'Minimum order quantity is 50 devices. Current total: {total_quantity}',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Get user's wallet
        try:
            wallet = Wallet.objects.get(user=request.user)
        except Wallet.DoesNotExist:
            return error_response(
                message='Wallet not found. Please contact administrator.',
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        # Calculate totals
        subtotal = Decimal('0.00')
        for item_data in order_items_data:
            plan = SubscriptionPlan.objects.get(id=item_data['subscription_plan'])
            subtotal += plan.purchasing_price * Decimal(str(item_data['quantity']))
        
        if is_vat:
            vat = subtotal * Decimal('0.13')
        else:
            vat = Decimal('0.00')
        
        total = subtotal + vat
        
        # Check wallet balance
        if wallet.balance < total:
            return error_response(
                message=f'Insufficient wallet balance. Required: {total}, Available: {wallet.balance}. Please top up your wallet.',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Create order
        order = DeviceOrder.objects.create(
            user=request.user,
            status='accepted',
            payment_status='pending',
            sub_total=subtotal,
            is_vat=is_vat,
            vat=vat,
            total=total
        )
        
        # Create order items
        for item_data in order_items_data:
            plan = SubscriptionPlan.objects.get(id=item_data['subscription_plan'])
            DeviceOrderItem.objects.create(
                device_order=order,
                subscription_plan=plan,
                price=plan.purchasing_price,
                quantity=item_data['quantity']
            )
        
        # Recalculate totals (in case of rounding)
        order.calculate_totals()
        order.refresh_from_db()
        
        # Deduct from wallet
        success = wallet.subtract_balance(
            amount=order.total,
            description=f'Device order #{order.id} payment',
            performed_by=request.user
        )
        
        if success:
            order.payment_status = 'completed'
            order.save()
        else:
            order.payment_status = 'failed'
            order.save()
            return error_response(
                message='Payment failed. Please try again.',
                status_code=HTTP_STATUS['INTERNAL_ERROR']
            )
        
        # Clear cart
        request.session[cart_key] = []
        request.session.modified = True
        
        serializer = DeviceOrderSerializer(order)
        
        return success_response(
            data=serializer.data,
            message='Order placed successfully',
            status_code=HTTP_STATUS['CREATED']
        )
        
    except Exception as e:
        return error_response(
            message=f'Error creating order: {str(e)}',
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET'])
@require_auth
@require_dealer_or_admin
@api_response
def list_orders(request):
    """
    List user's orders (paginated)
    Super Admin can see all orders
    """
    try:
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 10))
        search = request.GET.get('search', '')
        status_filter = request.GET.get('status', '')
        payment_status_filter = request.GET.get('payment_status', '')
        
        # Check if user is Super Admin
        is_super_admin = request.user.groups.filter(name='Super Admin').exists()
        
        if is_super_admin:
            queryset = DeviceOrder.objects.all().order_by('-created_at')
        else:
            queryset = DeviceOrder.objects.filter(user=request.user).order_by('-created_at')
        
        # Apply filters
        if search:
            queryset = queryset.filter(
                Q(id__icontains=search) |
                Q(user__name__icontains=search) |
                Q(user__phone__icontains=search)
            )
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if payment_status_filter:
            queryset = queryset.filter(payment_status=payment_status_filter)
        
        # Pagination
        paginator = Paginator(queryset, limit)
        page_obj = paginator.get_page(page)
        
        # Serialize data
        serializer = DeviceOrderListSerializer(page_obj.object_list, many=True)
        
        return success_response(
            data={
                'orders': serializer.data,
                'pagination': {
                    'current_page': page_obj.number,
                    'total_pages': paginator.num_pages,
                    'total_items': paginator.count,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous(),
                }
            },
            message='Orders retrieved successfully'
        )
        
    except Exception as e:
        return error_response(
            message=f'Error retrieving orders: {str(e)}',
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET'])
@require_auth
@require_dealer_or_admin
@api_response
def get_order(request, order_id):
    """
    Get order details by ID
    Users can only see their own orders unless Super Admin
    """
    try:
        order = DeviceOrder.objects.prefetch_related('items__subscription_plan').get(id=order_id)
        
        # Check access
        is_super_admin = request.user.groups.filter(name='Super Admin').exists()
        if not is_super_admin and order.user.id != request.user.id:
            return error_response(
                message='Access denied',
                status_code=HTTP_STATUS['FORBIDDEN']
            )
        
        serializer = DeviceOrderSerializer(order)
        
        return success_response(
            data=serializer.data,
            message='Order retrieved successfully'
        )
        
    except DeviceOrder.DoesNotExist:
        return error_response(
            message='Order not found',
            status_code=HTTP_STATUS['NOT_FOUND']
        )
    except Exception as e:
        return error_response(
            message=f'Error retrieving order: {str(e)}',
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['PUT'])
@require_auth
@require_super_admin
@api_response
def update_order_status(request, order_id):
    """
    Update order status (Super Admin only)
    """
    try:
        order = DeviceOrder.objects.get(id=order_id)
        serializer = DeviceOrderStatusUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            order.status = serializer.validated_data['status']
            if 'payment_status' in serializer.validated_data:
                order.payment_status = serializer.validated_data['payment_status']
            order.save()
            
            response_serializer = DeviceOrderSerializer(order)
            
            return success_response(
                data=response_serializer.data,
                message='Order status updated successfully'
            )
        else:
            return error_response(
                message='Validation error',
                data=serializer.errors,
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
            
    except DeviceOrder.DoesNotExist:
        return error_response(
            message='Order not found',
            status_code=HTTP_STATUS['NOT_FOUND']
        )
    except Exception as e:
        return error_response(
            message=f'Error updating order status: {str(e)}',
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET'])
@require_auth
@require_dealer_or_admin
@api_response
def get_subscription_plans_for_order(request):
    """
    Get subscription plans with purchasing_price for ordering
    """
    try:
        plans = SubscriptionPlan.objects.filter(
            purchasing_price__isnull=False
        ).order_by('title')
        
        plan_data = []
        for plan in plans:
            plan_data.append({
                'id': plan.id,
                'title': plan.title,
                'price': float(plan.price),
                'dealer_price': float(plan.dealer_price) if plan.dealer_price else None,
                'purchasing_price': float(plan.purchasing_price) if plan.purchasing_price else None,
            })
        
        return success_response(
            data=plan_data,
            message='Subscription plans retrieved successfully'
        )
        
    except Exception as e:
        return error_response(
            message=f'Error retrieving subscription plans: {str(e)}',
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )

