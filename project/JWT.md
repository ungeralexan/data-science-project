# Jason Web Tokens (JWT)

References: 

- https://www.youtube.com/watch?v=Y2H3DXDeS3Q
- https://arielweinberger.medium.com/json-web-token-jwt-the-only-explanation-youll-ever-need-cf53f0822f50

---

There are two important concepts when a user wants to sign into an account:

1. Authentication
2. Authorization

## Authentication

Authentication is the process of identifying a user through their credentials. The user goes to the website, types in their email and password and gets access. 
At this point, the user is authenticated. After successful authentication, the user is issued a access token (Jason Web Token).
The access token is used for authorization.

## Authorization

Authorization is the process of ensuring that the user is permitted to access the resource / operation they're trying to access.  
The authorization part is where many websites use Jason Web Tokens. These are usually provided as a bearer token

## General Structure of JWT Standard

#### Example JWT:

<span style="color:red;">eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9</span>.<span style="color:pink;">eyJzdWIiOiIxZGZlZThkOC05OGE1LTQzMTQtYjRhZS1mYjU1YzRiMTg4NDUiLCJlbWFpbCI6ImFyaWVsQGNvZGluZ2x5LmlvIiwibmFtZSI6IkFyaWVsIFdlaW5iZXJnZXIiLCJyb2xlIjoiVVNFUiIsImlhdCI6MTU5ODYwODg0OCwiZXhwIjoxNTk4NjA5MTQ4fQ</span>.
<span style="color:lightblue;">oa3ziIZAoVFdn-97rweJAjjFn6a4ZSw7ogIHA74mGq0</span>

A JWT consists of three parts:
<span style="color:red;">HEADER</span>.
<span style="color:pink;">PAYLOAD</span>.
<span style="color:lightblue;">SIGNATURE</span>

#### HEADER:

Contains metadata about the token

```JSON
{
    "typ": "JWT", // Type of Token
    "alg":"HS256" // Algorithm used to create signature
}
```

#### PAYLOAD:

```JSON
{
    "iss": "oauth", // Issuer of token
    "sub": "userId", // Subject = User ID
    "exp": "1516237022", // Timestamp of when token expires
    "iat": "1516239022", // Timestamp of when token was issued
    "orgId": "someOrgId", // Organization ID
    "email": "my@email.com", // E-Mail
    "role": "ADMIN", // Access level
    "...": "..."
}
```

#### SIGNATURE:

When a JWT is issued to a user, the authenticating server needs to sign that token. That signature is a mechanism to ensure that the payload can be trusted. 
The signature is created by running a hashing function f() that uses a SECRET_KEY, the HEADER, and the PAYLOAD. Therefore, the signature is just a hash. The signature is included in the token itself.

f (SECRET_KEY HEADER PAYLOAD) = oa3ziIZAoVFdn-97rweJAjjFn6a4ZSw7ogIHA74mGq0

#### HOW DOES AUTHORIZATION WORK WITH JWT?

When a token is send to a server, it will take the header and the payload, run it through the exact same hashing function to produce an signature and compare that signature to the one provided by the user. 
If they match, the user is authorized. Otherwise, he is declined. 
Jason Web Tokens are not encrypted. They are encoded using Base64. Anyone can view and alter the tokens. However, when changing any part of the token (e.g. the payload), the signature changes which will result in the user being declined. 


## How does TUEVENT use JWT for Access Tokens?

### Example Login:

**Step 1: User Submits Login Form (Frontend)**

``` JAVASCRIPT
// AuthContext.tsx - login function
const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),  // { email: "user@example.com", password: "secret123" }
});
```

**Step 2: The backend creates the token**

```jwt.encode()``` does this:

1. Takes the payload dictionary
2. Converts it to JSON
3. Base64-encodes it (header + payload)
4. Creates a signature using JWT_SECRET_KEY and HS256 algorithm
5. Returns: "header.payload.signature"

``` PYTHON
# auth/utils.py - create_access_token()
def create_access_token(user_id: int) -> str:

    expire = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)  # 7 days
    
    payload = {
        "sub": str(user_id),        # "sub" = subject (who the token is about)
        "exp": expire,               # expiration timestamp
        "iat": datetime.now(...)     # "issued at" timestamp
    }

    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
```

The signature is the key (See further explanations above)! It's created like this:

```
signature = HMAC-SHA256(
    base64(header) + "." + base64(payload),
    JWT_SECRET_KEY
)
```

Only the backend knows the JWT_SECRET_KEY. It can be changed in the config.py file. 
Therefore, only the backend can create a valid signature and verify that a token wasn't tampered with.

**Step 3: Token Sent to Frontend**

``` PYTHON
# auth/routes.py - login endpoint
return TokenResponse( #TokenResponse is a Pydantic Model
    access_token = access_token,  # The JWT string
    token_type = "bearer",
    user=user_orm_to_response(user) #user_orm_to_response converts a UserORM instance to a Pydantic UserResponse model.
)
```

