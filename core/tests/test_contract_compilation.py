import pytest
import os
import json
from django.conf import settings
from django.core.management import call_command

@pytest.mark.django_db
class TestContractCompilation:
    def test_compile_contract_command(self):
        """Test that the contract compilation command works"""
        # Ensure build directory doesn't exist initially
        build_dir = os.path.join(settings.BASE_DIR, 'contracts', 'build')
        
        # Call the compile command
        call_command('compile_contract')
        
        # Check that build files were created
        compiled_path = os.path.join(build_dir, 'compiled_contract.json')
        abi_path = os.path.join(build_dir, 'abi.json')
        
        assert os.path.exists(compiled_path), "Compiled contract file should exist"
        assert os.path.exists(abi_path), "ABI file should exist"
        
        # Verify the content
        with open(compiled_path, 'r') as file:
            compiled_data = json.load(file)
            assert 'contracts' in compiled_data
        
        with open(abi_path, 'r') as file:
            abi_data = json.load(file)
            assert isinstance(abi_data, list)