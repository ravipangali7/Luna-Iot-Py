"""
Community Siren Members Views
Handles community siren members management endpoints
"""
from rest_framework.decorators import api_view
from community_siren.models import CommunitySirenMembers, CommunitySirenBuzzer, CommunitySirenSwitch
from community_siren.serializers import (
    CommunitySirenMembersSerializer,
    CommunitySirenMembersCreateSerializer,
    CommunitySirenMembersUpdateSerializer,
    CommunitySirenMembersListSerializer,
    CommunitySirenBuzzerWithStatusSerializer,
    CommunitySirenSwitchWithStatusSerializer
)
from core.models import Module, InstituteModule, Institute
from api_common.utils.response_utils import success_response, error_response
from api_common.constants.api_constants import SUCCESS_MESSAGES, ERROR_MESSAGES, HTTP_STATUS
from api_common.decorators.response_decorators import api_response
from api_common.decorators.auth_decorators import require_auth
from api_common.exceptions.api_exceptions import NotFoundError


@api_view(['GET'])
@require_auth
@api_response
def get_all_community_siren_members(request):
    """Get all community siren members"""
    try:
        members = CommunitySirenMembers.objects.select_related('user').all().order_by('-created_at')
        serializer = CommunitySirenMembersListSerializer(members, many=True)
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Community siren members retrieved successfully')
        )
    except Exception as e:
        return error_response(message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'), data=str(e))


@api_view(['GET'])
@require_auth
@api_response
def get_community_siren_member_by_id(request, member_id):
    """Get community siren member by ID"""
    try:
        try:
            member = CommunitySirenMembers.objects.select_related('user').get(id=member_id)
        except CommunitySirenMembers.DoesNotExist:
            raise NotFoundError("Community siren member not found")
        serializer = CommunitySirenMembersSerializer(member)
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Community siren member retrieved successfully')
        )
    except NotFoundError as e:
        return error_response(message=str(e), status_code=HTTP_STATUS['NOT_FOUND'])
    except Exception as e:
        return error_response(message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'), data=str(e))


@api_view(['POST'])
@require_auth
@api_response
def create_community_siren_member(request):
    """Create new community siren member"""
    try:
        serializer = CommunitySirenMembersCreateSerializer(data=request.data)
        if serializer.is_valid():
            member = serializer.save()
            response_serializer = CommunitySirenMembersSerializer(member)
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_CREATED', 'Community siren member created successfully'),
                status_code=HTTP_STATUS['CREATED']
            )
        else:
            return error_response(
                message=ERROR_MESSAGES.get('VALIDATION_ERROR', 'Validation error'),
                data=serializer.errors,
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
    except Exception as e:
        return error_response(message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'), data=str(e))


@api_view(['PUT'])
@require_auth
@api_response
def update_community_siren_member(request, member_id):
    """Update community siren member"""
    try:
        try:
            member = CommunitySirenMembers.objects.get(id=member_id)
        except CommunitySirenMembers.DoesNotExist:
            raise NotFoundError("Community siren member not found")
        serializer = CommunitySirenMembersUpdateSerializer(member, data=request.data)
        if serializer.is_valid():
            member = serializer.save()
            response_serializer = CommunitySirenMembersSerializer(member)
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_UPDATED', 'Community siren member updated successfully')
            )
        else:
            return error_response(
                message=ERROR_MESSAGES.get('VALIDATION_ERROR', 'Validation error'),
                data=serializer.errors,
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
    except NotFoundError as e:
        return error_response(message=str(e), status_code=HTTP_STATUS['NOT_FOUND'])
    except Exception as e:
        return error_response(message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'), data=str(e))


@api_view(['DELETE'])
@require_auth
@api_response
def delete_community_siren_member(request, member_id):
    """Delete community siren member"""
    try:
        try:
            member = CommunitySirenMembers.objects.get(id=member_id)
        except CommunitySirenMembers.DoesNotExist:
            raise NotFoundError("Community siren member not found")
        member.delete()
        return success_response(
            data={'id': member_id},
            message="Community siren member deleted successfully"
        )
    except NotFoundError as e:
        return error_response(message=str(e), status_code=HTTP_STATUS['NOT_FOUND'])
    except Exception as e:
        return error_response(message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'), data=str(e))


@api_view(['GET'])
@require_auth
@api_response
def check_member_access(request):
    """
    Check if current user is a member of any institute with community-siren module
    Returns institute, buzzer, switches, and has_module_access details if access exists
    """
    try:
        user = request.user
        
        # Check if user is Super Admin
        user_groups = user.groups.all()
        user_role_names = [group.name for group in user_groups]
        is_super_admin = 'Super Admin' in user_role_names
        
        # Get the community-siren module
        try:
            community_siren_module = Module.objects.get(slug='community-siren')
        except Module.DoesNotExist:
            return success_response(
                data={'has_access': False, 'has_module_access': False, 'message': 'Community siren module not found'},
                message='Access check completed'
            )
        
        # Find institutes where user has access to community-siren module
        institute_module = None
        institute = None
        has_module_access = False
        
        if is_super_admin:
            # Super Admin: Get all institutes with community-siren module
            institute_modules = InstituteModule.objects.filter(
                module=community_siren_module
            ).select_related('institute').prefetch_related('institute__community_siren_buzzers__device')
            if institute_modules.exists():
                institute_module = institute_modules.first()
                institute = institute_module.institute
                has_module_access = True
        else:
            # Regular users: Get only institutes where user has access
            institute_modules = InstituteModule.objects.filter(
                module=community_siren_module,
                users=user
            ).select_related('institute').prefetch_related('institute__community_siren_buzzers__device')
            if institute_modules.exists():
                institute_module = institute_modules.first()
                institute = institute_module.institute
                has_module_access = True
        
        # If no InstituteModule access, check if user is in CommunitySirenMembers
        if not institute:
            is_community_siren_member = CommunitySirenMembers.objects.filter(user=user).exists()
            if is_community_siren_member:
                # Find institutes that have community-siren module (through InstituteModule)
                # Get institutes that have buzzers or switches configured
                institute_modules = InstituteModule.objects.filter(
                    module=community_siren_module
                ).select_related('institute').prefetch_related('institute__community_siren_buzzers__device')
                
                if institute_modules.exists():
                    # Get the first institute that has community-siren module
                    institute_module = institute_modules.first()
                    institute = institute_module.institute
                    # User is in CommunitySirenMembers but not in InstituteModule
                    has_module_access = False
                else:
                    # No institutes with community-siren module found
                    return success_response(
                        data={'has_access': False, 'has_module_access': False},
                        message='Access check completed'
                    )
            else:
                # User is not in CommunitySirenMembers and has no InstituteModule access
                return success_response(
                    data={'has_access': False, 'has_module_access': False},
                    message='Access check completed'
                )
        
        # Get buzzer for this institute
        buzzers = CommunitySirenBuzzer.objects.filter(
            institute=institute
        ).select_related('device', 'institute').order_by('-created_at')
        
        buzzer_data = None
        if buzzers.exists():
            buzzer = buzzers.first()
            buzzer_serializer = CommunitySirenBuzzerWithStatusSerializer(buzzer)
            buzzer_data = buzzer_serializer.data
            # Add institute logo URL to buzzer data
            if institute.logo:
                try:
                    buzzer_data['institute_logo'] = request.build_absolute_uri(institute.logo.url) if request else institute.logo.url
                except Exception:
                    buzzer_data['institute_logo'] = None
            else:
                buzzer_data['institute_logo'] = None
        
        # Get switches for this institute (only if user has module access)
        switches_data = []
        if has_module_access:
            switches = CommunitySirenSwitch.objects.filter(
                institute=institute
            ).select_related('device', 'institute').order_by('-created_at')
            
            for switch in switches:
                switch_serializer = CommunitySirenSwitchWithStatusSerializer(switch)
                switch_data = switch_serializer.data
                # Add institute logo URL to switch data
                if institute.logo:
                    try:
                        switch_data['institute_logo'] = request.build_absolute_uri(institute.logo.url) if request else institute.logo.url
                    except Exception:
                        switch_data['institute_logo'] = None
                else:
                    switch_data['institute_logo'] = None
                switches_data.append(switch_data)
        
        # Prepare institute data
        logo_url = None
        if institute.logo:
            try:
                logo_url = request.build_absolute_uri(institute.logo.url) if request else institute.logo.url
            except Exception:
                logo_url = None
        
        institute_data = {
            'id': institute.id,
            'name': institute.name,
            'logo': logo_url,
            'phone': institute.phone,
            'address': institute.address,
        }
        
        return success_response(
            data={
                'has_access': True,
                'has_module_access': has_module_access,
                'institute': institute_data,
                'buzzer': buzzer_data,
                'switches': switches_data
            },
            message='Access check completed'
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )
