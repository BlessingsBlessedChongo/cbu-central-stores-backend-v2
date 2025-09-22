// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract StreamlinedStoresManagerV3 {
    address public owner;
    
    // Role management
    mapping(address => bool) public isStoresManager;
    mapping(address => bool) public isProcurementOfficer;
    mapping(address => bool) public isCFO;
    mapping(address => bool) public isDepartmentDean;
    
    // Request structure
    struct DepartmentRequest {
        uint256 requestId;
        address departmentAddress;
        string itemName;
        uint256 quantity;
        string priority;
        string reason;
        uint256 timestamp;
        bool exists;
    }
    
    // Approval structure
    struct Approval {
        address approver;
        bool approved;
        string reason;
        uint256 timestamp;
    }
    
    // Request tracking
    mapping(uint256 => DepartmentRequest) public requests;
    mapping(uint256 => Approval[]) public requestApprovals;
    uint256 public requestCounter;
    
    // Events
    event RoleAssigned(address indexed user, string role, bool assigned, uint256 timestamp);
    event RequestCreated(uint256 indexed requestId, address indexed department, string itemName, uint256 quantity, string priority, uint256 timestamp);
    event RequestApproved(uint256 indexed requestId, address indexed approver, bool approved, string reason, uint256 timestamp);
    event StockAdjusted(string itemName, int256 quantityChange, string reason, uint256 timestamp);
    event DeliveryLogged(string itemName, uint256 quantity, string supplier, uint256 timestamp);
    event DamageReported(string itemName, uint256 quantity, string description, uint256 timestamp);
    event RelocationLogged(string itemName, uint256 quantity, string fromLocation, string toLocation, uint256 timestamp);
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can perform this action");
        _;
    }
    
    modifier onlyStoresManager() {
        require(isStoresManager[msg.sender], "Only Stores Manager can perform this action");
        _;
    }
    
    modifier onlyProcurementOfficer() {
        require(isProcurementOfficer[msg.sender], "Only Procurement Officer can perform this action");
        _;
    }
    
    modifier onlyCFO() {
        require(isCFO[msg.sender], "Only CFO can perform this action");
        _;
    }
    
    modifier onlyDepartmentDean() {
        require(isDepartmentDean[msg.sender], "Only Department Dean can perform this action");
        _;
    }
    
    constructor() {
        owner = msg.sender;
        requestCounter = 0;
    }
    
    // Role management functions
    function assignStoresManager(address _manager, bool _status) external onlyOwner {
        isStoresManager[_manager] = _status;
        emit RoleAssigned(_manager, "StoresManager", _status, block.timestamp);
    }
    
    function assignProcurementOfficer(address _officer, bool _status) external onlyOwner {
        isProcurementOfficer[_officer] = _status;
        emit RoleAssigned(_officer, "ProcurementOfficer", _status, block.timestamp);
    }
    
    function assignCFO(address _cfo, bool _status) external onlyOwner {
        isCFO[_cfo] = _status;
        emit RoleAssigned(_cfo, "CFO", _status, block.timestamp);
    }
    
    function assignDepartmentDean(address _dean, bool _status) external onlyOwner {
        isDepartmentDean[_dean] = _status;
        emit RoleAssigned(_dean, "DepartmentDean", _status, block.timestamp);
    }
    
    // Request functions
    function createRequest(
        string memory _itemName,
        uint256 _quantity,
        string memory _priority,
        string memory _reason
    ) external onlyDepartmentDean {
        requestCounter++;
        requests[requestCounter] = DepartmentRequest({
            requestId: requestCounter,
            departmentAddress: msg.sender,
            itemName: _itemName,
            quantity: _quantity,
            priority: _priority,
            reason: _reason,
            timestamp: block.timestamp,
            exists: true
        });
        
        emit RequestCreated(requestCounter, msg.sender, _itemName, _quantity, _priority, block.timestamp);
    }
    
    function approveRequest(
        uint256 _requestId,
        bool _approved,
        string memory _reason
    ) external {
        require(requests[_requestId].exists, "Request does not exist");
        
        // Check if approver has the right role
        require(
            isStoresManager[msg.sender] || isProcurementOfficer[msg.sender] || isCFO[msg.sender],
            "Not authorized to approve requests"
        );
        
        requestApprovals[_requestId].push(Approval({
            approver: msg.sender,
            approved: _approved,
            reason: _reason,
            timestamp: block.timestamp
        }));
        
        emit RequestApproved(_requestId, msg.sender, _approved, _reason, block.timestamp);
    }
    
    // Stock management functions
    function adjustStock(
        string memory _itemName,
        int256 _quantityChange,
        string memory _reason
    ) external onlyStoresManager {
        emit StockAdjusted(_itemName, _quantityChange, _reason, block.timestamp);
    }
    
    function logDelivery(
        string memory _itemName,
        uint256 _quantity,
        string memory _supplier
    ) external onlyProcurementOfficer {
        emit DeliveryLogged(_itemName, _quantity, _supplier, block.timestamp);
    }
    
    function reportDamage(
        string memory _itemName,
        uint256 _quantity,
        string memory _description
    ) external {
        require(
            isDepartmentDean[msg.sender] || isProcurementOfficer[msg.sender],
            "Only Department Dean or Procurement Officer can report damage"
        );
        emit DamageReported(_itemName, _quantity, _description, block.timestamp);
    }
    
    function logRelocation(
        string memory _itemName,
        uint256 _quantity,
        string memory _fromLocation,
        string memory _toLocation
    ) external onlyStoresManager {
        emit RelocationLogged(_itemName, _quantity, _fromLocation, _toLocation, block.timestamp);
    }
    
    // Utility functions
    function getContractInfo() external view returns (string memory) {
        return "CBU Central Stores Manager Contract V3";
    }
    
    function getRequestApprovals(uint256 _requestId) external view returns (Approval[] memory) {
        return requestApprovals[_requestId];
    }
    
    function getRequestStatus(uint256 _requestId) external view returns (string memory) {
        if (!requests[_requestId].exists) return "Non-existent";
        
        Approval[] memory approvals = requestApprovals[_requestId];
        if (approvals.length == 0) return "Pending";
        
        for (uint i = 0; i < approvals.length; i++) {
            if (!approvals[i].approved) return "Rejected";
        }
        
        return approvals.length >= 3 ? "Approved" : "In Progress";
    }
}