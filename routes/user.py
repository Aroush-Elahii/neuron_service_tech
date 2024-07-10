from fastapi import APIRouter
from fastapi.responses import JSONResponse
from database.models.models import User
from database.config.connection import collection_users
from database.schema.schemas import list_serial
from database.schema.schema import *
from bson import ObjectId
from utils import *
user_router = APIRouter()

@user_router.get("/get_users")
async def get_user():
    users = list_serial(collection_users.find())
    return users 

# POST request 
@user_router.post("/register", tags=["User"])
async def register_user(user: UserCreate):
    deleted_user = collection_users.find_one({"email": user.email, "is_deleted": True})
    if deleted_user:
        collection_users.update_one(
            {"email": user.email},  
            {"$set": {
                "first_name": user.first_name,
                "last_name": user.last_name,
                "username": user.username,
                "password": user.password,
                "is_deleted": False,
                "updated_on": datetime.utcnow()
            }}
        )
        updated_user = collection_users.find_one({"email": user.email})
        user_dict = {
            "id": str(updated_user["_id"]),
            "username": updated_user["username"],
            "email": updated_user["email"],
            "first_name": updated_user["first_name"],
            "last_name": updated_user["last_name"],
            "token": create_token(data={"sub": updated_user["username"]})
        }
        return JSONResponse(
            content={"success": True, "message": "User registered successfully!", "user": user_dict},
            status_code=200
        )

    existing_user = collection_users.find_one({"$or": [{"email": user.email}, {"username": user.username}]})
    if existing_user:
        if existing_user["email"] == user.email:
            return JSONResponse(
                content={"success": False, "message": "User with email already registered!"},
                status_code=409
            )
        if existing_user["username"] == user.username:
            return JSONResponse(
                content={"success": False, "message": "User with username already exists!"},
                status_code=409
            )

    new_user = dict(user)
    new_user['is_deleted'] = False
    new_user['added_on'] = datetime.utcnow()  # Set added_on field
    new_user['updated_on'] = datetime.utcnow()  # Set updated_on field
    result = collection_users.insert_one(new_user)
    new_user["_id"] = result.inserted_id

    collection_users.update_one({"_id": new_user["_id"]}, {"$set": {"otp": ""}})  # Assuming 'otp' field is required but can be empty

    user_dict = {
        "id": str(new_user["_id"]),
        "username": new_user["username"],
        "email": new_user["email"],
        "first_name": new_user["first_name"],
        "last_name": new_user["last_name"],
        "token": create_token(data={"sub": new_user["username"]})
    }

    return JSONResponse(
        content={"success": True, "message": "User registered successfully", "user": user_dict},
        status_code=200
    )

