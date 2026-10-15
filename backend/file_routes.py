import uuid
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from auth import decode_access_token
from database import get_db
from encryption import encrypt_file, decrypt_file
from models import FileRecord, User
from security_logger import log_security_event


router = APIRouter(
    prefix="/files",
    tags=["Secure File Sharing"],
)

bearer_scheme = HTTPBearer(auto_error=True)

STORAGE_DIR = Path(__file__).resolve().parent / "storage"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 10 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    ".txt",
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".csv",
}


def validate_file_content(filename: str, data: bytes) -> bool:
    extension = Path(filename).suffix.lower()

    if not data:
        return False

    if extension == ".pdf":
        return data.startswith(b"%PDF-")

    if extension == ".png":
        return data.startswith(b"\x89PNG\r\n\x1a\n")

    if extension in {".jpg", ".jpeg"}:
        return data.startswith(b"\xff\xd8\xff")

    if extension in {".txt", ".csv"}:
        try:
            data.decode("utf-8")
            return True
        except UnicodeDecodeError:
            return False

    return False


def get_authenticated_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_access_token(credentials.credentials)
        subject = payload.get("sub")

        if not isinstance(subject, str):
            raise ValueError("Invalid token subject")

        user_id = int(subject)

    except Exception:
        log_security_event(
            "FILE_AUTHENTICATION_FAILED",
            detail="Invalid or expired token on file endpoint",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.get(User, user_id)

    if user is None or not user.is_active:
        log_security_event(
            "FILE_AUTHENTICATION_FAILED",
            user_id=user_id,
            detail="User missing or inactive on file endpoint",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db),
):
    original_name = Path(file.filename or "uploaded_file").name
    extension = Path(original_name).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        log_security_event(
            "FILE_UPLOAD_REJECTED",
            user_id=current_user.id,
            detail="Disallowed file extension",
        )
        await file.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File extension not allowed",
        )

    file_id = uuid.uuid4().hex
    storage_filename = f"{file_id}.enc"
    destination = STORAGE_DIR / storage_filename

    total_size = 0
    chunks = []

    try:
        while True:
            chunk = await file.read(1024 * 1024)

            if not chunk:
                break

            total_size += len(chunk)

            if total_size > MAX_FILE_SIZE:
                log_security_event(
                    "FILE_UPLOAD_REJECTED",
                    user_id=current_user.id,
                    detail="File exceeded 10 MB limit",
                )
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="File exceeds the 10 MB limit",
                )

            chunks.append(chunk)

        plaintext = b"".join(chunks)

        if not validate_file_content(original_name, plaintext):
            log_security_event(
                "FILE_UPLOAD_REJECTED",
                user_id=current_user.id,
                detail="File content validation failed",
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File content does not match the allowed file format",
            )

        encrypted_data = encrypt_file(plaintext)

        with destination.open("wb") as output:
            output.write(encrypted_data)

        record = FileRecord(
            file_id=file_id,
            original_filename=original_name,
            storage_filename=storage_filename,
            size_bytes=total_size,
            owner_id=current_user.id,
            encrypted=True,
        )

        db.add(record)
        db.commit()

        log_security_event(
            "FILE_UPLOAD_SUCCESS",
            user_id=current_user.id,
            detail=f"file_id={file_id}; size_bytes={total_size}",
        )

        return {
            "message": "File uploaded and encrypted successfully",
            "file_id": file_id,
            "filename": original_name,
            "size_bytes": total_size,
            "uploaded_by": current_user.email,
            "encrypted": True,
            "encryption_algorithm": "AES-256-GCM",
        }

    except Exception:
        db.rollback()
        destination.unlink(missing_ok=True)
        raise

    finally:
        await file.close()


@router.get("/{file_id}/download")
def download_file(
    file_id: str,
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db),
):
    record = (
        db.query(FileRecord)
        .filter(
            FileRecord.file_id == file_id,
            FileRecord.owner_id == current_user.id,
        )
        .first()
    )

    if record is None:
        log_security_event(
            "FILE_ACCESS_DENIED",
            user_id=current_user.id,
            detail=f"Requested file_id={file_id}; missing or not owned",
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    storage_filename = Path(record.storage_filename).name
    file_path = STORAGE_DIR / storage_filename

    if not file_path.is_file():
        log_security_event(
            "FILE_STORAGE_MISSING",
            user_id=current_user.id,
            detail=f"file_id={file_id}",
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stored file not found",
        )

    try:
        encrypted_data = file_path.read_bytes()
        plaintext = decrypt_file(encrypted_data)

    except Exception:
        log_security_event(
            "FILE_DECRYPTION_FAILED",
            user_id=current_user.id,
            detail=f"file_id={file_id}",
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File decryption failed",
        )

    safe_filename = (
        Path(record.original_filename).name
        .replace('"', "_")
        .replace("\r", "_")
        .replace("\n", "_")
    )

    log_security_event(
        "FILE_DOWNLOAD_SUCCESS",
        user_id=current_user.id,
        detail=f"file_id={file_id}",
    )

    return Response(
        content=plaintext,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_filename}"',
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "no-store",
        },
    )
