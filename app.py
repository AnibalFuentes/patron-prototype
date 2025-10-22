# app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
import uuid
import copy

app = FastAPI(title="Prototype-based MultiCloud Provisioner (demo)")

# --- Pydantic models (request/response) ---
class NetworkSpec(BaseModel):
    region: str
    public_ip: Optional[bool] = False
    firewall_rules: Optional[List[str]] = []

class StorageSpec(BaseModel):
    size_gb: int
    iops: Optional[int] = None
    encrypted: Optional[bool] = False

class VMSpec(BaseModel):
    provider: str
    template_key: str  # which template to clone (ej: "aws-standard", "gcp-memopt")
    name: Optional[str] = None
    overrides: Optional[Dict[str, Any]] = Field(default_factory=dict)
    network_overrides: Optional[Dict[str, Any]] = Field(default_factory=dict)
    storage_overrides: Optional[Dict[str, Any]] = Field(default_factory=dict)

# --- Prototype classes ---
class Prototype:
    def clone(self):
        raise NotImplementedError

class VMPrototype(Prototype):
    def __init__(self, provider: str, name: str, vcpus: int, memory_gb: int, disk_gb:int, network_id: Optional[str]=None, storage_id: Optional[str]=None):
        self.id = str(uuid.uuid4())
        self.provider = provider
        self.name = name
        self.vcpus = vcpus
        self.memory_gb = memory_gb
        self.disk_gb = disk_gb
        self.network_id = network_id
        self.storage_id = storage_id

    def clone(self):
        # deep copy to isolate nested structures if exist
        new = copy.deepcopy(self)
        new.id = str(uuid.uuid4())
        return new

    def apply_overrides(self, overrides: Dict[str, Any]):
        for k, v in overrides.items():
            if hasattr(self, k):
                setattr(self, k, v)

class NetworkPrototype(Prototype):
    def __init__(self, provider: str, region: str, public_ip: bool=False, firewall_rules: Optional[List[str]]=None):
        self.id = str(uuid.uuid4())
        self.provider = provider
        self.region = region
        self.public_ip = public_ip
        self.firewall_rules = firewall_rules or []

    def clone(self):
        new = copy.deepcopy(self)
        new.id = str(uuid.uuid4())
        return new

    def apply_overrides(self, overrides: Dict[str, Any]):
        for k, v in overrides.items():
            if hasattr(self, k):
                setattr(self, k, v)

class StoragePrototype(Prototype):
    def __init__(self, provider: str, size_gb:int, iops: Optional[int]=None, encrypted: bool=False):
        self.id = str(uuid.uuid4())
        self.provider = provider
        self.size_gb = size_gb
        self.iops = iops
        self.encrypted = encrypted

    def clone(self):
        new = copy.deepcopy(self)
        new.id = str(uuid.uuid4())
        return new

    def apply_overrides(self, overrides: Dict[str, Any]):
        for k, v in overrides.items():
            if hasattr(self, k):
                setattr(self, k, v)

# --- Prototype Registry (in-memory) ---
class PrototypeRegistry:
    def __init__(self):
        self.vm_templates: Dict[str, VMPrototype] = {}
        self.net_templates: Dict[str, NetworkPrototype] = {}
        self.storage_templates: Dict[str, StoragePrototype] = {}

    def register_vm(self, key: str, proto: VMPrototype):
        self.vm_templates[key] = proto

    def get_vm_clone(self, key: str) -> VMPrototype:
        if key not in self.vm_templates:
            raise KeyError(key)
        return self.vm_templates[key].clone()

    def register_net(self, key: str, proto: NetworkPrototype):
        self.net_templates[key] = proto

    def get_net_clone(self, key: str) -> NetworkPrototype:
        if key not in self.net_templates:
            raise KeyError(key)
        return self.net_templates[key].clone()

    def register_storage(self, key: str, proto: StoragePrototype):
        self.storage_templates[key] = proto

    def get_storage_clone(self, key: str) -> StoragePrototype:
        if key not in self.storage_templates:
            raise KeyError(key)
        return self.storage_templates[key].clone()

registry = PrototypeRegistry()

# --- Seed some templates (ejemplos por proveedor y flavor) ---
def seed_templates():
    # AWS standard
    registry.register_vm("aws-standard", VMPrototype(provider="aws", name="aws-standard", vcpus=2, memory_gb=4, disk_gb=50))
    registry.register_net("aws-standard-net", NetworkPrototype(provider="aws", region="us-east-1", public_ip=True, firewall_rules=["SSH","HTTP"]))
    registry.register_storage("aws-standard-store", StoragePrototype(provider="aws", size_gb=50, iops=100, encrypted=True))

    # GCP memory optimized
    registry.register_vm("gcp-memopt", VMPrototype(provider="gcp", name="gcp-memopt", vcpus=4, memory_gb=32, disk_gb=100))
    registry.register_net("gcp-memopt-net", NetworkPrototype(provider="gcp", region="us-central1", public_ip=False, firewall_rules=["SSH"]))
    registry.register_storage("gcp-memopt-store", StoragePrototype(provider="gcp", size_gb=100, iops=300, encrypted=False))

seed_templates()

# --- In-memory "provisioned" store (demo) ---
provisioned = {
    "vms": [],
    "networks": [],
    "storages": []
}

# --- Helper: validate provider coherence ---
def validate_provider_coherence(provider, net: NetworkPrototype, storage: StoragePrototype):
    if net.provider != provider or storage.provider != provider:
        raise ValueError("Proveedor incoherente entre VM, Network y Storage")

# --- Endpoint: clone template and "provision" (demo) ---
@app.post("/provision", status_code=201)
def provision_vm(spec: VMSpec):
    try:
        # get vm clone
        vm_clone = registry.get_vm_clone(spec.template_key)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"VM template {spec.template_key} not found")

    # decide network & storage template keys (naming simple: template_key-net, -store)
    net_key = f"{spec.template_key}-net"
    store_key = f"{spec.template_key}-store"
    try:
        net_clone = registry.get_net_clone(net_key)
        store_clone = registry.get_storage_clone(store_key)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=f"Associated template not found: {e}")

    # apply overrides
    if spec.overrides:
        vm_clone.apply_overrides(spec.overrides)
    if spec.network_overrides:
        net_clone.apply_overrides(spec.network_overrides)
    if spec.storage_overrides:
        store_clone.apply_overrides(spec.storage_overrides)

    # simple coherence validation
    try:
        validate_provider_coherence(vm_clone.provider, net_clone, store_clone)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # optionally set name
    if spec.name:
        vm_clone.name = spec.name

    # "provision" -> in real app, aquí llamarías a las fábricas/SDK provider para crear recursos.
    provisioned["networks"].append(net_clone.__dict__)
    provisioned["storages"].append(store_clone.__dict__)
    provisioned["vms"].append(vm_clone.__dict__)

    return {
        "status": "provisioned",
        "vm": vm_clone.__dict__,
        "network": net_clone.__dict__,
        "storage": store_clone.__dict__
    }

@app.get("/provisioned")
def list_provisioned():
    return provisioned

