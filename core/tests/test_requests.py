import pytest
from rest_framework import status
from rest_framework.test import APIClient
from django.urls import reverse
from ..models import DepartmentRequest, CustomUser

@pytest.mark.django_db
class TestRequestsAPI:
    def setup_method(self):
        self.client = APIClient()
        
        # Create test users
        self.admin_user = CustomUser.objects.create_user(
            username='admin01', password='admin123', role='admin',
            email='admin@cbu.edu.zm', department='IT_ADMIN'
        )
        
        self.dept_user = CustomUser.objects.create_user(
            username='dept01', password='dept123', role='department_dean',
            email='dept@cbu.edu.zm', department='COMPUTER_SCIENCE'
        )
        
        self.other_dept_user = CustomUser.objects.create_user(
            username='dept02', password='dept123', role='department_dean',
            email='dept2@cbu.edu.zm', department='ENGINEERING'
        )
        
        # Create test requests
        self.request1 = DepartmentRequest.objects.create(
            user=self.dept_user,
            item_name="Dell Laptop",
            quantity=5,
            priority="HIGH",
            reason="New employees need laptops",
            status="PENDING",
            department="COMPUTER_SCIENCE"
        )
        
        self.request2 = DepartmentRequest.objects.create(
            user=self.other_dept_user,
            item_name="Office Chairs",
            quantity=20,
            priority="MEDIUM",
            reason="New office setup",
            status="APPROVED",
            department="ENGINEERING"
        )
    
    def test_create_request(self):
        """Test creating a new request"""
        self.client.force_authenticate(user=self.dept_user)
        
        data = {
            "item": "Projector",
            "quantity": 3,
            "priority": "HIGH",
            "reason": "For classroom presentations",
            "status": "PENDING",
            "requester_id": "dept01",
            "department": "COMPUTER_SCIENCE"
        }
        
        response = self.client.post(reverse('create-request'), data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['item'] == "Projector"
        assert response.data['status'] == "PENDING"
        assert response.data['user_id'] == "dept01"
    
    def test_get_all_requests(self):
        """Test getting all requests"""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get(reverse('all-requests'))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
    
    def test_get_requests_department_filter(self):
        """Test department users only see their own requests"""
        self.client.force_authenticate(user=self.dept_user)
        
        response = self.client.get(reverse('all-requests'))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1  # Only sees own department's requests
        assert response.data[0]['department'] == "COMPUTER_SCIENCE"
    
    def test_get_single_request(self):
        """Test getting single request by ID"""
        self.client.force_authenticate(user=self.dept_user)
        
        response = self.client.get(reverse('get-request', args=[self.request1.id]))
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == self.request1.id
        assert response.data['item'] == "Dell Laptop"
    
    def test_update_request(self):
        """Test updating a request"""
        self.client.force_authenticate(user=self.dept_user)
        
        data = {
            "status": "APPROVED",
            "priority": "MEDIUM"
        }
        
        response = self.client.put(
            reverse('update-request', args=[self.request1.id]), 
            data, 
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == "APPROVED"
        assert response.data['priority'] == "MEDIUM"
    
    def test_delete_request(self):
        """Test deleting a request"""
        self.client.force_authenticate(user=self.dept_user)
        
        response = self.client.delete(reverse('delete-request', args=[self.request1.id]))
        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == "Request deleted successfully"
        
        # Verify request is deleted
        response = self.client.get(reverse('get-request', args=[self.request1.id]))
        assert response.status_code == status.HTTP_404_NOT_FOUND