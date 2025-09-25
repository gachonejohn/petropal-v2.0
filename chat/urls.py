from django.urls import path
from chat import views

urlpatterns = [
    # Conversations
    path('conversations/', views.ConversationListCreateView.as_view(), name='conversation-list-create'),
    path('conversations/<uuid:conversation_id>/', views.ConversationDetailView.as_view(), name='conversation-detail'),
    path('conversations/with-user/<str:user_id>/', views.get_or_create_conversation, name='get-or-create-conversation'),
    
    # Conversation deletion and restoration
    path('conversations/<uuid:conversation_id>/delete/', views.delete_conversation, name='delete-conversation'),
    path('conversations/<uuid:conversation_id>/restore/', views.restore_conversation, name='restore-conversation'),
    
    # Messages
    path('conversations/<uuid:conversation_id>/messages/', views.MessageListCreateView.as_view(), name='message-list-create'),
    path('conversations/<uuid:conversation_id>/mark-read/', views.mark_messages_read, name='mark-messages-read'),
    path('conversations/<uuid:conversation_id>/typing/', views.set_typing_status, name='set-typing-status'),
    
    # Message editing, deletion and restoration
    path('messages/<uuid:message_id>/', views.MessageDetailView.as_view(), name='message-detail'),
    path('messages/<uuid:message_id>/delete/', views.delete_message, name='delete-message'),
    path('messages/<uuid:message_id>/restore/', views.restore_message, name='restore-message'),

    #group management
    path('conversations/<uuid:conversation_id>/group/delete/', views.delete_group, name='delete-group'),
    path('conversations/<uuid:conversation_id>/participants/', views.group_participants, name='group-participants'),
    path('conversations/<uuid:conversation_id>/participants/add/', views.add_participants, name='add-participants'),
    path('conversations/<uuid:conversation_id>/participants/remove/', views.remove_participants, name='remove-participants'),
    path('conversations/<uuid:conversation_id>/update-name/', views.update_group_name, name='update-group-name'),
    
    # Reactions
    path('messages/<uuid:message_id>/react/', views.add_reaction, name='add-reaction'),
    
    # User status
    path('status/', views.update_user_status, name='update-user-status'),
]