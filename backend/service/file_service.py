
import aiofiles
from fastapi import UploadFile
from pathlib import Path
from datetime import datetime
import uuid


class FileService():
    def __init__(self):
        self.root_folder = "bucket"
    
    def get_path(self, type):
        if type == "public":
            type = "public"
        else:
            type = "private"
        now = datetime.now()
        year = now.year
        month = now.month
        day = now.day
        hour = now.hour
        path = Path(f'{type}/{year}/{month}/{day}/{hour}')
        full_path = Path(self.root_folder) / path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print("")
        return full_path
    
    async def save_file(self, type: str, file: UploadFile):
        full_path = self.get_path(type=type)
        name = file.filename
        content = await file.read()
        new_name = str(uuid.uuid4()) + "_" + name
        full_path_with_name = full_path / Path(new_name)
        async with aiofiles.open(full_path_with_name, "wb+") as f:
            await f.write(content)
        return full_path_with_name
