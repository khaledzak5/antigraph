"""
College-based data isolation utilities for doctor users.

This module provides helper functions to ensure doctors can only access
and manage data related to their assigned college.
"""

from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from .models import User


def get_user_college(user: Optional[User]) -> Optional[str]:
    """
    Extract the college from a user object.
    
    For doctors: returns doctor_college
    For college admins: returns college_admin_college  
    For HOD: returns hod_college
    For regular users: returns None
    
    Args:
        user: The current user object
        
    Returns:
        The college name string, or None if user is admin or has no college assignment
    """
    if not user:
        return None
    
    # Super admins have access to all colleges
    if user.is_admin:
        return None
    
    # Doctors have a specific college
    if user.is_doc and user.doctor_college:
        return user.doctor_college
    
    # College admins have a specific college
    if user.is_college_admin and user.college_admin_college:
        return user.college_admin_college
    
    # HOD have a college assignment
    if user.is_hod and user.hod_college:
        return user.hod_college
    
    return None


def verify_college_access(user: Optional[User], college: Optional[str]) -> bool:
    """
    Verify if a user has access to a specific college's data.
    
    Args:
        user: The current user object
        college: The college to verify access for
        
    Returns:
        True if user has access to this college's data, False otherwise
    """
    if not user or not college:
        return False
    
    # Super admins can access everything
    if user.is_admin:
        return True
    
    user_college = get_user_college(user)
    
    # User must be assigned to a college
    if not user_college:
        return False
    
    # Normalize and compare colleges
    return user_college.strip().lower() == college.strip().lower()


def filter_by_college(query, model_class, user: Optional[User]):
    """
    Apply college-based filtering to a SQLAlchemy query.
    
    This function automatically filters by the user's college if they are
    a doctor, college admin, or HOD. Super admins see all data.
    
    Args:
        query: The SQLAlchemy query object
        model_class: The model class to filter (e.g., FirstAidBox)
        user: The current user object
        
    Returns:
        Modified query with college filter applied (or unchanged if user is admin)
    """
    if not user or user.is_admin:
        return query
    
    user_college = get_user_college(user)
    
    if not user_college:
        return query
    
    # Ensure model has a college_id or college column
    if not hasattr(model_class, 'college_id') and not hasattr(model_class, 'college'):
        return query
    
    # Filter by college_id if it exists (preferred)
    if hasattr(model_class, 'college_id'):
        return query.filter(model_class.college_id == user_college)
    
    # Fall back to college column
    if hasattr(model_class, 'college'):
        return query.filter(model_class.college == user_college)
    
    return query


def normalize_college(college: Optional[str]) -> Optional[str]:
    """
    Normalize a college name for consistent comparisons and storage.
    
    - Strips whitespace
    - Collapses internal whitespace
    - Preserves case
    
    Args:
        college: The college name to normalize
        
    Returns:
        Normalized college name, or None if input is None/empty
    """
    if not college:
        return None
    
    # Strip and collapse internal whitespace
    normalized = " ".join(str(college).strip().split())
    return normalized if normalized else None


def validate_college_assignment(user: Optional[User], college: Optional[str]) -> tuple[bool, str]:
    """
    Validate if a user can be assigned to a college and what their access level is.
    
    Args:
        user: The user object to validate
        college: The college to check assignment for
        
    Returns:
        Tuple of (is_valid, reason_or_message)
    """
    if not user:
        return False, "User not found"
    
    if not college:
        return False, "College not specified"
    
    # Super admins can access all colleges
    if user.is_admin:
        return True, "Admin has full access to all colleges"
    
    # Doctors must have a college_college
    if user.is_doc:
        if not user.doctor_college:
            return False, "Doctor has no college assigned"
        if user.doctor_college.strip().lower() != college.strip().lower():
            return False, f"Doctor can only access their assigned college: {user.doctor_college}"
        return True, f"Doctor has access to college: {college}"
    
    # College admins must have a college_admin_college
    if user.is_college_admin:
        if not user.college_admin_college:
            return False, "College admin has no college assigned"
        if user.college_admin_college.strip().lower() != college.strip().lower():
            return False, f"College admin can only access their assigned college: {user.college_admin_college}"
        return True, f"College admin has access to college: {college}"
    
    # HOD must have a hod_college
    if user.is_hod:
        if not user.hod_college:
            return False, "HOD has no college assigned"
        if user.hod_college.strip().lower() != college.strip().lower():
            return False, f"HOD can only access their assigned college: {user.hod_college}"
        return True, f"HOD has access to college: {college}"
    
    return False, "User has no recognized role with college access"


def get_all_accessible_colleges(user: Optional[User]) -> list[str]:
    """
    Get a list of all colleges a user can access.
    
    Args:
        user: The current user object
        
    Returns:
        List of college names the user can access. Empty list for regular users.
    """
    if not user:
        return []
    
    # Super admins have access to all colleges (return empty = no filter)
    if user.is_admin:
        return []
    
    accessible = []
    
    if user.is_doc and user.doctor_college:
        accessible.append(user.doctor_college)
    
    if user.is_college_admin and user.college_admin_college:
        accessible.append(user.college_admin_college)
    
    if user.is_hod and user.hod_college:
        accessible.append(user.hod_college)
    
    return list(set(accessible))  # Remove duplicates if user has multiple roles


def prevent_cross_college_access(user: Optional[User], target_college: Optional[str]) -> None:
    """
    Raise an exception if user tries to access a college they don't have access to.
    
    Args:
        user: The current user object
        target_college: The college they're trying to access
        
    Raises:
        PermissionError: If user doesn't have access to the target college
    """
    from fastapi import HTTPException, status
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    if not target_college:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="College not specified"
        )
    
    is_valid, message = validate_college_assignment(user, target_college)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=message
        )
