from web.fun_test.django_interactive import *

from web.fun_test.models import SchedulerDirective
from scheduler.scheduler_global import SchedulerDirectiveTypes

from scheduler.scheduler_helper import pause, unpause

pause()
#unpause()
from web.fun_test.web_interface import *
#set_annoucement("Abc")
#clear_announcements()