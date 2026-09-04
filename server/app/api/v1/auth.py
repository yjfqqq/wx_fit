import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import create_access_token
from app.models.user import Goal, User, UserProfile
from app.schemas.auth import GoalIn, GoalOut, LoginIn, LoginOut, ProfileIn, ProfileOut
from app.services.wechat import WeChatLoginError, code2session

router = APIRouter(prefix="/auth", tags=["认证"])

# 允许的头像图片类型与文件大小上限（2MB）
_ALLOWED_AVATAR_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
_MAX_AVATAR_BYTES = 2 * 1024 * 1024


@router.post(
    "/test-login",
    response_model=LoginOut,
    summary="[DEBUG] 测试登录：真实微信登录不可用时供冒烟测试使用",
)
def test_login(db: Session = Depends(get_db)):
    """DEBUG 模式专用：用固定 openid 登录，保证业务测试链路不受真实登录影响。"""
    if not settings.DEBUG:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "仅 DEBUG 模式可用")
    openid = "test_openid_smoke"
    user = db.scalar(select(User).where(User.openid == openid))
    if user is None:
        user = User(openid=openid, nickname="冒烟测试用户")
        db.add(user)
        db.flush()
        db.add(UserProfile(user_id=user.id))
        db.add(Goal(user_id=user.id))
        db.commit()
        db.refresh(user)
    return LoginOut(token=create_access_token(user.id), is_new=False, user_id=user.id)


@router.post("/login", response_model=LoginOut, summary="微信小程序静默登录")
async def login(body: LoginIn, request: Request, db: Session = Depends(get_db)):
    # 微信云托管场景：小程序经 callContainer/安全网关调用时，网关会注入 x-wx-openid，
    # 此时无需再外呼 jscode2session（也绕开了容器无公网出口的问题）
    wx_openid = request.headers.get("x-wx-openid")
    if wx_openid:
        openid = wx_openid
    else:
        try:
            openid = await code2session(body.code)
        except WeChatLoginError as e:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))

    user = db.scalar(select(User).where(User.openid == openid))
    is_new = user is None
    if is_new:
        user = User(openid=openid, nickname=body.nickname or "运动达人")
        db.add(user)
        db.flush()
        db.add(UserProfile(user_id=user.id))
        db.add(Goal(user_id=user.id))
        db.commit()
        db.refresh(user)

    token = create_access_token(user.id)
    return LoginOut(token=token, is_new=is_new, user_id=user.id)


@router.post(
    "/avatar",
    response_model=ProfileOut,
    summary="上传微信头像并更新资料",
)
def upload_avatar(
    file: UploadFile,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ext = _ALLOWED_AVATAR_TYPES.get(file.content_type or "")
    if ext is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "头像仅支持 jpg / png / webp 格式"
        )
    data = file.file.read()
    if len(data) > _MAX_AVATAR_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "头像不能超过 2MB")

    # 目录：{UPLOAD_DIR}/avatars，文件名用用户 id + 时间戳防缓存
    avatars_dir = os.path.join(settings.UPLOAD_DIR, "avatars")
    os.makedirs(avatars_dir, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    filename = f"u{user.id}_{ts}{ext}"
    file_path = os.path.join(avatars_dir, filename)
    with open(file_path, "wb") as f:
        f.write(data)

    # 更新库中头像地址（存相对路径，前端拼自己的 BASE_URL）
    user.avatar_url = f"{settings.AVATAR_URL_PREFIX}/{filename}"
    db.commit()

    profile = db.scalar(select(UserProfile).where(UserProfile.user_id == user.id))
    return ProfileOut(
        id=user.id,
        openid=user.openid,
        nickname=user.nickname,
        avatar_url=user.avatar_url,
        gender=profile.gender if profile else 0,
        birthday=profile.birthday if profile else None,
        height_cm=profile.height_cm if profile else None,
        activity_level=profile.activity_level if profile else 1,
    )


@router.get("/me", response_model=ProfileOut, summary="当前用户资料")
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.scalar(select(UserProfile).where(UserProfile.user_id == user.id))
    if profile is None:
        profile = UserProfile(user_id=user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return ProfileOut(
        id=user.id,
        openid=user.openid,
        nickname=user.nickname,
        avatar_url=user.avatar_url,
        gender=profile.gender,
        birthday=profile.birthday,
        height_cm=profile.height_cm,
        activity_level=profile.activity_level,
    )


@router.put("/profile", response_model=ProfileOut, summary="更新用户资料")
def update_profile(
    body: ProfileIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.scalar(select(UserProfile).where(UserProfile.user_id == user.id))
    if profile is None:
        profile = UserProfile(user_id=user.id)
        db.add(profile)
        db.flush()

    for field in ("gender", "birthday", "height_cm", "activity_level"):
        value = getattr(body, field)
        if value is not None:
            setattr(profile, field, value)
    if body.nickname is not None:
        user.nickname = body.nickname
    if body.avatar_url is not None:
        user.avatar_url = body.avatar_url

    db.commit()
    db.refresh(profile)
    return ProfileOut(
        id=user.id,
        openid=user.openid,
        nickname=user.nickname,
        avatar_url=user.avatar_url,
        gender=profile.gender,
        birthday=profile.birthday,
        height_cm=profile.height_cm,
        activity_level=profile.activity_level,
    )


@router.get("/goal", response_model=GoalOut, summary="读取减重目标")
def get_goal(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    goal = db.scalar(select(Goal).where(Goal.user_id == user.id))
    if goal is None:
        return GoalOut(
            start_weight=None,
            target_weight=None,
            target_date=None,
            daily_deficit=500,
            status=1,
        )
    return GoalOut.model_validate(goal)


@router.put("/goal", response_model=GoalOut, summary="设置减重目标")
def set_goal(
    body: GoalIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    goal = db.scalar(select(Goal).where(Goal.user_id == user.id))
    if goal is None:
        goal = Goal(user_id=user.id)
        db.add(goal)

    for field in ("start_weight", "target_weight", "target_date", "daily_deficit"):
        value = getattr(body, field)
        if value is not None:
            setattr(goal, field, value)
    db.commit()
    db.refresh(goal)
    return GoalOut.model_validate(goal)
