from fastapi import APIRouter, File, HTTPException, UploadFile, status, Depends
from fastapi.responses import FileResponse

from dto.response.success_response import SuccessResponse
from service.file_service import FileService
import pathlib

file_router = APIRouter()

@file_router.post("/upload")
async def upload_file(type: str = "public", file: UploadFile = File(...), file_service: FileService = Depends(FileService)):
    path = await file_service.save_file(type, file)
    return SuccessResponse(result= "/".join(path.parts))

@file_router.get("/download")
async def download(str_path: str):
    path = pathlib.Path(str_path)
    if path.is_file():
        return FileResponse(path= path, filename=path.name)
    return  HTTPException(status_code=404)
    