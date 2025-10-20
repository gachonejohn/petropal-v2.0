from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from cryptography.fernet import Fernet
from django.conf import settings
import json
import uuid
from django.core.validators import FileExtensionValidator

# Account = get_user_model()

class Conversation(models.Model):
    conversation_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations')
    name = models.CharField(max_length=255, blank=True, null=True)  # Optional for group chats
    is_group = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_conversations')
    
    encryption_key = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-updated_at']
        db_table = 'conversations'

    def save(self, *args, **kwargs):
        if not self.encryption_key:
            self.encryption_key = Fernet.generate_key().decode()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.is_group and self.name:
            return self.name
        participants_names = ", ".join([self.get_display_name(user) for user in self.participants.all()[:2]])
        return f"Conversation: {participants_names}"

    def get_display_name(self, user):
        if hasattr(user, 'profile') and user.profile.company_name:
            return user.profile.company_name
        if user.full_name:
            return user.full_name
        return user.email

    @property
    def last_message(self):
        return self.messages.first()

    def encrypt_message(self, message):
        if not message:
            return message
            
        if not self.encryption_key:
            self.encryption_key = Fernet.generate_key().decode()
            self.save(update_fields=['encryption_key'])
        
        try:
            f = Fernet(self.encryption_key.encode())
            encrypted = f.encrypt(message.encode()).decode()
            return encrypted
        except Exception as e:
            return message  

    def decrypt_message(self, encrypted_message):
        if not self.encryption_key or not encrypted_message:
            return encrypted_message
        
        try:
            f = Fernet(self.encryption_key.encode())
            decrypted = f.decrypt(encrypted_message.encode()).decode()
            return decrypted
        except Exception as e:
            return encrypted_message
            

class Message(models.Model):
    message_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages'
    )
    content = models.TextField(blank=True, null=True)  
    timestamp = models.DateTimeField(default=timezone.now)
    
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('file', 'File'),
        ('video', 'Video'),
        ('system', 'System'),  # For typing indicators, user joined, etc.
    ]
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    attachment = models.FileField(upload_to='message_attachments/', blank=True, null=True,
    validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp', 'mp4', 'mov', 'avi', 'mkv', 'webm', 'pdf', 'doc', 'docx', 'txt', 'xlsx', 'csv'])])
    
    file_name = models.CharField(max_length=255, blank=True)
    file_size = models.BigIntegerField(default=0)  
    file_mime_type = models.CharField(max_length=100, blank=True)
    is_compressed = models.BooleanField(default=False)
    original_file_size = models.BigIntegerField(default=0)

    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    reply_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')

    class Meta:
        ordering = ['-timestamp']
        db_table = 'messages'

    def __str__(self):
        display_name = self.conversation.get_display_name(self.sender)
        return f"{display_name}: {self.get_decrypted_content()[:50]}"

    def get_decrypted_content(self):
        return self.conversation.decrypt_message(self.content)

    def save(self, *args, **kwargs):
        if self.content and not kwargs.pop('skip_encryption', False):
            original_content = self.content
            self.content = self.conversation.encrypt_message(self.content)
        
        super().save(*args, **kwargs)


class MessageReadStatus(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='read_statuses')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['message', 'user']
        db_table = 'message_read_statuses'

class MessageReaction(models.Model):
    REACTION_CHOICES = [
        ('like', '👍'),
        ('love', '❤️'),
        ('laugh', '😂'),
        ('wow', '😮'),
        ('sad', '😢'),
        ('angry', '😠'),
    ]
    
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reaction = models.CharField(max_length=10, choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['message', 'user', 'reaction']
        db_table = 'message_reactions'

# User status in conversations (online, away, busy, etc.)
class UserStatus(models.Model):
    STATUS_CHOICES = [
        ('online', 'Online'),
        ('away', 'Away'),
        ('busy', 'Busy'),
        ('offline', 'Offline'),
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='status')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='offline')
    last_seen = models.DateTimeField(auto_now=True)
    is_typing_in = models.ForeignKey(Conversation, on_delete=models.SET_NULL, null=True, blank=True)
    typing_started_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'user_statuses'

    def __str__(self):
        display_name = self.user.full_name or self.user.email
        return f"{display_name} - {self.status}"

class MessageDeletion(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='user_deletions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    deleted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['message', 'user']
        db_table = 'message_deletions'

class ConversationDeletion(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='user_deletions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    deleted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['conversation', 'user']
        db_table = 'conversation_deletions'