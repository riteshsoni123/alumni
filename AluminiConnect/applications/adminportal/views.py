from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum
from django.shortcuts import render, redirect
from django.urls import reverse_lazy

from datetime import date

from applications.alumniprofile.models import Profile
from .models import EmailTemplate, BulkEmailHistory, SingleEmailHistory
from .mail_helper import send_bulk_mail, send_birthday_wish, send_verification_email

ALLOWED_RECIPIENTS_PER_DAY = 500


def is_superuser(user):
    return user.is_superuser


@login_required
@user_passes_test(
    is_superuser, redirect_field_name=None,
    login_url=reverse_lazy('home')
)
def index(request):
    if request.POST:
        print("sending birthday wishes")
        profile = Profile.objects.get(roll_no='2017247')
        send_birthday_wish(profile)

    return render(request, 'adminportal/index.html')


@login_required
@user_passes_test(
    is_superuser, redirect_field_name=None,
    login_url=reverse_lazy('home')
)
def registrations_index(request):
    if request.method == 'POST':
        try:
            profile = Profile.objects.get(roll_no=request.POST.get('id'))
            if profile.verify is not None:
                raise RuntimeError("Invalid Verification request for {}".format(profile.roll_no))

            if 'approve' in request.POST:
                send_verification_email(request, profile)
                profile.verify = True
                messages.add_message(request, messages.SUCCESS,
                                     "Registration Success, Mail sent to {}".format(profile.name))

            elif 'decline' in request.POST:
                profile.verify = False
                messages.add_message(request, messages.SUCCESS, "Registration Declined for {}".format(profile.name))

            profile.save()
        except Exception:
            print(Exception)
            messages.add_message(request, messages.ERROR, "Something went wrong, contact the admins.")

        return redirect('adminportal:registrations')

    unregistered = Profile.objects.all().filter(verify=None).filter(mail_sent=False)

    context = {
        'pending': unregistered
    }
    return render(request, 'adminportal/registrations.html', context)


@login_required
@user_passes_test(
    is_superuser, redirect_field_name=None,
    login_url=reverse_lazy('home')
)
def mailservice_index(request):
    programmes = Profile.objects.values_list('programme', flat=True).distinct()
    batches = Profile.objects.select_related('batch').values_list('batch__batch', flat=True).distinct()
    branches = Profile.objects.values_list('branch', flat=True).distinct()

    if request.method == 'POST':
        template_id = request.POST['template_id']
        programme = request.POST['programme']
        batch = request.POST['batch']
        branch = request.POST['branch']

        recipients = Profile.objects.all()
        if programme:
            recipients = recipients.filter(programme=programme)
            programmes = programme
        if batch:
            recipients = recipients.filter(batch__batch=batch)
            batches = batch
        if branch:
            recipients = recipients.filter(branch=branch)
            branches = branch

        total_recipients = recipients.count()
        if total_recipients == 0:
            messages.error(request, f"Cannot send email to 0 recipients.")
            return redirect('adminportal:mailservice')

        emails_sent_today = BulkEmailHistory.objects.filter(
            timestamp__date=date.today()
        ).aggregate(Sum('total_delivered'))['total_delivered__sum']

        if emails_sent_today is None:
            emails_sent_today = 0

        total_recipients_allowed = ALLOWED_RECIPIENTS_PER_DAY - emails_sent_today
        if total_recipients > total_recipients_allowed:
            messages.error(request,
                           f"You can only send {total_recipients_allowed} more emails today. Limit: 500 per day.")
            return redirect('adminportal:mailservice')

        try:
            total_messages_delivered = send_bulk_mail(batches, branches, programmes, recipients, template_id)
        except Exception as error:
            print(error)
            messages.error(request, "Something went wrong while sending the emails.")
            return redirect('adminportal:mailservice')

        messages.success(request, f"Email sent successfully to {total_messages_delivered} recipients.")
        return redirect('adminportal:mailservice')

    email_templates = EmailTemplate.objects.all()
    bulk_email_history = BulkEmailHistory.objects.all().order_by('-timestamp')
    single_email_history = SingleEmailHistory.objects.all().order_by('-timestamp')

    context = {
        'email_templates': email_templates,
        'bulk_email_history': bulk_email_history,
        'single_email_history': single_email_history,
        'programmes': programmes,
        'batches': batches,
        'branches': branches,
    }

    return render(request, 'adminportal/mailservice.html', context)
