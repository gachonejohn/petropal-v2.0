import os
import mimetypes
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.exceptions import ValidationError
from django.conf import settings
import subprocess
import tempfile

class FileProcessor:
    """Handle file validation, compression, and processing"""
    
    @staticmethod
    def validate_file_size(file, file_type):
        size_limits = {
            'image': settings.MAX_IMAGE_SIZE,
            'video': settings.MAX_VIDEO_SIZE,
            'audio': settings.MAX_AUDIO_SIZE,
            'file': settings.MAX_DOCUMENT_SIZE,
            'document': settings.MAX_DOCUMENT_SIZE,
        }
        
        max_size = size_limits.get(file_type, settings.MAX_FILE_SIZE)
        
        if file.size > max_size:
            max_size_mb = max_size / (1024 * 1024)
            raise ValidationError(
                f'{file_type.capitalize()} file size must be less than {max_size_mb}MB'
            )
        
        return True
    
    @staticmethod
    def get_file_type(filename):
        ext = os.path.splitext(filename)[1].lower()
        
        if ext in settings.ALLOWED_IMAGE_EXTENSIONS:
            return 'image'
        elif ext in settings.ALLOWED_VIDEO_EXTENSIONS:
            return 'video'
        elif ext in settings.ALLOWED_DOCUMENT_EXTENSIONS:
            return 'file'
        elif ext in settings.ALLOWED_AUDIO_EXTENSIONS:
            return 'audio'
        else:
            return 'document'
    
    @staticmethod
    def compress_image(image_file):
        if not settings.COMPRESS_IMAGES:
            return image_file, False
        
        try:
            img = Image.open(image_file)
            
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            
            max_dimension = 1920
            if max(img.size) > max_dimension:
                img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
            
            output = BytesIO()
            img.save(output, format='JPEG', quality=settings.IMAGE_QUALITY, optimize=True)
            output.seek(0)
            
            compressed_file = InMemoryUploadedFile(
                output,
                'ImageField',
                f"{os.path.splitext(image_file.name)[0]}.jpg",
                'image/jpeg',
                output.getbuffer().nbytes,
                None
            )
            
            return compressed_file, True
            
        except Exception as e:
            print(f"Image compression failed: {e}")
            return image_file, False
    
    @staticmethod
    def compress_video(video_file):
        if not settings.COMPRESS_VIDEOS:
            return video_file, False
        
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(video_file.name)[1]) as temp_input:
                for chunk in video_file.chunks():
                    temp_input.write(chunk)
                temp_input_path = temp_input.name
            
            temp_output_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
            
            command = [
                'ffmpeg',
                '-i', temp_input_path,
                '-c:v', 'libx264',
                '-crf', str(settings.VIDEO_CRF),
                '-preset', 'medium',
                '-c:a', 'aac',
                '-b:a', '128k',
                '-movflags', '+faststart',
                '-y',
                temp_output_path
            ]
            
            subprocess.run(command, check=True, capture_output=True)
            
            with open(temp_output_path, 'rb') as f:
                compressed_data = f.read()
            
            os.unlink(temp_input_path)
            os.unlink(temp_output_path)
            
            compressed_file = InMemoryUploadedFile(
                BytesIO(compressed_data),
                'FileField',
                f"{os.path.splitext(video_file.name)[0]}.mp4",
                'video/mp4',
                len(compressed_data),
                None
            )
            
            return compressed_file, True
            
        except Exception as e:
            print(f"Video compression failed: {e}")
            if 'temp_input_path' in locals():
                try:
                    os.unlink(temp_input_path)
                except:
                    pass
            if 'temp_output_path' in locals():
                try:
                    os.unlink(temp_output_path)
                except:
                    pass
            return video_file, False
    
    # @staticmethod
    # def generate_video_thumbnail(video_file):
    #     try:
    #         with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
    #             for chunk in video_file.chunks():
    #                 temp_video.write(chunk)
    #             temp_video_path = temp_video.name
            
    #         thumbnail_path = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg').name
            
    #         command = [
    #             'ffmpeg',
    #             '-i', temp_video_path,
    #             '-ss', '00:00:01',
    #             '-vframes', '1',
    #             '-vf', 'scale=320:-1',
    #             '-y',
    #             thumbnail_path
    #         ]
            
    #         subprocess.run(command, check=True, capture_output=True)
            
    #         with open(thumbnail_path, 'rb') as f:
    #             thumbnail_data = f.read()
            
    #         os.unlink(temp_video_path)
    #         os.unlink(thumbnail_path)
            
    #         thumbnail_file = InMemoryUploadedFile(
    #             BytesIO(thumbnail_data),
    #             'ImageField',
    #             f"thumb_{os.path.splitext(video_file.name)[0]}.jpg",
    #             'image/jpeg',
    #             len(thumbnail_data),
    #             None
    #         )
            
    #         return thumbnail_file
            
    #     except Exception as e:
    #         print(f"Thumbnail generation failed: {e}")
    #         return None
    
    # @staticmethod
    # def get_video_duration(video_path):
    #     try:
    #         command = [
    #             'ffprobe',
    #             '-v', 'error',
    #             '-show_entries', 'format=duration',
    #             '-of', 'default=noprint_wrappers=1:nokey=1',
    #             video_path
    #         ]
            
    #         result = subprocess.run(command, capture_output=True, text=True, check=True)
    #         return float(result.stdout.strip())
            
    #     except Exception as e:
    #         print(f"Failed to get video duration: {e}")
    #         return None