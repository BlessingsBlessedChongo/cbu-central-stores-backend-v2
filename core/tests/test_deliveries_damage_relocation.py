import pytest
from rest_framework import status
from rest_framework.test import APIClient
from django.urls import reverse
from django.utils import timezone
from ..models import Delivery, DamageReport, Relocation, Stock, CustomUser

@pytest.mark.django_db
class TestDeliveriesDamageRelocation:
    def setup_method(self):
        self.client = APIClient()
        
        # Create test users
        self.procurement_officer = CustomUser.objects.create_user(
            username='procure01', password='procure123', role='procurement_officer',
            email='procure@cbu.edu.zm', blockchain_address='0xProcurementOfficer'
        )
        
        self.stores_manager = CustomUser.objects.create_user(
            username='stores01', password='stores123', role='stores_manager',
            email='stores@cbu.edu.zm', blockchain_address='0xStoresManager'
        )
        
        self.dept_user = CustomUser.objects.create_user(
            username='dept01', password='dept123', role='department_dean',
            email='dept@cbu.edu.zm', department='COMPUTER_SCIENCE'
        )
        
        # Create test stock
        self.stock = Stock.objects.create(
            item_name='Test Laptop',
            original_quantity=10,
            current_quantity=10,
            cost_each=1000.00,
            location='Warehouse A',
            available=True
        )
    
    def test_create_delivery(self):
        """Test creating a new delivery"""
        self.client.force_authenticate(user=self.procurement_officer)
        
        data = {
            "stock": self.stock.id,
            "supplier": "Tech Suppliers Ltd",
            "ordered_quantity": 5,
            "unit_cost": 950.00,
            "expected_date": "2025-12-31",
            "notes": "Urgent delivery needed"
        }
        
        response = self.client.post(reverse('create-delivery'), data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['supplier'] == "Tech Suppliers Ltd"
        assert response.data['status'] == "PENDING"
    
    def test_receive_delivery(self):
        """Test receiving a delivery"""
        # First create a delivery
        delivery = Delivery.objects.create(
            stock=self.stock,
            supplier="Test Supplier",
            ordered_quantity=5,
            unit_cost=1000.00,
            expected_date="2025-12-31",
            created_by=self.procurement_officer
        )
        
        self.client.force_authenticate(user=self.stores_manager)
        
        data = {
            "delivered_quantity": 5,
            "actual_date": "2025-12-25",
            "status": "RECEIVED",
            "received_by": self.stores_manager.id
        }
        
        response = self.client.put(
            reverse('update-delivery', args=[delivery.id]),
            data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['delivered_quantity'] == 5
        assert response.data['status'] == "RECEIVED"
        
        # Verify stock was updated
        self.stock.refresh_from_db()
        assert self.stock.current_quantity == 15  # 10 initial + 5 delivered
    
    def test_report_damage(self):
        """Test reporting damaged stock"""
        self.client.force_authenticate(user=self.dept_user)
        
        data = {
            "stock": self.stock.id,
            "quantity": 2,
            "severity": "MODERATE",
            "description": "Screen damage during transportation",
            "location": "Computer Lab A"
        }
        
        response = self.client.post(reverse('report-damage'), data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['quantity'] == 2
        assert response.data['severity'] == "MODERATE"
        
        # Verify stock was updated
        self.stock.refresh_from_db()
        assert self.stock.current_quantity == 8  # 10 initial - 2 damaged
    
    def test_relocate_stock(self):
        """Test relocating stock"""
        self.client.force_authenticate(user=self.stores_manager)
        
        data = {
            "stock": self.stock.id,
            "quantity": 5,
            "from_location": "Warehouse A",
            "to_location": "Warehouse B",
            "reason": "Reorganization of storage areas"
        }
        
        response = self.client.post(reverse('relocate-stock'), data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['from_location'] == "Warehouse A"
        assert response.data['to_location'] == "Warehouse B"
        assert response.data['completed'] == True
        
        # Verify stock location was updated
        self.stock.refresh_from_db()
        assert self.stock.location == "Warehouse B"