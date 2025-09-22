import pytest
from rest_framework import status
from rest_framework.test import APIClient
from django.urls import reverse
from ..models import Stock, Category, CustomUser

@pytest.mark.django_db
class TestStocksAPI:
    def setup_method(self):
        self.client = APIClient()
        
        # Create test users
        self.stores_manager = CustomUser.objects.create_user(
            username='stores01', password='stores123', role='stores_manager',
            email='stores@cbu.edu.zm'
        )
        
        self.dept_user = CustomUser.objects.create_user(
            username='dept01', password='dept123', role='department_dean',
            email='dept@cbu.edu.zm', department='COMPUTER_SCIENCE'
        )
        
        # Create test category
        self.category = Category.objects.create(
            name='Electronics',
            description='Electronic equipment and devices'
        )
        
        # Create test stock items
        self.stock1 = Stock.objects.create(
            item_name='Dell Laptop',
            original_quantity=20,
            current_quantity=15,
            cost_each=1200.00,
            location='Warehouse A',
            category=self.category
        )
        
        self.stock2 = Stock.objects.create(
            item_name='HP Printer',
            original_quantity=10,
            current_quantity=7,
            cost_each=300.00,
            location='Warehouse B',
            category=self.category
        )
    
    def test_create_stock_item(self):
        """Test creating a new stock item"""
        self.client.force_authenticate(user=self.stores_manager)
        
        data = {
            "item_name": "Projector",
            "original_quantity": 5,
            "current_quantity": 5,
            "cost_each": 900.00,
            "location": "Warehouse C",
            "category": "Electronics"
        }
        
        response = self.client.post(reverse('create-stock'), data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['item_name'] == "Projector"
        assert response.data['location'] == "Warehouse C"
        assert response.data['available'] == True
    
    def test_create_stock_permission(self):
        """Test that only authorized users can create stock items"""
        self.client.force_authenticate(user=self.dept_user)
        
        data = {
            "item_name": "Test Item",
            "original_quantity": 10,
            "current_quantity": 10,
            "cost_each": 100.00,
            "location": "Test Location",
            "category": "Test Category"
        }
        
        response = self.client.post(reverse('create-stock'), data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_get_all_stocks(self):
        """Test getting all stock items"""
        self.client.force_authenticate(user=self.stores_manager)
        
        response = self.client.get(reverse('all-stocks'))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        assert response.data[0]['item_name'] == 'Dell Laptop'
        assert response.data[1]['item_name'] == 'HP Printer'
    
    def test_filter_stocks(self):
        """Test filtering stocks by category and location"""
        self.client.force_authenticate(user=self.stores_manager)
        
        # Filter by category
        response = self.client.get(reverse('all-stocks') + '?category=Electronics')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        
        # Filter by location
        response = self.client.get(reverse('all-stocks') + '?location=Warehouse A')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['location'] == 'Warehouse A'
    
    def test_get_single_stock(self):
        """Test getting single stock item by ID"""
        self.client.force_authenticate(user=self.stores_manager)
        
        response = self.client.get(reverse('get-stock', args=[self.stock1.id]))
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == self.stock1.id
        assert response.data['item_name'] == 'Dell Laptop'
    
    def test_update_stock_item(self):
        """Test updating a stock item"""
        self.client.force_authenticate(user=self.stores_manager)
        
        data = {
            "current_quantity": 14,
            "location": "Warehouse B"
        }
        
        response = self.client.put(
            reverse('update-stock', args=[self.stock1.id]), 
            data, 
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['current_quantity'] == 14
        assert response.data['location'] == "Warehouse B"
    
    def test_delete_stock_item(self):
        """Test deleting a stock item"""
        self.client.force_authenticate(user=self.stores_manager)
        
        response = self.client.delete(reverse('delete-stock', args=[self.stock1.id]))
        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == "Stock item deleted successfully"
        
        # Verify stock item is deleted
        response = self.client.get(reverse('get-stock', args=[self.stock1.id]))
        assert response.status_code == status.HTTP_404_NOT_FOUND