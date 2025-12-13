"""
Authentication Middleware
Handles token verification using x-phone and x-token headers
Matches Node.js auth_middleware.js functionality
"""
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from core.models.user import User
from api_common.utils.response_utils import error_response
from api_common.constants.api_constants import ERROR_MESSAGES
 

class AuthMiddleware(MiddlewareMixin):
    """
    Middleware to verify authentication token
    Matches Node.js AuthMiddleware.verifyToken functionality
    """
    
    def process_request(self, request):
        # Debug logging for vehicle tag endpoints - verify middleware is running
        is_vehicle_tag_endpoint = request.path and '/api/vehicle-tag/' in request.path
        if is_vehicle_tag_endpoint:
            print(f"[Auth Middleware] ===== MIDDLEWARE STARTED ===== {request.path}")
            print(f"[Auth Middleware] Request method: {request.method}")
            print(f"[Auth Middleware] Initial request.user: {getattr(request, 'user', 'NOT SET')}, type: {type(getattr(request, 'user', None))}")
        
        try:
            if is_vehicle_tag_endpoint:
                print(f"[Auth Middleware] Entered try block for vehicle tag endpoint")
            # Skip authentication for public routes
            public_paths = [
                '/api/core/auth/login',
                '/api/core/auth/register/send-otp',
                '/api/core/auth/register/verify-otp',
                '/api/core/auth/register/resend-otp',
                '/api/core/auth/forgot-password/send-otp',
                '/api/core/auth/forgot-password/verify-otp',
                '/api/core/auth/forgot-password/reset-password',
                '/api/core/auth/biometric-login',  # Public biometric login endpoint
                '/api/health/blood-donation',  # Public blood donation endpoints
                '/api/shared/popup/active',  # Public popup endpoint
            ]
            
            # Skip authentication for public share-track routes (viewing shared links)
            if request.path.startswith('/api/fleet/share-track/token/'):
                if is_vehicle_tag_endpoint:
                    print(f"[Auth Middleware] Skipping - share-track route")
                return None
            
            # Skip authentication for public radar token routes
            if request.path.startswith('/api/alert-system/alert-radar/token/'):
                if is_vehicle_tag_endpoint:
                    print(f"[Auth Middleware] Skipping - radar token route")
                return None
            
            # Skip authentication for public alert history by radar routes  
            if request.path.startswith('/api/alert-system/alert-history/by-radar/'):
                if is_vehicle_tag_endpoint:
                    print(f"[Auth Middleware] Skipping - alert history by radar route")
                return None
            
            # Skip authentication for alert history create endpoint (called by Node)
            if request.path.startswith('/api/alert-system/alert-history/create/') and request.method == 'POST':
                if is_vehicle_tag_endpoint:
                    print(f"[Auth Middleware] Skipping - alert history create route")
                return None
            
            # Skip authentication for community siren history create endpoint (called by Node)
            if request.path.startswith('/api/community-siren/community-siren-history/create/') and request.method == 'POST':
                if is_vehicle_tag_endpoint:
                    print(f"[Auth Middleware] Skipping - community siren history create route")
                return None
            
            # Skip authentication for vehicle tag alert endpoints (public access)
            if request.path.startswith('/api/vehicle-tag/alert/'):
                if is_vehicle_tag_endpoint:
                    print(f"[Auth Middleware] Skipping - vehicle tag alert route (public)")
                return None
            
            # Skip authentication for vehicle tag public endpoints (public access for alert page)
            import re
            # Match VTID format (VTID followed by digits) followed by: /, /latest-alert/, or /qr/
            # Examples: /api/vehicle-tag/VTID84/, /api/vehicle-tag/VTID84/latest-alert/, /api/vehicle-tag/VTID84/qr/
            # DO NOT match: /api/vehicle-tag/generate/, /api/vehicle-tag/history/, etc.
            if (re.match(r'^/api/vehicle-tag/VTID\d+/(latest-alert/|qr/)$', request.path) or
                re.match(r'^/api/vehicle-tag/VTID\d+/$', request.path)):
                if is_vehicle_tag_endpoint:
                    print(f"[Auth Middleware] Skipping - vehicle tag public VTID route")
                return None
            
            # Skip authentication for media files
            if request.path.startswith('/media/'):
                if is_vehicle_tag_endpoint:
                    print(f"[Auth Middleware] Skipping - media route")
                return None

            # Skip authentication for public short-link resolver endpoint
            if request.path.startswith('/api/shared/short-links/'):
                if is_vehicle_tag_endpoint:
                    print(f"[Auth Middleware] Skipping - short-links route")
                return None
                
            # Skip authentication for health blood donation endpoints
            if request.path.startswith('/api/health/blood-donation'):
                if is_vehicle_tag_endpoint:
                    print(f"[Auth Middleware] Skipping - health blood donation route")
                return None
            
            # Skip authentication for Django admin interface
            if request.path.startswith('/admin'):
                if is_vehicle_tag_endpoint:
                    print(f"[Auth Middleware] Skipping - admin route")
                return None
            if request.path.startswith('/admin/'):
                if is_vehicle_tag_endpoint:
                    print(f"[Auth Middleware] Skipping - admin route (with slash)")
                return None
            
            # Skip authentication for specific device endpoints (Node.js GT06 handler)
            if request.path.startswith('/api/device/status/') and request.method == 'POST':
                if is_vehicle_tag_endpoint:
                    print(f"[Auth Middleware] Skipping - device status route")
                return None
            if request.path.startswith('/api/device/location/') and request.method == 'POST':
                if is_vehicle_tag_endpoint:
                    print(f"[Auth Middleware] Skipping - device location route")
                return None
            
            if request.path in public_paths:
                if is_vehicle_tag_endpoint:
                    print(f"[Auth Middleware] Path is in public_paths, skipping auth")
                return None
            
            # Debug: Log that we're past all the public path checks
            if is_vehicle_tag_endpoint:
                print(f"[Auth Middleware] Past public path checks, proceeding with authentication")
                print(f"[Auth Middleware] About to extract headers from request.META")
                
            # Extract phone and token from headers
            # Try multiple header formats to handle different proxy/load balancer configurations
            phone = None
            token = None
            
            # Check META first (standard Django way)
            phone = (request.META.get('HTTP_X_PHONE') or 
                    request.META.get('X-PHONE') or 
                    request.META.get('x-phone') or
                    request.META.get('HTTP_X_PHONE_NORMALIZED'))
            
            token = (request.META.get('HTTP_X_TOKEN') or 
                    request.META.get('X-TOKEN') or 
                    request.META.get('x-token') or
                    request.META.get('HTTP_X_TOKEN_NORMALIZED'))
            
            # If not found in META, check request.headers (Django 2.2+)
            if not phone and hasattr(request, 'headers'):
                phone = (request.headers.get('X-PHONE') or 
                        request.headers.get('x-phone') or
                        request.headers.get('HTTP_X_PHONE'))
            
            if not token and hasattr(request, 'headers'):
                token = (request.headers.get('X-TOKEN') or 
                        request.headers.get('x-token') or
                        request.headers.get('HTTP_X_TOKEN'))
            
            # Debug logging for vehicle tag endpoints
            if is_vehicle_tag_endpoint:
                print(f"[Auth Middleware] Processing vehicle tag request: {request.path}")
                print(f"[Auth Middleware] Request method: {request.method}")
                print(f"[Auth Middleware] Phone header (HTTP_X_PHONE): {request.META.get('HTTP_X_PHONE')}")
                print(f"[Auth Middleware] Token header (HTTP_X_TOKEN): {'SET' if request.META.get('HTTP_X_TOKEN') else 'NOT SET'}")
                print(f"[Auth Middleware] Phone (all formats checked): {phone}, Token (all formats checked): {'SET' if token else 'NOT SET'}")
                print(f"[Auth Middleware] All META keys with X/PHONE/TOKEN: {[k for k in request.META.keys() if 'X' in k.upper() or 'PHONE' in k.upper() or 'TOKEN' in k.upper()]}")
                if hasattr(request, 'headers'):
                    print(f"[Auth Middleware] Request.headers keys: {list(request.headers.keys()) if hasattr(request.headers, 'keys') else 'N/A'}")
                    if hasattr(request.headers, 'get'):
                        print(f"[Auth Middleware] Request.headers X-PHONE: {request.headers.get('X-PHONE')}")
                        print(f"[Auth Middleware] Request.headers x-phone: {request.headers.get('x-phone')}")
                        print(f"[Auth Middleware] Request.headers X-TOKEN: {'SET' if request.headers.get('X-TOKEN') else 'NOT SET'}")
                        print(f"[Auth Middleware] Request.headers x-token: {'SET' if request.headers.get('x-token') else 'NOT SET'}")
                # Log all META keys for debugging
                all_meta_keys = list(request.META.keys())
                print(f"[Auth Middleware] Total META keys: {len(all_meta_keys)}")
                print(f"[Auth Middleware] Sample META keys: {all_meta_keys[:30]}")
            
            if not phone or not token:
                if is_vehicle_tag_endpoint:
                    print(f"[Auth Middleware] Missing phone or token for vehicle tag endpoint - returning 401")
                    print(f"[Auth Middleware] Final check - phone: {phone}, token: {'SET' if token else 'NOT SET'}")
                return error_response( 
                    message='Phone and token required',
                    status_code=401
                )
            
            # Find user by phone first, then verify token
            try:
                # First check if any users exist
                user_count = User.objects.count()
                
                # List all users for debugging
                all_users = User.objects.all()[:5]  # Get first 5 users
                
                # Find user by phone
                user = User.objects.get(phone=phone)
                
                # Check if token matches
                if user.token != token:
                    if is_vehicle_tag_endpoint:
                        print(f"[Auth Middleware] Token mismatch for vehicle tag endpoint - user token: {user.token}, expected: {token}")
                    print(f"Auth Middleware: Token mismatch - user token: {user.token}, expected: {token}")
                    return error_response(
                        message='Invalid token',
                        status_code=401
                    )
                
                if not user.is_active:
                    if is_vehicle_tag_endpoint:
                        print(f"[Auth Middleware] User is not active for vehicle tag endpoint")
                    print(f"Auth Middleware: User is not active")
                    return error_response(
                        message='User account is not active',
                        status_code=777
                    )
                
                # Add user to request
                # Ensure user is properly set and marked as authenticated
                # Force overwrite even if Django's AuthenticationMiddleware set AnonymousUser
                request.user = user
                
                # Verify the user was set correctly
                if is_vehicle_tag_endpoint:
                    print(f"[Auth Middleware] Before setting user - request.user type: {type(request.user)}")
                
                # Force overwrite to ensure our authenticated user is used
                request.user = user
                
                # Verify is_authenticated property works
                is_auth = getattr(request.user, 'is_authenticated', False)
                if is_vehicle_tag_endpoint:
                    print(f"[Auth Middleware] After setting user - request.user: {request.user}, "
                          f"type: {type(request.user)}, "
                          f"is_authenticated: {is_auth}, "
                          f"phone: {request.user.phone if hasattr(request.user, 'phone') else 'N/A'}")
                
                # Double-check that user is not AnonymousUser
                from django.contrib.auth.models import AnonymousUser
                if isinstance(request.user, AnonymousUser):
                    if is_vehicle_tag_endpoint:
                        print(f"[Auth Middleware] ERROR: User is still AnonymousUser after setting! Forcing overwrite.")
                    # Force overwrite again
                    request.user = user
                
                return None
                
            except User.DoesNotExist:
                if is_vehicle_tag_endpoint:
                    print(f"[Auth Middleware] User not found with phone: {phone}")
                print(f"Auth Middleware: User not found with phone: {phone}")
                return error_response(
                    message='User matching query does not exist.',
                    status_code=404
                )
                
            except Exception as e:
                if is_vehicle_tag_endpoint:
                    print(f"[Auth Middleware] Exception occurred: {str(e)}")
                    import traceback
                    traceback.print_exc()
                print(f"Auth Middleware: Exception occurred: {str(e)}")
                import traceback
                traceback.print_exc()
                return error_response(
                    message='Authentication error',
                    status_code=500
                )
        except Exception as outer_exception:
            # Catch any unexpected exceptions in the middleware
            if is_vehicle_tag_endpoint:
                print(f"[Auth Middleware] CRITICAL: Outer exception in middleware: {str(outer_exception)}")
                import traceback
                traceback.print_exc()
            # Don't let middleware exceptions break the request - return None to continue
            # The decorator will handle authentication
            return None
