from celery.schedules import crontab
from celery.decorators import periodic_task
from celery.utils.log import get_task_logger
from datetime import date
from applications.alumniprofile.models import Profile
from applications.adminportal.mail_helper import send_birthday_wish
import datetime

logger = get_task_logger(__name__)


@periodic_task(
    run_every=(crontab()),
    name="send_birthday_wish_celery",
    ignore_result=True
)
def send_birthday_wish_celery():
    logger.info("hiiiiiii")
    today = date.today()
    # birthday_users = Profile.objects.filter(date_of_birth__day=today.day, date_of_birth__month=today.month)
    # if birthday_users:
    #     logger.info("{} People have birthdays today".format(len(birthday_users)))
    #     for user in birthday_users:
    #         send_birthday_wish(user.name, user.email)
    #         logger.info("Birthday Mail Sent to {} at {}".format(user.name, user.email))
    #     logger.info("Birthday Mails Sent to {} People Today!".format(len(birthday_users)))
    # else:
    #     logger.info("No Birthdays Today!")
