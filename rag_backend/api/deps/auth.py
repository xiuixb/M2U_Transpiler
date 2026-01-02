from datetime import datetime, timedelta, timezone
import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from rag_backend.core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

# 配置日志
logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/user/login")


def create_access_token(data: dict, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    """创建JWT访问令牌"""
    try:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    except Exception as e:
        logger.error(f"创建访问令牌失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="令牌创建失败"
        )


async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """获取当前用户ID（JWT验证）"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 解码JWT令牌
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_name: str = payload.get("sub") # type: ignore
        
        if user_name is None:
            logger.warning("JWT令牌中缺少sub字段")
            raise credentials_exception
            
        # 验证令牌过期时间
        exp = payload.get("exp")
        if exp is None:
            logger.warning("JWT令牌中缺少exp字段")
            raise credentials_exception
            
        if datetime.now(timezone.utc).timestamp() > exp:
            logger.warning(f"JWT令牌已过期，用户: {user_name}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="令牌已过期"
            )
            
        logger.info(f"用户验证成功: {user_name}")
        return user_name
        
    except JWTError as e:
        logger.error(f"JWT验证失败: {e}")
        raise credentials_exception
    except Exception as e:
        logger.error(f"验证用户时发生未预期错误: {e}")
        raise credentials_exception


async def get_current_user_optional(token: str = Depends(oauth2_scheme)) -> str | None:
    """可选的用户验证（用于不需要强制登录的接口）"""
    try:
        return await get_current_user(token)
    except HTTPException:
        return None