The Reponse looks like this:

``` JSON
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0MiIsImV4cCI6MTczMzQwMDAwMH0.xyz123",
    "token_type": "bearer",
    "user": { "user_id": 1, "email": "user@example.com", ... }
}
```

**Step 4: The Frontend Stores the Token in localStorage**

```JAVASCRIPT
// AuthContext.tsx - after successful login
const authResponse: AuthResponse = await response.json();

// Store in browser's localStorage (persists across page reloads)
localStorage.setItem(TOKEN_KEY, authResponse.access_token);

// Also keep in React state for quick access
setToken(authResponse.access_token);
setUser(authResponse.user);
```

### Example Using the Token:

If a user has logged in, the access token is stored in the localStorage and now he wants to change his interest. 

**Step 1: The Frontend Sends Token with Requests**

The updateUser function executes this code:

``` JAVASCRIPT
// AuthContext.tsx
const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
    method: 'PUT',  // PUT = update existing resource

    headers: {
        'Content-Type': 'application/json',      // We're sending JSON
        'Authorization': `Bearer ${token}`,       // Prove who we are!
    },

    body: JSON.stringify(data),  // The fields to update
});
```

The HTTP Request that is send to the backend looks like this: 

```
PUT /api/auth/me HTTP/1.1
Host: API_BASE_URL
Content-Type: application/json
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0MiIsImV4cCI6MTczMzQwMDAwMH0.xyz123

{
    "interest_keys": ["Technology", "Music"],
    "interest_text": "I love AI and concerts"
}
```

**Step 2:**

FastAPI router sends the request to the update_me() function. FastAPI further automatically validates the JSON body against ```UserUpdate``` model defined in ```models.py```. 
It also calls the ```get_current_user()``` function in ```utils.py``` to get the user as ```UserORM``` model and save it in the variable ```current_user```. 

``` PYTHON
# auth/routes.py
@auth_router.put("/me", response_model=UserResponse)
async def update_me(user_update: UserUpdate, current_user: UserORM = Depends(get_current_user)):

    with SessionLocal() as db:

        #Retrieve the user extracted with get_current_user() function from database
        user = db.query(UserORM).filter(UserORM.user_id == current_user.user_id).first() 

        ...

        #Update values
        user.interest_keys = user_update.interest_keys
        user.interest_text = user_update.interest_text

        ...

        #Make changes in database
        db.commit()
        db.refresh(user)

        #Returns pydantic model of UserORM
        return user_orm_to_response(user)

```

update_me() retrieves user information from the database by calling get_current_user(). The get_current_user() function requires credentials which it extracts
from the HTTP request via the HTTPBearer function.

HTTP Bearer function:

- Looks for the ```Authorization``` header in incoming requests.
- Expects the format ```Bearer <token>```
- Parses it and extracts just the token part (After "Bearer", Example: )
- Returns an HTTPAuthorizationCredentials object

``` PYTHON
# auth/utils.py

# Security Scheme for FastAPI dependencies. 
# The HTTPBearer() function extracts "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0MiIsImV4cCI6MTczMzQwMDAwMH0.xyz123" from the HTTP request.
security = HTTPBearer(auto_error=False)

#The 
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserORM:

    # credentials.credentials contains just the token
    token = credentials.credentials

    # Decode and validate token with decode_access_token() function defined in utils.py
    # The function returns the user id
    user_id = decode_access_token(token)

    # decode_access_token() will return None if token is expired or invalid. 
    if user_id is None:
        raise HTTPException(status_code = 401, detail="Invalid or expired token")

    ...
```

The magic happens in the ```jwt.decode()``` function. Here the signature of the token is recalculated and checked for validity.

```jwt.decode()``` does this:

1. Splits the token into header, payload, and signature
2. Recalculates the signature using JWT_SECREC_KEY
3. Compares calculated signature with the one in the token
4. If they match -> Token is valid
5. Checks if "exp" (expiration) has passed
6. Returns the payload as a dictionary

``` PYTHON
# auth/utils.py
def decode_access_token(token: str) -> Optional[int]:

    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

    return int(payload.get("sub")) #Returns the user_id which is saved in the variable "sub" (See explanations above)

```

**Step 3:**

After the changes have been made in the database, the ```update_me()``` functions ```return user_orm_to_response(user)``` which simply converts the ```UserORM``` into a pydantic model.
FastAPI sends the Response JSON to the Frontend:

``` JSON
{
    "user_id": 42,
    ...
    "interest_keys": ["Technology", "Music"],
    "interest_text": "I love AI and concerts",
    ...
}
```

The Frontend receives the response and triggers a re-render of any component using the ```useAuth()``` function. 


