"""
This file contains the serializers for the API
"""
from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    This file contains the serializers for the API.
    Serializers in Django REST Framework are responsible for converting complex data types,
    such as querysets and model instances, into Python native datatypes that can then be
    easily rendered into JSON, XML, or other content types. 

    The serializers in this file are likely to be used for handling permissions-related data.
    They may include serializers for models like User, Group, Permission, etc., and may
    include fields like 'id', 'name', 'permissions', etc.

    Each serializer in this file should be a subclass of one of the serializer classes
    provided by Django REST Framework (like Serializer, ModelSerializer, etc.), and should
    define a Meta class that specifies the model and fields to be included in the
    serialized representation.
    """
    def has_object_permission(self, request, view, obj):
        """
        This file, 'permissions.py', contains the permission classes for the API.
        Permission classes in Django REST Framework are used to grant or deny access
        for different classes of users to different parts of the API.

        The permission classes in this file are likely to be used for handling
        permissions-related data. They may include permission classes like 'IsAuthenticated',
        'IsAdminUser', 'IsAuthenticatedOrReadOnly', etc.

        Each permission class in this file should be a subclass of one of the permission
        classes provided by Django REST Framework (like BasePermission, SAFE_METHODS, etc.),
        and should define methods like 'has_permission', 'has_object_permission', etc. that
        determine whether a user has a certain permission.
        """
        if request.method in permissions.SAFE_METHODS:
            # Allow read-only methods for everyone
            return True
        # Check if the user making the request is the owner of the student object
        return obj.user == request.user
