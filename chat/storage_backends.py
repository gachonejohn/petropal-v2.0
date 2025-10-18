from django.conf import settings
from storages.backends.sftpstorage import SFTPStorage


class CPanelSFTPStorage(SFTPStorage):
    """
    Custom SFTP Storage for cPanel hosting.
    Uploads media files to remote server via SFTP.
    """
    
    def __init__(self, **kwargs):
        kwargs['host'] = settings.SFTP_STORAGE_HOST
        kwargs['root_path'] = settings.SFTP_STORAGE_ROOT
        kwargs['params'] = settings.SFTP_STORAGE_PARAMS
        kwargs['interactive'] = settings.SFTP_STORAGE_INTERACTIVE
        kwargs['file_mode'] = settings.SFTP_STORAGE_FILE_MODE
        kwargs['dir_mode'] = settings.SFTP_STORAGE_DIR_MODE
        super().__init__(**kwargs)
    
    def _save(self, name, content):
        name = name.replace('\\', '/')
        return super()._save(name, content)
    
    def url(self, name):
        if name:
            clean_name = name.lstrip('/').replace('\\', '/')
            return f"{settings.MEDIA_URL.rstrip('/')}/{clean_name}"
        return settings.MEDIA_URL