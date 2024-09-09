from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse
from .models import SupportRequest, ChatArchive
from transactions.models import Transaction
from django.utils import timezone

def is_support_agent(user):
    return user.groups.filter(name='Support').exists()

@user_passes_test(is_support_agent)
def support_dashboard(request):
    support_requests = SupportRequest.objects.filter(status='waiting')
    return render(request, 'support/support_dashboard.html', {'support_requests': support_requests})

@user_passes_test(is_support_agent)
def join_chat(request, support_id):
    support_request = get_object_or_404(SupportRequest, id=support_id)
    support_request.support_agent = request.user
    support_request.status = 'in_room'
    support_request.save()
    return JsonResponse({'status': 'joined', 'chat_url': f"/transactions/{support_request.transaction.id}/"})

@user_passes_test(is_support_agent)
def leave_chat(request, support_id):
    support_request = get_object_or_404(SupportRequest, id=support_id)
    support_request.status = 'closed'
    support_request.closed_at = timezone.now()
    support_request.save()
    return JsonResponse({'status': 'left'})

@user_passes_test(is_support_agent)
def archive_chat(request, support_id):
    support_request = get_object_or_404(SupportRequest, id=support_id)
    chat = support_request.transaction.messages.all()  # Assuming you have messages stored in the transaction
    chat_data = '\n'.join([f"{msg.sender}: {msg.text}" for msg in chat])
    ChatArchive.objects.create(support_request=support_request, chat_data=chat_data)
    return JsonResponse({'status': 'archived'})