@user_router.post("/login", tags=["User"])
def user_login(user_data: UserLogin):
    user = authenticate_user(user_data.email, user_data.password)
    if user is None:
        response = {
            "success": False,
            "message": "Invalid Credentials passed!"
        }
        return JSONResponse(
            content=response,
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    else:
        user_dict = {
            "id": str(user["_id"]),
            "username": user["username"],
            "email": user["email"],
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "token": create_token(data={"sub": user["username"]})
        }

        response = {
            "success": True,
            "message": "User login successfully",
            "user": user_dict
        }

        return JSONResponse(
            content=response,
            status_code=status.HTTP_200_OK
        )
    
@user_router.post("/social_auth", tags=["User"])
def social_authentication(user: SocialAuth):
    if user.type != "apple":
        present_user = collection_users.find_one({"username": user.username, "email": user.email, "is_deleted": False})
        if present_user:
            user_dict = {
                "id": str(present_user["_id"]),
                "username": present_user["username"],
                "email": present_user["email"],
                "first_name": present_user["first_name"],
                "last_name": present_user["last_name"],
                "profile_url": present_user.get("profile_url", ""),
                "type": user.type,
                "token": create_token(data={"sub": present_user["username"]})
            }

            data = {
                "success": True,
                "message": "User Login successful!",
                "user": user_dict
            }

            return JSONResponse(
                content=data,
                status_code=status.HTTP_200_OK
            )

    if user.type == "google":
        try:
            deleted_user = collection_users.find_one({"email": user.email, "is_deleted": True})
            if deleted_user:
                collection_users.update_one(
                    {"email": user.email},
                    {"$set": {"is_deleted": False}}
                )

                updated_user = collection_users.find_one({"email": user.email})
                user_dict = {
                    "id": str(updated_user["_id"]),
                    "username": updated_user["username"],
                    "email": updated_user["email"],
                    "first_name": updated_user["first_name"],
                    "last_name": updated_user["last_name"],
                    "profile_url": updated_user.get("profile_url", ""),
                    "type": "simple",
                    "token": create_token(data={"sub": updated_user["username"]})
                }

                response = {
                    "success": True,
                    "message": "User registered successfully!",
                    "user": user_dict,
                }

                return JSONResponse(
                    content=response,
                    status_code=status.HTTP_200_OK
                )
        except Exception as e:
            return JSONResponse(
                content={
                    "success": False,
                    "message": f"Unable to process the user with email {user.email}!",
                    "exception": str(e)
                },
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        try:
            present_user = collection_users.find_one(
                {"$or": [{"username": user.username}, {"email": user.email}]}
            )
            if present_user:
                return JSONResponse(
                    content={
                        "success": False,
                        "message": "User with provided email/username already exists!"
                    },
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            new_user = {
                "first_name": user.first_name,
                "last_name": user.last_name,
                "username": user.username,
                "email": user.email,
                "password": user.password,  # Make sure to hash this password before storing
                "profile_url": user.profile_url,
                "is_deleted": False,
                "added_on": datetime.utcnow(),
                "updated_on": datetime.utcnow()
            }
            result = collection_users.insert_one(new_user)
            new_user["_id"] = result.inserted_id

            user_dict = {
                "id": str(new_user["_id"]),
                "username": new_user["username"],
                "email": new_user["email"],
                "first_name": new_user["first_name"],
                "last_name": new_user["last_name"],
                "profile_url": new_user.get("profile_url", ""),
                "type": user.type,
                "token": create_token(data={"sub": new_user["username"]})
            }

            data = {
                "success": True,
                "message": "User registered successfully",
                "user": user_dict
            }

            return JSONResponse(
                content=data,
                status_code=status.HTTP_200_OK
            )

        except Exception as e:
            data = {
                "success": False,
                "message": f"User already exists! {str(e)}"
            }
            return JSONResponse(
                content=data,
                status_code=status.HTTP_400_BAD_REQUEST
            )

    elif user.type == "apple":
        identity_user = collection_users.find_one({"unique_key": user.unique_key})
        if identity_user:
            user_dict = {
                "id": str(identity_user["_id"]),
                "username": identity_user["username"],
                "email": identity_user["email"],
                "first_name": identity_user["first_name"],
                "last_name": identity_user["last_name"],
                "profile_url": identity_user.get("profile_url", ""),
                "type": user.type,
                "token": create_token(data={"sub": identity_user["username"]})
            }

            data = {
                "success": True,
                "message": "User Login successful!",
                "user": user_dict
            }

            return JSONResponse(
                content=data,
                status_code=status.HTTP_200_OK
            )

        try:
            if not user.email or not user.username:
                return JSONResponse(
                    content={
                        "success": False,
                        "message": "Cannot register a new user without email and username!"
                    },
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            random_password = generate_password()
            print("Random Password:", random_password)

            new_user = {
                "first_name": user.first_name,
                "last_name": user.last_name,
                "username": user.username,
                "email": user.email,
                "unique_key": user.unique_key,
                "password": "",  # Password can be set to random_password if needed
                "is_deleted": False,
                "added_on": datetime.utcnow(),
                "updated_on": datetime.utcnow()
            }
            result = collection_users.insert_one(new_user)
            new_user["_id"] = result.inserted_id

            user_dict = {
                "id": str(new_user["_id"]),
                "username": new_user["username"],
                "email": new_user["email"],
                "first_name": new_user["first_name"],
                "last_name": new_user["last_name"],

                "token": create_token(data={"sub": new_user["username"]})
            }

            data = {
                "success": True,
                "message": "User registered successfully",
                "user": user_dict
            }

            return JSONResponse(
                content=data,
                status_code=status.HTTP_200_OK
            )

        except Exception as e:
            data = {
                "success": False,
                "message": f"User already exists! {str(e)}"
            }

            return JSONResponse(
                content=data,
                status_code=status.HTTP_400_BAD_REQUEST
            )

    else:
        data = {
            "success": False,
            "message": "User registration failed!"
        }

        return JSONResponse(
            content=data,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
# Delete User 

@user_router.delete("/delete", tags=["User"])
async def user_delete(user: UserDelete, current_user: Dict = Depends(get_current_user)):
    if not current_user:
        data = {
            "success": False,
            "message": "User not authenticated!"
        }
        return JSONResponse(
            content=data,
            status_code=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Check if the user is soft deleted
        deleted_user = collection_users.find_one({"email": user.email, "is_deleted": True})
        if deleted_user:
            return JSONResponse(
                content={
                    "success": False,
                    "message": f"User with email '{user.email}' does not exist!"
                },
                status_code=status.HTTP_400_BAD_REQUEST
            )
    except Exception as e:
        return JSONResponse(
            content={
                "success": False,
                "message": "User not found!",
                "exception": "Exception while deleting user\n" + str(e)
            },
            status_code=status.HTTP_404_NOT_FOUND
        )

    user_id = current_user["user_id"]
    db_user = collection_users.find_one({"_id": ObjectId(user_id), "email": user.email, "password": user.password})

    if not db_user:
        response = {
            "success": False,
            "message": f"User with email '{user.email}' does not exist!"
        }
        return JSONResponse(
            content=response,
            status_code=status.HTTP_404_NOT_FOUND
        )

    collection_users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"is_deleted": True}}
    )

    response = {
        "success": True,
        "message": "User and related information deleted successfully!",
        "data": str(user_id)
    }

    return JSONResponse(
        content=response,
        status_code=status.HTTP_200_OK
    )
