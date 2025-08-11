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
    print(f"📝 User registration attempt: {user_data.email}")
    print(f"🏢 Company: {user_data.company}")
    print(f"👤 Name: {user_data.first_name} {user_data.last_name}")
    
    try:
        # Check if user already exists
        print(f"🔍 Checking if user exists: {user_data.email}")
        try:
            response = users_table.get_item(Key={"user_id": user_data.email})
            print(f"📊 DynamoDB response keys: {response.keys()}")
            if response.get("Item"):
                print(f"⚠️ User already exists: {user_data.email}")
                raise HTTPException(
                    status_code=400,
                    detail="User with this email already exists"
                )
            print(f"✅ User does not exist, proceeding with registration")
        except ClientError as e:
            print(f"❌ DynamoDB ClientError: {e.response['Error']['Code']} - {e.response['Error']['Message']}")
            if e.response['Error']['Code'] != 'ResourceNotFoundException':
                raise HTTPException(status_code=500, detail=f"Database error: {e.response['Error']['Message']}")
        
        # Create new user
        user_id = str(uuid.uuid4())
        print(f"🆔 Generated user ID: {user_id}")
        
        hashed_password = get_password_hash(user_data.password)
        print(f"🔐 Password hashed successfully")
        
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
        
        print(f"💾 Storing user in DynamoDB: {users_table.table_name}")
        print(f"📝 User item keys: {list(user_item.keys())}")
        
        # Store in DynamoDB
        users_table.put_item(Item=user_item)
        print(f"✅ User stored successfully in DynamoDB")
        
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
    print(f"🔑 Login attempt for: {login_data.email}")
    print(f"📊 Using table: {users_table.table_name}")
    print(f"🌍 AWS Region: {settings.AWS_REGION}")
    
    try:
        # Get user from DynamoDB (using email as lookup)
        print(f"🔍 Scanning DynamoDB for user: {login_data.email}")
        print(f"📊 Filter expression: email = :email")
        
        response = users_table.scan(
            FilterExpression="email = :email",
            ExpressionAttributeValues={":email": login_data.email}
        )
        
        print(f"📊 Scan response keys: {response.keys()}")
        print(f"📊 Scan count: {response.get('Count', 0)} items found")
        print(f"📊 Scanned count: {response.get('ScannedCount', 0)} items scanned")
        
        users = response.get("Items", [])
        if not users:
            print(f"❌ No user found with email: {login_data.email}")
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
        
        user = users[0]
        print(f"✅ User found: {user.get('user_id', 'unknown')}")
        print(f"📝 User keys: {list(user.keys())}")
        print(f"🔐 Has password hash: {'password_hash' in user}")
        
        # Verify password
        print(f"🔐 Verifying password...")
        if not verify_password(login_data.password, user["password_hash"]):
            print(f"❌ Password verification failed for: {login_data.email}")
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
        
        print(f"✅ Password verified successfully")
        
        # Create access token
        print(f"🎫 Creating access token...")
        token_data = {"sub": user["user_id"], "email": user["email"]}
        access_token = create_access_token(token_data)
        print(f"✅ Access token created")
        
        user_response = {
            "user_id": user["user_id"],
            "email": user["email"],
            "profile": user.get("profile", {}),
            "plan_tier": user.get("plan_tier", "free")
        }
        
        print(f"🎉 Login successful for: {login_data.email}")
        print(f"👤 Returning user data: {list(user_response.keys())}")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user_response
        }
        
    except HTTPException as http_ex:
        print(f"❌ HTTP Exception during login: {http_ex.detail}")
        raise
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']
        print(f"❌ DynamoDB ClientError during login: {error_code} - {error_msg}")
        print(f"📊 Full error response: {e.response}")
        raise HTTPException(status_code=500, detail=f"Database error: {error_code}")
    except Exception as e:
        print(f"❌ Unexpected login error: {type(e).__name__}: {str(e)}")
        print(f"📊 Exception details: {repr(e)}")
        raise HTTPException(status_code=500, detail="Login failed")

