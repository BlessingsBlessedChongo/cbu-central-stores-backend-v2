import pytest
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

@pytest.mark.django_db
class TestAuthentication:
    def setup_method(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            username='admin01',
            password='admin123',
            email='admin@cbu.edu.zm',
            role='admin',
            first_name='Admin',
            last_name='User'
        )
        self.department_user = User.objects.create_user(
            username='dept01',
            password='dept123',
            email='dept@cbu.edu.zm',
            role='department_dean',
            department='COMPUTER_SCIENCE',
            first_name='Department',
            last_name='User'
        )
    
    def test_user_registration_admin_only(self):
        """Test that only admins can register users"""
        # Login as admin
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            'username': 'TEST001',
            'email': 'test@cbu.edu.zm',
            'password': 'test123',
            'firstname': 'Test',
            'lastname': 'User',
            'role': 'department_dean',
            'department': 'COMPUTER_SCIENCE'
        }
        
        response = self.client.post(reverse('register'), data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['username'] == 'TEST001'
    
    def test_user_login(self):
        """Test user login functionality"""
        data = {
            'username': 'dept01',
            'password': 'dept123'
        }
        
        response = self.client.post(reverse('login'), data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data
        assert response.data['user']['username'] == 'dept01'
    
    def test_get_current_user(self):
        """Test getting current user info"""
        self.client.force_authenticate(user=self.department_user)
        
        response = self.client.get(reverse('current-user'))
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == 'dept01'
        assert response.data['department'] == 'COMPUTER_SCIENCE'
    
    def test_get_all_users_admin_only(self):
        """Test that only admins can get all users"""
        # Try as department user (should fail)
        self.client.force_authenticate(user=self.department_user)
        response = self.client.get(reverse('all-users'))
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
        # Try as admin (should succeed)
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(reverse('all-users'))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2  # admin + department user