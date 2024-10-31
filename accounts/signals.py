from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Profile, User
from monero_app.services import MoneroService
from django.contrib import messages

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # Create a profile for the user
        profile = Profile.objects.create(user=instance)
        
        # Create a Monero subaddress for the user using MoneroService
        monero_service = MoneroService()
        try:
            subaddress = monero_service.create_user_subaddress(label=instance.username)
            if subaddress:
                profile.user_subaddress = subaddress['address']
                profile.save()
            else:
                # Handle the case where subaddress creation fails
                raise ValueError("Failed to create a Monero subaddress.")
        except Exception as e:
            # Log or handle errors appropriately
            print(f"Error creating Monero subaddress for {instance.username}: {e}")