@router.post("/google-sso")
async def google_sso_login(google_data: GoogleSSOData):
    """Login/register user with Google SSO"""
    print(f"🔐 Google SSO login attempt for: {google_data.email}")
    print(f"🆔 Google ID: {google_data.google_id}")
    print(f"👤 Name: {google_data.name}")
    print(f"🖼️ Has picture: {bool(google_data.picture)}")
    
    try:
        # Check if user exists
        print(f"🔍 Checking if user exists: {google_data.email}")
        response = users_table.scan(
            FilterExpression="email = :email",
            ExpressionAttributeValues={":email": google_data.email}
        )
        
        print(f"📊 Scan response: {response.get('Count', 0)} items found")
        users = response.get("Items", [])
        
        if users:
            # Existing user - update Google ID if needed
            user = users[0]
            print(f"✅ Existing user found: {user.get('user_id')}")
            print(f"🔍 Current Google ID: {user.get('google_id')}")
            print(f"🔍 New Google ID: {google_data.google_id}")
            
            if user.get("google_id") != google_data.google_id:
                print(f"🔄 Updating Google ID for user")
                users_table.update_item(
                    Key={"user_id": user["user_id"]},
                    UpdateExpression="SET google_id = :google_id, updated_at = :updated_at",
                    ExpressionAttributeValues={
                        ":google_id": google_data.google_id,
                        ":updated_at": datetime.utcnow().isoformat()
                    }
                )
                print(f"✅ Google ID updated successfully")
            else:
                print(f"ℹ️ Google ID already up to date")
        else:
            # New user - create from Google data
            print(f"👤 Creating new user from Google data")
            user_id = str(uuid.uuid4())
            print(f"🆔 Generated user ID: {user_id}")
            
            name_parts = google_data.name.split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ""
            print(f"📝 Parsed name: {first_name} {last_name}")
            
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
            
            print(f"💾 Storing new user in DynamoDB")
            print(f"📝 User item keys: {list(user.keys())}")
            users_table.put_item(Item=user)
            print(f"✅ New user created successfully")
        
        # Create access token
        print(f"🎫 Creating access token for: {user['email']}")
        token_data = {"sub": user["user_id"], "email": user["email"]}
        access_token = create_access_token(token_data)
        print(f"✅ Access token created")
        
        user_response = {
            "user_id": user["user_id"],
            "email": user["email"],
            "profile": user.get("profile", {}),
            "plan_tier": user.get("plan_tier", "free")
        }
        
        print(f"🎉 Google SSO successful for: {google_data.email}")
        print(f"👤 Returning user data: {list(user_response.keys())}")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user_response
        }
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']
        print(f"❌ DynamoDB ClientError during Google SSO: {error_code} - {error_msg}")
        print(f"📊 Full error response: {e.response}")
        raise HTTPException(status_code=500, detail=f"Database error: {error_code}")
    except Exception as e:
        print(f"❌ Unexpected Google SSO error: {type(e).__name__}: {str(e)}")
        print(f"📊 Exception details: {repr(e)}")
        raise HTTPException(status_code=500, detail="Google SSO failed")

@router.get("/verify")
async def verify_token(current_user: dict = Depends(get_current_user)):
    """Verify JWT token and return user info"""
    print(f"🔍 Token verification request")
    print(f"👤 Current user ID: {current_user.get('user_id', 'unknown')}")
    print(f"📧 Current user email: {current_user.get('email', 'unknown')}")
    print(f"📝 User data keys: {list(current_user.keys())}")
    
    user_response = {
        "user_id": current_user["user_id"],
        "email": current_user["email"],
        "profile": current_user.get("profile", {}),
        "plan_tier": current_user.get("plan_tier", "free")
    }
    
    print(f"✅ Token verification successful")
    print(f"👤 Returning user data: {list(user_response.keys())}")
    
    return {"user": user_response}