from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional
import boto3
from botocore.exceptions import ClientError
import uuid
from datetime import datetime

from ..core.config import settings
from ..core.auth import get_password_hash, verify_password, create_access_token, get_current_user

router = APIRouter()

# DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name=settings.AWS_REGION)
users_table = dynamodb.Table('themisguard-users')

class UserRegistration(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    company: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class GoogleSSOData(BaseModel):
    email: EmailStr
    name: str
    google_id: str
    picture: Optional[str] = None

@router.post("/register")
async def register_user(user_data: UserRegistration):
    """Register a new user"""
    try:
        # Check if user already exists
        try:
            response = users_table.get_item(Key={"user_id": user_data.email})
            if response.get("Item"):
                raise HTTPException(
                    status_code=400,
                    detail="User with this email already exists"
                )
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceNotFoundException':
                raise HTTPException(status_code=500, detail="Database error")
        
        # Create new user
        user_id = str(uuid.uuid4())
        hashed_password = get_password_hash(user_data.password)
        
        user_item = {
            "user_id": user_id,
            "email": user_data.email,
            "password_hash": hashed_password,
            "profile": {
                "first_name": user_data.first_name,
                "last_name": user_data.last_name,
                "name": f"{user_data.first_name} {user_data.last_name}",
                "company": user_data.company
            },
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "email_verified": False,
            "plan_tier": "free",
            "status": "active"
        }
        
        # Store in DynamoDB
        users_table.put_item(Item=user_item)
        
        # Create access token
        token_data = {"sub": user_id, "email": user_data.email}
        access_token = create_access_token(token_data)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "user_id": user_id,
                "email": user_data.email,
                "profile": user_item["profile"],
                "plan_tier": "free"
            }
        }
        
    except ClientError as e:
        print(f"DynamoDB error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create user")
    except Exception as e:
        print(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@router.post("/login")
async def login_user(login_data: UserLogin):
    """Login user with email/password"""
    try:
        # Get user from DynamoDB (using email as lookup)
        response = users_table.scan(
            FilterExpression="email = :email",
            ExpressionAttributeValues={":email": login_data.email}
        )
        
        users = response.get("Items", [])
        if not users:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
        
        user = users[0]
        
        # Verify password
        if not verify_password(login_data.password, user["password_hash"]):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
        
        # Create access token
        token_data = {"sub": user["user_id"], "email": user["email"]}
        access_token = create_access_token(token_data)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "user_id": user["user_id"],
                "email": user["email"],
                "profile": user.get("profile", {}),
                "plan_tier": user.get("plan_tier", "free")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@router.post("/google-sso")
async def google_sso_login(google_data: GoogleSSOData):
    """Login/register user with Google SSO"""
    try:
        # Check if user exists
        response = users_table.scan(
            FilterExpression="email = :email",
            ExpressionAttributeValues={":email": google_data.email}
        )
        
        users = response.get("Items", [])
        
        if users:
            # Existing user - update Google ID if needed
            user = users[0]
            if user.get("google_id") != google_data.google_id:
                users_table.update_item(
                    Key={"user_id": user["user_id"]},
                    UpdateExpression="SET google_id = :google_id, updated_at = :updated_at",
                    ExpressionAttributeValues={
                        ":google_id": google_data.google_id,
                        ":updated_at": datetime.utcnow().isoformat()
                    }
                )
        else:
            # New user - create from Google data
            user_id = str(uuid.uuid4())
            name_parts = google_data.name.split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ""
            
            user = {
                "user_id": user_id,
                "email": google_data.email,
                "google_id": google_data.google_id,
                "profile": {
                    "first_name": first_name,
                    "last_name": last_name,
                    "name": google_data.name,
                    "picture": google_data.picture
                },
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "email_verified": True,  # Google accounts are pre-verified
                "plan_tier": "free",
                "status": "active"
            }
            
            users_table.put_item(Item=user)
        
        # Create access token
        token_data = {"sub": user["user_id"], "email": user["email"]}
        access_token = create_access_token(token_data)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "user_id": user["user_id"],
                "email": user["email"],
                "profile": user.get("profile", {}),
                "plan_tier": user.get("plan_tier", "free")
            }
        }
        
    except Exception as e:
        print(f"Google SSO error: {e}")
        raise HTTPException(status_code=500, detail="Google SSO failed")

@router.get("/verify")
async def verify_token(current_user: dict = Depends(get_current_user)):
    """Verify JWT token and return user info"""
    return {
        "user": {
            "user_id": current_user["user_id"],
            "email": current_user["email"],
            "profile": current_user.get("profile", {}),
            "plan_tier": current_user.get("plan_tier", "free")
        }
    }