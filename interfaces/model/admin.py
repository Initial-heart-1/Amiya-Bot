from pydantic import BaseModel
from interfaces.model import SearchBase, Pagination


class EditPassword(BaseModel):
    newPassword: str
    newPasswordConfirm: str
    password: str


class AdminModel(BaseModel):
    user_id: str


class AdminTableSearch(SearchBase):
    active: str = None
    user_id: str = None


class AdminTable(Pagination):
    search: AdminTableSearch


class AdminState(BaseModel):
    user_id: str
    active: int


class RoleTableSearch(SearchBase):
    active: str = None
    role_name: str = None


class RoleModel(BaseModel):
    id: int
    role_name: str
    access_path: str
    active: int


class RoleTable(Pagination):
    search: RoleTableSearch


class RoleState(BaseModel):
    role_id: str
    active: int
