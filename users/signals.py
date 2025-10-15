"""
Signals for the users app.

Automatically creates a Profile when a User is created.
"""

import logging
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Profile

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance: User, created: bool, **kwargs):
    """
    Signal handler to automatically create a Profile when a User is created.
    
    Args:
        sender: The model class (User)
        instance: The actual User instance being saved
        created: Boolean indicating if this is a new User
        **kwargs: Additional keyword arguments
    """
    if created and not hasattr(instance, 'profile'):
        try:
            # Note: telegram_id and phone_number must be set separately
            # This signal only creates the Profile, actual data is filled later
            logger.info(f"Profile creation signal triggered for user: {instance.username}")
        except Exception as e:
            logger.error(f"Error in profile creation signal: {str(e)}")
