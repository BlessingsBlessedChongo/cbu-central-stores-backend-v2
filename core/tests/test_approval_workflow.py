import pytest
from rest_framework import status
from rest_framework.test import APIClient
from django.urls import reverse
from django.utils import timezone
from .models import DepartmentRequest, ApprovalStage, CustomUser

@pytest.mark.django_db
class TestApprovalWorkflow:
    def setup_method(self):
        self.client = APIClient()
        
        # Create test users with different roles
        self.stores_manager = CustomUser.objects.create_user(
            username='stores01', password='stores123', role='stores_manager',
            email='stores@cbu.edu.zm', blockchain_address='0xStoresManager'
        )
        
        self.procurement_officer = CustomUser.objects.create_user(
            username='procure01', password='procure123', role='procurement_officer',
            email='procure@cbu.edu.zm', blockchain_address='0xProcurementOfficer'
        )
        
        self.cfo = CustomUser.objects.create_user(
            username='cfo01', password='cfo123', role='cfo',
            email='cfo@cbu.edu.zm', blockchain_address='0xCFO'
        )
        
        self.dept_user = CustomUser.objects.create_user(
            username='dept01', password='dept123', role='department_dean',
            email='dept@cbu.edu.zm', department='COMPUTER_SCIENCE'
        )
        
        # Create test request
        self.request = DepartmentRequest.objects.create(
            user=self.dept_user,
            item_name="Test Equipment",
            quantity=10,
            priority="HIGH",
            reason="Testing approval workflow",
            status="PENDING",
            department="COMPUTER_SCIENCE"
        )
        
        # Initialize approval stages
        self.request.initialize_approval_stages()
    
    def test_approval_stages_initialized(self):
        """Test that approval stages are created for new requests"""
        stages = ApprovalStage.objects.filter(request=self.request)
        assert stages.count() == 3
        stage_types = [stage.stage for stage in stages]
        assert 'STORES_MANAGER' in stage_types
        assert 'PROCUREMENT_OFFICER' in stage_types
        assert 'CFO' in stage_types
    
    def test_stores_manager_approval(self):
        """Test stores manager approval"""
        self.client.force_authenticate(user=self.stores_manager)
        
        # Get the stores manager approval stage
        stage = ApprovalStage.objects.get(request=self.request, stage='STORES_MANAGER')
        
        data = {
            "approved": True,
            "reason": "Items are needed for department operations",
            "comments": "Approved with suggestion to prioritize"
        }
        
        response = self.client.post(
            reverse('approve-request', args=[self.request.id, stage.id]),
            data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'PROCESSING'
        
        # Verify stage is completed
        stage.refresh_from_db()
        assert stage.completed == True
        assert stage.approved == True
        assert stage.approver == self.stores_manager
    
    def test_permission_validation(self):
        """Test that only authorized users can approve stages"""
        self.client.force_authenticate(user=self.dept_user)  # Department user
        
        stage = ApprovalStage.objects.get(request=self.request, stage='STORES_MANAGER')
        
        data = {
            "approved": True,
            "reason": "Trying to approve without permission"
        }
        
        response = self.client.post(
            reverse('approve-request', args=[self.request.id, stage.id]),
            data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_get_pending_approvals(self):
        """Test getting pending approvals for a user"""
        self.client.force_authenticate(user=self.stores_manager)
        
        response = self.client.get(reverse('pending-approvals'))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['item_name'] == 'Test Equipment'
    
    def test_full_approval_workflow(self):
        """Test complete approval workflow"""
        # Stores Manager approval
        self.client.force_authenticate(user=self.stores_manager)
        stage1 = ApprovalStage.objects.get(request=self.request, stage='STORES_MANAGER')
        self.client.post(
            reverse('approve-request', args=[self.request.id, stage1.id]),
            {"approved": True, "reason": "Approved by stores"},
            format='json'
        )
        
        # Procurement Officer approval
        self.client.force_authenticate(user=self.procurement_officer)
        stage2 = ApprovalStage.objects.get(request=self.request, stage='PROCUREMENT_OFFICER')
        self.client.post(
            reverse('approve-request', args=[self.request.id, stage2.id]),
            {"approved": True, "reason": "Approved by procurement"},
            format='json'
        )
        
        # CFO approval
        self.client.force_authenticate(user=self.cfo)
        stage3 = ApprovalStage.objects.get(request=self.request, stage='CFO')
        response = self.client.post(
            reverse('approve-request', args=[self.request.id, stage3.id]),
            {"approved": True, "reason": "Approved by CFO"},
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'APPROVED'
        assert response.data['is_fully_approved'] == True