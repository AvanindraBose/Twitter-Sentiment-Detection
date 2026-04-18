import logging
from fastapi import APIRouter,HTTPException,status,Depends,Request
from fastapi.responses import JSONResponse
from backend.core.security import create_access_tokens, create_refresh_tokens,verify_refresh_token,verify_password,hash_password,hash_refresh_token,verify_hashed_refresh_token
from backend.schema.users_auth import UserCreate,UserLogin
from backend.core.dependencies import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi.concurrency import run_in_threadpool
from backend.db.models.users import User
from backend.db.models.refresh_token import RefreshToken
from datetime import datetime, timezone
from backend.core.rate_limiter import login_rate_limiter , refresh_rate_limiter

router = APIRouter(prefix="/auth",tags=["Auth"])
logger = logging.getLogger(__name__)

@router.post("/signup")
async def signup(user_input:UserCreate , db:AsyncSession = Depends(get_db)):

    stmt = select(User).where(User.email == user_input.email)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "User Already Exists"
        )
    # CPU Based Operation
    password_hash = await run_in_threadpool(
        hash_password, user_input.password
    )
    new_user = User(
        username = user_input.username,
        email = user_input.email,
        password_hash = password_hash
    )
    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
    except Exception:
        await db.rollback()
        logger.error(
            "Signup failed due to DB error",
            exc_info=True,
            extra = {"email":user_input.email}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = "Could not create user , please try again"
        )
    
    return {
        "message":"User Created Successfully"
    }

@router.post("/login")
async def login(request:Request , user_input:UserLogin , db:AsyncSession = Depends(get_db) , _ = Depends(login_rate_limiter)):

    stmt = select(User).where(User.email == user_input.email)
    result = await db.execute(stmt)
    db_user = result.scalar_one_or_none()

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid credentials"
        )
    password_valid = await run_in_threadpool(
        verify_password,
        user_input.password,
        db_user.password_hash,
    )

    if not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid credentials"
        )
    
    access_token = create_access_tokens(str(db_user.id))
    refresh_token,expires_at = create_refresh_tokens(str(db_user.id))
    
    hashed_refresh_token = await run_in_threadpool(
        hash_refresh_token, refresh_token
    )
    stmt = select(RefreshToken).where(
        RefreshToken.user_id == db_user.id
    )
    result = await db.execute(stmt)
    existing_token = result.scalar_one_or_none()
    
    try:
        if existing_token:
            existing_token.token = hashed_refresh_token
            existing_token.expires_at = expires_at
        else :
            db.add(
                RefreshToken(
                    user_id=db_user.id,
                    token=hashed_refresh_token,
                    expires_at=expires_at,
                )
            )
            
        await db.commit()
    except Exception:
        await db.rollback()
        logger.error(
            "Login Token Persistance Failed",
            exc_info= True,
            extra={"user_id":db_user.id}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = "Could not create tokens , please try again"
        )

    response = JSONResponse(
        content= {
            "access_token" : access_token,
            "token_type" : "bearer"
        }
    )
    max_age = int((expires_at - datetime.now(timezone.utc)).total_seconds())
    response.set_cookie(
        key = "refresh_token",
        value = refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        path = "/",
        max_age = max_age
    )
    return response


@router.post("/refresh")
async def refresh_access_tokens(request:Request, db:AsyncSession = Depends(get_db), _= Depends(refresh_rate_limiter)):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
     raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Refresh token missing"
    )
    payload = verify_refresh_token(refresh_token)
# Using Nested Dependecies
    if payload is None :
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid or expired refresh token"
        )
    
    user_id = payload["sub"]
    # refresh_rate_limiter(user_id)

    try:
        # BEGIN TRANSACTION
        stmt = (
            select(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .with_for_update()
            # It does row_locking
        )

        result = await db.execute(stmt)
        db_token = result.scalar_one_or_none()

        if not db_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not found. Please login again",
            )
        
        is_valid_token = await run_in_threadpool(
            verify_hashed_refresh_token,
            refresh_token,
            db_token.token
        )

        if not is_valid_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        if db_token.expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired",
            )

        # ROTATE TOKENS
        new_access_token = create_access_tokens(user_id)
        new_refresh_token, expires_at = create_refresh_tokens(user_id)
        hash_new_token = await run_in_threadpool(
            hash_refresh_token,
            new_refresh_token
        )
        db_token.token = hash_new_token
        db_token.expires_at = expires_at

        await db.commit()

        logger.info(
            "Tokens refreshed successfully",
            extra={"user_id": user_id}
        )

    except HTTPException:
        await db.rollback()
        raise

    except Exception:
        await db.rollback()
        logger.error(
            "Refresh token rotation failed",
            exc_info=True,
            extra={"user_id": user_id},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not refresh tokens",
        )

    response = JSONResponse(
        content={
            "access_token": new_access_token,
            "token_type": "bearer",
        }
    )

    max_age = int((expires_at - datetime.now(timezone.utc)).total_seconds())

    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
        max_age=max_age,
    )

    return response

@router.post("/logout")
async def logout(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    refresh_token = request.cookies.get("refresh_token")

    if refresh_token:
        payload = verify_refresh_token(refresh_token)
        
        if payload:
            user_id = payload["sub"]
            
            try:
                # Find and delete refresh token
                stmt = select(RefreshToken).where(
                    RefreshToken.user_id == user_id
                )
                result = await db.execute(stmt)
                db_token = result.scalar_one_or_none()
                
                if db_token:
                    await db.delete(db_token)
                    await db.commit()
                    
                    logger.info(
                        "User logged out - token deleted",
                        extra={"user_id": user_id}
                    )
                else:
                    logger.info(
                        "User logged out - token already gone",
                        extra={"user_id": user_id}
                    )
                    
            except Exception:
                await db.rollback()
                logger.exception(
                    "Logout DB operation failed - continuing anyway",
                    extra={"user_id": user_id}
                )
                # Don't raise - still clear cookie and return success
        else:
            logger.info("Logout with invalid/expired token - clearing cookie")
    else:
        logger.info("Logout with no refresh token - clearing cookie")
    
    # Always clear the cookie and return success (idempotent)
    response = JSONResponse(
        content={"message": "Logged out successfully"}
    )
    
    response.delete_cookie(
        key="refresh_token",
        path="/",
        secure=False,
        httponly=True,
        samesite="lax"
    )
    
    return response
