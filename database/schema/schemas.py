# serializer 

def individual_serial(user) -> dict:
    return {
        "id" : str(user["_id"]),
        "first_name" : str(user["first_name"]),
        "last_name" : str(user["last_name"]),
        "email" : str(user["email"]),
        "username" : str(user["username"]),
        "password" : str(user["password"]),
        "otp" : str(user["otp"]),
    }

# deserializer 
def list_serial(users) -> list:
    return(individual_serial(user) for user in users)