"""
Community Siren Members Views
Handles community siren members management endpoints
"""
from rest_framework.decorators import api_view
from community_siren.models import CommunitySirenMembers
from community_siren.serializers import (
    CommunitySirenMembersSerializer,
    CommunitySirenMembersCreateSerializer,
    CommunitySirenMembersUpdateSerializer,
    CommunitySirenMembersListSerializer
)
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
