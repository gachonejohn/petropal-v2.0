from django.conf import settings
from storages.backends.sftpstorage import SFTPStorage


class CPanelSFTPStorage(SFTPStorage):
    
    def __init__(self, **kwargs):
        kwargs['host'] = settings.SFTP_STORAGE_HOST
        kwargs['root_path'] = settings.SFTP_STORAGE_ROOT
        kwargs['params'] = settings.SFTP_STORAGE_PARAMS
        kwargs['interactive'] = settings.SFTP_STORAGE_INTERACTIVE
        kwargs['file_mode'] = settings.SFTP_STORAGE_FILE_MODE
        kwargs['dir_mode'] = settings.SFTP_STORAGE_DIR_MODE
        super().__init__(**kwargs)
    
    def url(self, name):
        if name:
            clean_name = name.lstrip('/')
            return f"{settings.MEDIA_URL.rstrip('/')}/{clean_name}"
        return settings.MEDIA_URL