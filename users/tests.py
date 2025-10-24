"""
Tests for the users app.

Tests cover:
- Profile model functionality
- User services
- Admin actions
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User

from .models import Profile
from .services import (
    get_or_create_profile_by_telegram,
    get_profile_by_telegram_id,
    is_user_approved,
    update_user_balance
)


class ProfileModelTest(TestCase):
    """Test Profile model functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            first_name='John',
            last_name='Doe',
            password='testpass123'
        )
        self.profile = Profile.objects.create(
            user=self.user,
            telegram_id='123456789',
            telegram_username='johndoe',
            phone_number='+1234567890',
            is_approved=True,
            rial_balance=Decimal('1000000'),
            gold_balance_grams=Decimal('10.5000')
        )
    
    def test_profile_str(self):
        """Test string representation of profile."""
        self.assertIn('John Doe', str(self.profile))
        self.assertIn('+1234567890', str(self.profile))
    
    def test_get_display_name(self):
        """Test display name retrieval."""
        self.assertEqual(self.profile.get_display_name(), 'John Doe')
        
        # Test with user without full name
        user2 = User.objects.create_user(username='user2')
        profile2 = Profile.objects.create(
            user=user2,
            telegram_id='987654321',
            phone_number='+9876543210'
        )
        self.assertEqual(profile2.get_display_name(), 'user2')
    
    def test_can_trade(self):
        """Test trading permission check."""
        self.assertTrue(self.profile.can_trade())
        
        self.profile.is_approved = False
        self.assertFalse(self.profile.can_trade())
    
    def test_has_sufficient_rial_balance(self):
        """Test Rial balance check."""
        self.assertTrue(self.profile.has_sufficient_rial_balance(Decimal('500000')))
        self.assertTrue(self.profile.has_sufficient_rial_balance(Decimal('1000000')))
        self.assertFalse(self.profile.has_sufficient_rial_balance(Decimal('1000001')))
    
    def test_has_sufficient_gold_balance(self):
        """Test gold balance check."""
        self.assertTrue(self.profile.has_sufficient_gold_balance(Decimal('5.0000')))
        self.assertTrue(self.profile.has_sufficient_gold_balance(Decimal('10.5000')))
        self.assertFalse(self.profile.has_sufficient_gold_balance(Decimal('10.5001')))


class UserServicesTest(TestCase):
    """Test user service functions."""
    
    def test_get_or_create_profile_by_telegram_new_user(self):
        """Test creating a new profile."""
        profile, created = get_or_create_profile_by_telegram(
            telegram_id='111222333',
            phone_number='+1112223333',
            first_name='Alice',
            last_name='Smith',
            telegram_username='alice'
        )
        
        self.assertTrue(created)
        self.assertEqual(profile.telegram_id, '111222333')
        self.assertEqual(profile.phone_number, '+1112223333')
        self.assertEqual(profile.user.first_name, 'Alice')
        self.assertEqual(profile.telegram_username, 'alice')
    
    def test_get_or_create_profile_by_telegram_existing_user(self):
        """Test getting existing profile."""
        # Create first time
        profile1, created1 = get_or_create_profile_by_telegram(
            telegram_id='444555666',
            phone_number='+4445556666',
            first_name='Bob',
            telegram_username='bob'
        )
        self.assertTrue(created1)
        
        # Get second time
        profile2, created2 = get_or_create_profile_by_telegram(
            telegram_id='444555666',
            phone_number='+4445556666',
            first_name='Bob',
            telegram_username='bob_updated'
        )
        self.assertFalse(created2)
        self.assertEqual(profile1.id, profile2.id)
        self.assertEqual(profile2.telegram_username, 'bob_updated')
    
    def test_get_profile_by_telegram_id(self):
        """Test getting profile by telegram ID."""
        user = User.objects.create_user(username='tg_777888999')
        Profile.objects.create(
            user=user,
            telegram_id='777888999',
            phone_number='+7778889999'
        )
        
        profile = get_profile_by_telegram_id('777888999')
        self.assertIsNotNone(profile)
        self.assertEqual(profile.telegram_id, '777888999')
        
        # Test non-existent
        profile_none = get_profile_by_telegram_id('999999999')
        self.assertIsNone(profile_none)
    
    def test_is_user_approved(self):
        """Test approval status check."""
        user = User.objects.create_user(username='tg_123123123')
        profile = Profile.objects.create(
            user=user,
            telegram_id='123123123',
            phone_number='+1231231234',
            is_approved=False
        )
        
        self.assertFalse(is_user_approved('123123123'))
        
        profile.is_approved = True
        profile.save()
        
        self.assertTrue(is_user_approved('123123123'))
    
    def test_update_user_balance(self):
        """Test balance update."""
        user = User.objects.create_user(username='tg_456456456')
        profile = Profile.objects.create(
            user=user,
            telegram_id='456456456',
            phone_number='+4564564567',
            rial_balance=Decimal('1000'),
            gold_balance_grams=Decimal('10.0000')
        )
        
        # Test adding balance
        updated = update_user_balance(profile, rial_change=500, gold_change=5.5)
        self.assertEqual(updated.rial_balance, Decimal('1500'))
        self.assertEqual(updated.gold_balance_grams, Decimal('15.5000'))
        
        # Test subtracting balance
        updated = update_user_balance(profile, rial_change=-300, gold_change=-2.5)
        self.assertEqual(updated.rial_balance, Decimal('1200'))
        self.assertEqual(updated.gold_balance_grams, Decimal('13.0000'))
        
        # Test insufficient Rial balance
        with self.assertRaises(ValueError) as context:
            update_user_balance(profile, rial_change=-2000)
        self.assertIn('موجودی ریالی', str(context.exception))
        
        # Test insufficient gold balance
        with self.assertRaises(ValueError) as context:
            update_user_balance(profile, gold_change=-20)
        self.assertIn('موجودی طلا', str(context.exception))
