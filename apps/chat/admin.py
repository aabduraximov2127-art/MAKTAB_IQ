from django.contrib import admin

from .models import ChatMember, ChatRoom, Message, ModerationIncident


class ChatMemberInline(admin.TabularInline):
    model = ChatMember
    extra = 0


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ("name", "room_type", "class_room")
    inlines = [ChatMemberInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("chat_room", "sender", "created_at", "is_read")


@admin.register(ModerationIncident)
class ModerationIncidentAdmin(admin.ModelAdmin):
    list_display = ("created_at", "sender", "chat_room", "matched_words")
    readonly_fields = ("message", "chat_room", "sender", "matched_words", "notified")
