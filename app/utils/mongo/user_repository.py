from auth_lib.interfaces import DatabaseInterface
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional, Dict, Any
import hashlib
from bson import ObjectId
from typing import List

class MongoUserRepository(DatabaseInterface):
    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        self.collection = self.db.users
    
    def _convert_mongo_doc(self, doc: Dict) -> Dict[str, Any]:
        if doc and "_id" in doc:
            doc["_id"] = str(doc["_id"])             
        return doc
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            obj_id = ObjectId(user_id)
        except Exception:
            return None
        doc = await self.collection.find_one({"_id": obj_id})
        return self._convert_mongo_doc(doc) if doc else None
    
    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        doc = await self.collection.find_one({"username": username})
        return self._convert_mongo_doc(doc) if doc else None
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        email_hash = hashlib.sha256(email.lower().encode()).hexdigest()
        doc = await self.collection.find_one({"email": email})
        return self._convert_mongo_doc(doc) if doc else None
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        result = await self.collection.insert_one(user_data.copy())
        created_doc = await self.collection.find_one({"_id": result.inserted_id})
        return self._convert_mongo_doc(created_doc)
    
    async def update_user(self, user_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not update_data:
            return await self.get_user_by_id(user_id)
        
        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(user_id)},
            {"$set": update_data},
            return_document=True
        )
        return self._convert_mongo_doc(result) if result else None
    
    async def delete_user(self, user_id: str) -> bool:
        result = await self.collection.delete_one({"_id": ObjectId(user_id)})
        return result.deleted_count > 0

    # TODO : Add list users by role in the auth library
    async def list_users_by_roles(self, roles: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch all users with roles in the given list.
        Returns converted documents with _id as string.
        """
        cursor = self.collection.find({"role": {"$in": roles}})
        users = []
        async for doc in cursor:
            users.append(self._convert_mongo_doc(doc))
        return users